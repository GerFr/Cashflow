"""Account settings and summaries: name, liquid flag and the opening balance (an anchor the user enters)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from cashflow import balances
from cashflow.db import Account, BalanceObservation, Transaction, log
from cashflow.money import to_minor


class AccountError(ValueError):
    """An account change that can't be applied."""


@dataclass(frozen=True)
class Summary:
    account: Account
    transactions: int
    balance: int | None  # latest known balance, minor units
    balance_date: date | None
    opening: BalanceObservation | None
    mismatches: list[balances.AnchorCheck]


def opening_balance(session: Session, account_id: str) -> BalanceObservation | None:
    query = select(BalanceObservation).where(
        BalanceObservation.account_id == account_id, BalanceObservation.source == "opening"
    )
    return session.scalars(query).first()


def summary(session: Session, account: Account) -> Summary:
    count = session.scalar(select(func.count()).where(Transaction.account_id == account.id)) or 0
    latest = balances.latest(session, account.id)
    return Summary(
        account=account,
        transactions=count,
        balance=latest.balance_minor if latest else None,
        balance_date=latest.day if latest else None,
        opening=opening_balance(session, account.id),
        mismatches=balances.checks(session, account.id),
    )


def rename(session: Session, account: Account, name: str) -> None:
    if not name.strip():
        raise AccountError("name must not be empty")
    account.name = name.strip()
    log(session, "account.update", account.id, {"name": account.name})


def set_liquid(session: Session, account: Account, liquid: bool) -> None:
    account.liquid = liquid
    log(session, "account.update", account.id, {"liquid": liquid})


def set_opening_balance(session: Session, account: Account, amount: Decimal | None, when: date | None) -> None:
    """Balance at the end of ``when`` (default: the day before the first transaction); None removes it."""
    if amount is None:
        session.execute(
            delete(BalanceObservation).where(
                BalanceObservation.account_id == account.id, BalanceObservation.source == "opening"
            )
        )
        log(session, "balance_observation.delete", account.id, {"source": "opening"})
        return
    if when is None:
        first = session.scalar(select(func.min(Transaction.booking_date)).where(Transaction.account_id == account.id))
        if first is None:
            raise AccountError("the account has no transactions yet; give the date of the opening balance")
        when = first - timedelta(days=1)
    try:
        value = to_minor(amount, account.currency)
    except ValueError as exc:
        raise AccountError(str(exc)) from None
    existing = opening_balance(session, account.id)
    if existing is None:
        existing = BalanceObservation(account_id=account.id, source="opening")
        session.add(existing)
    existing.date, existing.balance_minor = when, value
    log(
        session,
        "balance_observation.save",
        account.id,
        {"source": "opening", "date": when.isoformat(), "balance": str(amount)},
    )
