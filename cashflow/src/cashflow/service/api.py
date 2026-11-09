from __future__ import annotations

from collections import OrderedDict
from collections.abc import Iterator
from datetime import date
from importlib.metadata import version
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from cashflow import balances
from cashflow.connectors.engine import ConnectorError, ParseResult
from cashflow.connectors.registry import Connector
from cashflow.db import Account, ImportRun
from cashflow.money import from_minor
from cashflow.service import accounts, importer
from cashflow.service.schemas import (
    AccountOut,
    AccountUpdate,
    BalancePoint,
    ConnectorInfo,
    Health,
    ImportPreviewOut,
    ImportRunOut,
)
from cashflow.utils.config import get_settings
from cashflow.utils.http import clean_filename, read_limited_body
from cashflow.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.sessions() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
ConnectorQuery = Annotated[str | None, Query(description="Connector id; detected from the file if omitted.")]
FilenameHeader = Annotated[str | None, Header(alias="X-Filename")]


async def parse_upload(
    request: Request, connector: str | None, filename: str | None
) -> tuple[Connector, ParseResult, str, int]:
    """Read the uploaded bytes, pick the connector and parse; HTTP errors for everything that can go wrong."""
    name = clean_filename(filename)
    content = await read_limited_body(request, get_settings().max_upload_mb * 1024 * 1024)
    registry = request.app.state.connectors
    if connector is not None:
        chosen = registry.get(connector)
        if chosen is None:
            raise HTTPException(status_code=404, detail=f"unknown connector {connector!r}")
    else:
        chosen = registry.detect(content, name)
        if chosen is None:
            raise HTTPException(status_code=422, detail="no connector recognises this file")
    try:
        result = chosen.parse(content)
    except (ConnectorError, UnicodeDecodeError) as exc:
        raise HTTPException(status_code=422, detail=f"{chosen.id}: {exc}") from None
    logger.info("parsed connector=%s bytes=%d rows=%d", chosen.id, len(content), len(result.transactions))
    return chosen, result, name, len(content)


@router.get("/health")
def health(request: Request) -> Health:
    return Health(status="ok", version=version("cashflow"), connectors=len(request.app.state.connectors))


@router.get("/connectors")
def list_connectors(request: Request) -> list[ConnectorInfo]:
    return [ConnectorInfo.from_connector(c) for c in request.app.state.connectors.connectors.values()]


@router.post("/parse")
async def parse_file(request: Request, connector: ConnectorQuery = None, filename: FilenameHeader = None) -> dict:
    """Parse a bank export (CSV or PDF, raw bytes in the body) into canonical transaction records. Nothing is stored."""
    _, result, _, _ = await parse_upload(request, connector, filename)
    return result.to_json()


# --- Imports ---------------------------------------------------------------------------


@router.post("/imports", status_code=status.HTTP_201_CREATED)
async def create_import(
    request: Request, session: SessionDep, connector: ConnectorQuery = None, filename: FilenameHeader = None
) -> ImportPreviewOut:
    """Parse a file and classify its rows against the database. Nothing is written until the commit."""
    chosen, result, name, size = await parse_upload(request, connector, filename)
    item = importer.preview(session, chosen, result, name, size)
    previews: OrderedDict[str, importer.Preview] = request.app.state.previews
    previews[item.id] = item
    while len(previews) > get_settings().max_previews:
        previews.popitem(last=False)
    return ImportPreviewOut.from_preview(item)


@router.post("/imports/{preview_id}/commit")
def commit_import(preview_id: str, request: Request, session: SessionDep) -> ImportRunOut:
    """Write a preview in one database transaction."""
    item = request.app.state.previews.pop(preview_id, None)
    if item is None:
        raise HTTPException(status_code=404, detail="preview not found (already imported or expired); upload again")
    run = importer.commit(session, item)
    logger.info("imported file=%s new=%d duplicate=%d", run.file_name, run.new, run.duplicate)
    return ImportRunOut.from_run(run)


@router.get("/imports")
def list_imports(session: SessionDep) -> list[ImportRunOut]:
    runs = session.scalars(select(ImportRun).order_by(ImportRun.committed_at.desc()))
    return [ImportRunOut.from_run(run) for run in runs]


# --- Accounts --------------------------------------------------------------------------


def get_account(session: Session, account_id: str) -> Account:
    account = session.get(Account, account_id)
    if account is None:
        raise HTTPException(status_code=404, detail="account not found")
    return account


@router.get("/accounts")
def list_accounts(session: SessionDep) -> list[AccountOut]:
    rows = session.scalars(select(Account).order_by(Account.institution, Account.name))
    return [AccountOut.from_summary(accounts.summary(session, account)) for account in rows]


@router.patch("/accounts/{account_id}")
def update_account(account_id: str, change: AccountUpdate, session: SessionDep) -> AccountOut:
    """Rename, include in or exclude from liquid net worth, set or remove (null) the opening balance."""
    with session.begin():
        account = get_account(session, account_id)
        try:
            if change.name is not None:
                accounts.rename(session, account, change.name)
            if change.liquid is not None:
                accounts.set_liquid(session, account, change.liquid)
            if "opening_balance" in change.model_fields_set:
                opening = change.opening_balance
                accounts.set_opening_balance(
                    session, account, opening.amount if opening else None, opening.date if opening else None
                )
                session.flush()
                balances.recompute(session, account.id)
        except accounts.AccountError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from None
    return AccountOut.from_summary(accounts.summary(session, account))


@router.get("/accounts/{account_id}/balances")
def account_balances(
    account_id: str,
    session: SessionDep,
    start: Annotated[date | None, Query(alias="from")] = None,
    end: Annotated[date | None, Query(alias="to")] = None,
) -> list[BalancePoint]:
    """End-of-day balances of one account."""
    account = get_account(session, account_id)
    return [
        BalancePoint(date=row.day, balance=from_minor(row.balance_minor, account.currency))
        for row in balances.series(session, account.id, start, end)
    ]
