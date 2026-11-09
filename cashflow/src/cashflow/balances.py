"""Daily balances from anchors and booked transactions (DESIGN.md#balances).

An anchor is a known end-of-day balance: a closing balance from an export or an opening balance the
user entered. From the earliest anchor the balance is carried backwards and forwards with the daily
sums of booked transactions; every later anchor resets it to the bank's figure and is checked against
the computed value first. A difference usually means a missing import. Pending transactions don't count.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import delete, func, insert, select
from sqlalchemy.orm import Session

from cashflow.db import BalanceDaily, BalanceObservation, Transaction


@dataclass(frozen=True)
class Anchor:
    date: date
    balance: int
    source: str  # export | opening


@dataclass(frozen=True)
class AnchorCheck:
    anchor: Anchor
    computed: int

    @property
    def difference(self) -> int:
        return self.anchor.balance - self.computed


def compute(anchors: list[Anchor], net: dict[date, int]) -> tuple[dict[date, int], list[AnchorCheck]]:
    """Balance per day from the first anchor or transaction to the last one, plus a check per later anchor."""
    if not anchors:
        return {}, []
    ordered = sorted(anchors, key=lambda a: (a.date, a.source != "export"))  # the bank's figure wins a tie
    by_date: dict[date, list[Anchor]] = defaultdict(list)
    for anchor in ordered:
        by_date[anchor.date].append(anchor)
    first = ordered[0]
    start = min(first.date, *net) if net else first.date
    end = max(ordered[-1].date, *net) if net else ordered[-1].date

    balances = {first.date: first.balance}
    checks = [AnchorCheck(other, first.balance) for other in by_date[first.date][1:]]
    day = first.date
    while day > start:  # end of the previous day = this day's balance minus this day's bookings
        balances[day - timedelta(days=1)] = balances[day] - net.get(day, 0)
        day -= timedelta(days=1)
    day, current = first.date, first.balance
    while day < end:
        day += timedelta(days=1)
        current += net.get(day, 0)
        if day in by_date:
            checks.extend(AnchorCheck(anchor, current) for anchor in by_date[day])
            current = by_date[day][0].balance
        balances[day] = current
    return balances, checks


def load(session: Session, account_id: str) -> tuple[list[Anchor], dict[date, int]]:
    anchors = [
        Anchor(o.date, o.balance_minor, o.source)
        for o in session.scalars(select(BalanceObservation).where(BalanceObservation.account_id == account_id))
    ]
    net: dict[date, int] = defaultdict(int)
    booked = select(Transaction).where(Transaction.account_id == account_id, Transaction.status == "booked")
    for tx in session.scalars(booked):
        net[tx.booking_date] += tx.signed_minor
    return anchors, dict(net)


def checks(session: Session, account_id: str) -> list[AnchorCheck]:
    """Anchors that disagree with the computed balance."""
    return [c for c in compute(*load(session, account_id))[1] if c.difference]


def recompute(session: Session, account_id: str) -> None:
    """Rewrite balance_daily for one account (call inside the write transaction)."""
    balances, _ = compute(*load(session, account_id))
    session.execute(delete(BalanceDaily).where(BalanceDaily.account_id == account_id))
    if balances:
        rows = [{"account_id": account_id, "day": day, "balance_minor": value} for day, value in balances.items()]
        session.execute(insert(BalanceDaily), rows)


def latest(session: Session, account_id: str) -> BalanceDaily | None:
    newest = select(func.max(BalanceDaily.day)).where(BalanceDaily.account_id == account_id).scalar_subquery()
    return session.scalars(
        select(BalanceDaily).where(BalanceDaily.account_id == account_id, BalanceDaily.day == newest)
    ).first()


def series(session: Session, account_id: str, start: date | None, end: date | None) -> list[BalanceDaily]:
    query = select(BalanceDaily).where(BalanceDaily.account_id == account_id)
    if start:
        query = query.where(BalanceDaily.day >= start)
    if end:
        query = query.where(BalanceDaily.day <= end)
    return list(session.scalars(query.order_by(BalanceDaily.day)))
