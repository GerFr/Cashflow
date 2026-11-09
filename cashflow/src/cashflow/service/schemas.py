from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field

from cashflow.connectors.registry import Connector
from cashflow.db import ImportRun
from cashflow.money import from_minor
from cashflow.service.accounts import Summary
from cashflow.service.importer import Preview


class Health(BaseModel):
    status: str
    version: str
    connectors: int


class ConnectorInfo(BaseModel):
    id: str
    name: str
    version: str
    status: str
    institution: str

    @classmethod
    def from_connector(cls, connector: Connector) -> ConnectorInfo:
        return cls(
            id=connector.id,
            name=connector.name,
            version=connector.version,
            status=connector.status,
            institution=connector.institution,
        )


class ImportPreviewOut(BaseModel):
    id: str
    file_name: str
    connector: ConnectorInfo
    already_imported: bool = Field(description="The same file (by SHA-256) was imported before.")
    new_accounts: list[str]
    counts: dict[str, int] = Field(description="new, duplicate, replaces_pending, removes_pending")
    balances: list[dict[str, str]]
    transactions: list[dict[str, Any]] = Field(description="Canonical records, each with its import 'state'.")

    @classmethod
    def from_preview(cls, item: Preview) -> ImportPreviewOut:
        return cls(
            id=item.id,
            file_name=item.file_name,
            connector=ConnectorInfo.from_connector(item.connector),
            already_imported=item.already_imported,
            new_accounts=item.plan.new_accounts,
            counts=item.plan.counts,
            balances=item.result.balances,
            transactions=[
                {**record, "state": state}
                for record, state in zip(item.result.transactions, item.plan.states, strict=True)
            ],
        )


class ImportRunOut(BaseModel):
    id: str
    file_name: str
    connector_id: str
    connector_version: str
    committed_at: dt.datetime
    new: int
    duplicate: int
    replaced_pending: int
    removed_pending: int

    @classmethod
    def from_run(cls, run: ImportRun) -> ImportRunOut:
        return cls.model_validate(run, from_attributes=True)


class Money(BaseModel):
    amount: str
    date: dt.date


class AnchorMismatch(BaseModel):
    date: dt.date
    source: str
    observed: str
    computed: str
    difference: str


class AccountOut(BaseModel):
    id: str
    name: str
    institution: str
    kind: str
    iban: str | None
    external_id: str | None
    currency: str
    liquid: bool
    transactions: int
    balance: Money | None = Field(description="Latest known balance; null until the account has an anchor.")
    opening_balance: Money | None
    mismatches: list[AnchorMismatch] = Field(description="Known balances that disagree with the computed one.")

    @classmethod
    def from_summary(cls, s: Summary) -> AccountOut:
        a, cur = s.account, s.account.currency
        return cls(
            id=a.id,
            name=a.name,
            institution=a.institution,
            kind=a.kind,
            iban=a.iban,
            external_id=a.external_id,
            currency=cur,
            liquid=a.liquid,
            transactions=s.transactions,
            balance=Money(amount=from_minor(s.balance, cur), date=s.balance_date) if s.balance is not None else None,
            opening_balance=Money(amount=from_minor(s.opening.balance_minor, cur), date=s.opening.date)
            if s.opening
            else None,
            mismatches=[
                AnchorMismatch(
                    date=c.anchor.date,
                    source=c.anchor.source,
                    observed=from_minor(c.anchor.balance, cur),
                    computed=from_minor(c.computed, cur),
                    difference=from_minor(c.difference, cur),
                )
                for c in s.mismatches
            ],
        )


class OpeningBalanceIn(BaseModel):
    amount: Decimal = Field(description='Decimal string, e.g. "1234.56"; negative for a credit card debt.')
    date: dt.date | None = Field(None, description="End of this day; default: the day before the first transaction.")


class AccountUpdate(BaseModel):
    name: str | None = None
    liquid: bool | None = None
    opening_balance: OpeningBalanceIn | None = Field(None, description="null removes the opening balance.")


class BalancePoint(BaseModel):
    date: dt.date
    balance: str
