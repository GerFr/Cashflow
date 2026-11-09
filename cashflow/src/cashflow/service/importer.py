"""Import pipeline: parse → classify against the database → preview → commit (DESIGN.md#import-pipeline).

Duplicates are found per transaction, never per file: each parsed record is classified by its
deterministic id (fingerprint of account, dates, amount, counterparty, purpose and reference ids), so a
new download that overlaps earlier ones only adds the rows that are missing:

* ``new``: not in the database yet;
* ``duplicate``: already imported (re-importing overlapping exports adds nothing);
* ``replaces_pending``: known as pending and now booked; the stored row is updated.

Pending rows of the same account that are no longer in a newer export of the same period are removed
(``removes_pending``): the bank has booked them with other details or dropped them. A commit classifies
again inside its transaction, so a preview that became stale can't write duplicates.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from cashflow import balances
from cashflow.connectors.engine import ParseResult, uuid8
from cashflow.connectors.registry import Connector
from cashflow.db import (
    Account,
    BalanceObservation,
    ImportRun,
    SourceFile,
    SourceRecord,
    Transaction,
    log,
    utcnow,
    uuid7,
)
from cashflow.money import to_minor

STATES = ("new", "duplicate", "replaces_pending")
COLUMNS = (
    "counterparty_name",
    "counterparty_iban",
    "counterparty_bic",
    "remittance_information",
    "booking_text",
    "creditor_id",
    "mandate_reference",
    "end_to_end_id",
    "merchant_category_code",
    "external_id",
)
EXTRA = ("transaction_datetime", "exchange_rate", "fee_amount", "related_external_id", "category_hint")


def account_id(key: str) -> str:
    """UUIDv8 from the IBAN or provider account id, the same on every device."""
    return str(uuid8(f"account:{key}"))


def account_key(record: dict[str, Any]) -> str:
    return record.get("account_iban") or record["account_external_id"]


def file_accounts(result: ParseResult) -> list[str]:
    """Accounts of the transactions plus accounts that only appear with a balance."""
    keys = list(result.accounts)
    keys += [b["account"] for b in result.balances if b["account"] and b["account"] not in keys]
    return keys


@dataclass
class Plan:
    states: list[str]  # one per parsed record, in file order
    stale_pending: list[Transaction]
    new_accounts: list[str]  # keys

    @property
    def counts(self) -> dict[str, int]:
        counts = Counter(self.states)
        return {**{state: counts[state] for state in STATES}, "removes_pending": len(self.stale_pending)}


@dataclass
class Preview:
    connector: Connector
    result: ParseResult
    file_name: str
    size: int
    plan: Plan
    id: str = field(default_factory=uuid7)
    created_at: datetime = field(default_factory=utcnow)


def classify(session: Session, result: ParseResult) -> Plan:
    ids = [record["id"] for record in result.transactions]
    known = {tx.id: tx for tx in session.scalars(select(Transaction).where(Transaction.id.in_(ids)))}
    states = []
    for record in result.transactions:
        old = known.get(record["id"])
        if old is None:
            states.append("new")
        elif old.status == "pending" and record["status"] == "booked":
            states.append("replaces_pending")
        else:
            states.append("duplicate")

    stale: list[Transaction] = []
    for key in result.accounts:
        dates = [date.fromisoformat(r["booking_date"]) for r in result.transactions if account_key(r) == key]
        stale += session.scalars(
            select(Transaction).where(
                Transaction.account_id == account_id(key),
                Transaction.status == "pending",
                Transaction.booking_date.between(min(dates), max(dates)),
                Transaction.id.not_in(ids),
            )
        )
    new_accounts = [key for key in file_accounts(result) if session.get(Account, account_id(key)) is None]
    return Plan(states, stale, new_accounts)


def preview(session: Session, connector: Connector, result: ParseResult, file_name: str, size: int) -> Preview:
    return Preview(connector, result, file_name, size, classify(session, result))


def columns(record: dict[str, Any]) -> dict[str, Any]:
    """Database columns of a canonical record."""
    currency = record["currency"]
    original = record.get("original_amount")
    return {
        "account_id": account_id(account_key(record)),
        "fingerprint": record["fingerprint"],
        "booking_date": date.fromisoformat(record["booking_date"]),
        "value_date": date.fromisoformat(record["value_date"]) if "value_date" in record else None,
        "direction": record["direction"],
        "amount_minor": to_minor(record["amount"], currency),
        "currency": currency,
        "status": record["status"],
        "original_amount_minor": to_minor(original, record.get("original_currency", currency)) if original else None,
        "original_currency": record.get("original_currency") if original else None,
        **{name: record.get(name) for name in COLUMNS},
        "extra": {name: record[name] for name in EXTRA if name in record},
        "row_number": record["row_number"],
    }


def commit(session: Session, item: Preview) -> ImportRun:
    """Write the preview in one transaction: accounts, source file and records, transactions, balances, op log."""
    result, connector = item.result, item.connector
    with session.begin():
        plan = classify(session, result)
        for key in plan.new_accounts:
            create_account(session, connector, result, key)

        source = session.get(SourceFile, result.file_sha256)
        if source is None:
            source = SourceFile(
                id=result.file_sha256,
                file_name=item.file_name,
                size=item.size,
                connector_id=result.connector_id,
                connector_version=result.connector_version,
                first_imported_at=utcnow(),
            )
            session.add(source)
            log(session, "source_file.create", source.id, {"file_name": item.file_name})
        session.flush()  # parents first: no ORM relationships, so the flush order follows the code
        counts = plan.counts
        run = ImportRun(
            id=uuid7(),
            source_file_id=source.id,
            file_name=item.file_name,
            connector_id=result.connector_id,
            connector_version=result.connector_version,
            committed_at=utcnow(),
            new=counts["new"],
            duplicate=counts["duplicate"],
            replaced_pending=counts["replaces_pending"],
            removed_pending=counts["removes_pending"],
        )
        session.add(run)
        session.flush()

        for row_number, raw in result.raw_rows.items():
            session.merge(SourceRecord(source_file_id=source.id, row_number=row_number, raw=raw))
        for record, state in zip(result.transactions, plan.states, strict=True):
            values = {**columns(record), "source_file_id": source.id, "import_run_id": run.id}
            if state == "new":
                session.add(Transaction(id=record["id"], **values))
                log(session, "transaction.create", record["id"], record)
            elif state == "replaces_pending":
                tx = session.get(Transaction, record["id"])
                for name, value in values.items():
                    setattr(tx, name, value)
                log(session, "transaction.update", record["id"], record)
        for tx in plan.stale_pending:
            log(session, "transaction.delete", tx.id, {"reason": "pending row no longer in export"})
            session.delete(tx)
        for observed in result.balances:
            if observed["account"]:
                save_export_balance(session, observed, source.id)

        session.flush()
        for key in file_accounts(result):
            balances.recompute(session, account_id(key))
        log(session, "import_run.create", run.id, {"file": source.id, **counts})
    return run


def create_account(session: Session, connector: Connector, result: ParseResult, key: str) -> None:
    currencies = [r["currency"] for r in result.transactions if account_key(r) == key]
    is_iban = re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", key) is not None
    account = Account(
        id=account_id(key),
        key=key,
        iban=key if is_iban else None,
        external_id=None if is_iban else key,
        name=f"{connector.institution} …{key[-4:]}",
        institution=connector.institution,
        kind=connector.account_kind,
        currency=currencies[0] if currencies else "EUR",
        created_at=utcnow(),
    )
    session.add(account)
    log(session, "account.create", account.id, {"key": key, "kind": account.kind, "name": account.name})


def save_export_balance(session: Session, observed: dict[str, str], source_file_id: str) -> None:
    account = session.get(Account, account_id(observed["account"]))
    when = date.fromisoformat(observed["date"])
    value = to_minor(observed["balance"], account.currency)
    existing = session.scalars(
        select(BalanceObservation).where(
            BalanceObservation.account_id == account.id,
            BalanceObservation.date == when,
            BalanceObservation.source == "export",
        )
    ).first()
    if existing is not None and existing.balance_minor == value:
        return
    if existing is None:
        existing = BalanceObservation(account_id=account.id, date=when, source="export")
        session.add(existing)
    existing.balance_minor, existing.source_file_id = value, source_file_id
    log(session, "balance_observation.save", account.id, {"date": observed["date"], "balance": observed["balance"]})
