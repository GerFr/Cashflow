"""SQLite storage: SQLAlchemy models and the operation log.

Every change to the logged tables happens inside one ``session.begin()`` block that also appends to
``op_log`` (rule 3 in DESIGN.md). ``balance_daily`` is derived data: it is recomputed from the logged
tables and not logged itself. Amounts are INTEGER minor units.
"""

from __future__ import annotations

import os
import time
import uuid
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any, ClassVar

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    TypeDecorator,
    UniqueConstraint,
    create_engine,
    event,
    inspect,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker

SCHEMA_VERSION = 1


class SchemaError(Exception):
    """The database was created by an incompatible version of the service."""


def utcnow() -> datetime:
    return datetime.now(UTC)


def uuid7() -> str:
    """Time-ordered UUIDv7 (RFC 9562) for entities created in Cashflow itself."""
    millis = time.time_ns() // 1_000_000
    rand = int.from_bytes(os.urandom(10), "big")
    value = (millis << 80) | (0x7 << 76) | ((rand >> 62) & 0xFFF) << 64 | (0b10 << 62) | (rand & ((1 << 62) - 1))
    return str(uuid.UUID(int=value))


class UTCDateTime(TypeDecorator):
    """Stored as naive UTC (SQLite has no time zones), always returned time-zone aware."""

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value: datetime | None, dialect) -> datetime | None:
        return value.astimezone(UTC).replace(tzinfo=None) if value else value

    def process_result_value(self, value: datetime | None, dialect) -> datetime | None:
        return value.replace(tzinfo=UTC) if value else value


class Base(DeclarativeBase):
    type_annotation_map: ClassVar[dict] = {dict[str, Any]: JSON, datetime: UTCDateTime}


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUIDv8 from the key
    key: Mapped[str] = mapped_column(unique=True)  # IBAN or provider account id from the export
    iban: Mapped[str | None]
    external_id: Mapped[str | None]
    name: Mapped[str]
    institution: Mapped[str]
    kind: Mapped[str]  # ontology class, e.g. CheckingAccount
    currency: Mapped[str] = mapped_column(String(3))
    liquid: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime]


class SourceFile(Base):
    __tablename__ = "source_files"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)  # SHA-256 of the file
    file_name: Mapped[str]
    size: Mapped[int]
    connector_id: Mapped[str]
    connector_version: Mapped[str]
    first_imported_at: Mapped[datetime]


class SourceRecord(Base):
    __tablename__ = "source_records"

    source_file_id: Mapped[str] = mapped_column(ForeignKey("source_files.id"), primary_key=True)
    row_number: Mapped[int] = mapped_column(primary_key=True)
    raw: Mapped[str] = mapped_column(Text)


class ImportRun(Base):
    __tablename__ = "import_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUIDv7
    source_file_id: Mapped[str] = mapped_column(ForeignKey("source_files.id"))
    file_name: Mapped[str]
    connector_id: Mapped[str]
    connector_version: Mapped[str]
    committed_at: Mapped[datetime]
    new: Mapped[int]
    duplicate: Mapped[int]
    replaced_pending: Mapped[int]
    removed_pending: Mapped[int]


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_account_date", "account_id", "booking_date"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUIDv8 from the fingerprint
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    fingerprint: Mapped[str] = mapped_column(String(64))
    booking_date: Mapped[date]
    value_date: Mapped[date | None]
    direction: Mapped[str] = mapped_column(String(6))  # debit | credit
    amount_minor: Mapped[int]  # >= 0; direction carries the sign
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(7))  # booked | pending
    original_amount_minor: Mapped[int | None]
    original_currency: Mapped[str | None] = mapped_column(String(3))
    counterparty_name: Mapped[str | None]
    counterparty_iban: Mapped[str | None]
    counterparty_bic: Mapped[str | None]
    remittance_information: Mapped[str | None] = mapped_column(Text)
    booking_text: Mapped[str | None]
    creditor_id: Mapped[str | None]
    mandate_reference: Mapped[str | None]
    end_to_end_id: Mapped[str | None]
    merchant_category_code: Mapped[str | None]
    external_id: Mapped[str | None]
    extra: Mapped[dict[str, Any]] = mapped_column(default=dict)  # other canonical fields
    source_file_id: Mapped[str] = mapped_column(ForeignKey("source_files.id"))
    row_number: Mapped[int]
    import_run_id: Mapped[str] = mapped_column(ForeignKey("import_runs.id"))

    @property
    def signed_minor(self) -> int:
        return self.amount_minor if self.direction == "credit" else -self.amount_minor


class BalanceObservation(Base):
    """A known balance at the end of a day: from an export, or an opening balance the user entered."""

    __tablename__ = "balance_observations"
    __table_args__ = (UniqueConstraint("account_id", "date", "source"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"))
    date: Mapped[date]
    balance_minor: Mapped[int]
    source: Mapped[str] = mapped_column(String(7))  # export | opening
    source_file_id: Mapped[str | None] = mapped_column(ForeignKey("source_files.id"))


class BalanceDaily(Base):
    """Derived: balance of each account at the end of each day (see balances.py)."""

    __tablename__ = "balance_daily"

    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id"), primary_key=True)
    day: Mapped[date] = mapped_column(primary_key=True)
    balance_minor: Mapped[int]


class OpLog(Base):
    __tablename__ = "op_log"

    seq: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    at: Mapped[datetime]
    op: Mapped[str]  # e.g. transaction.create
    entity_id: Mapped[str]
    data: Mapped[dict[str, Any]] = mapped_column(default=dict)


def log(session: Session, op: str, entity_id: str, data: dict[str, Any] | None = None) -> None:
    """Append to the operation log; call inside the same session.begin() block as the change."""
    session.add(OpLog(at=utcnow(), op=op, entity_id=entity_id, data=data or {}))


def connect(path: Path) -> sessionmaker[Session]:
    """Open (and create) the database; refuse one with another schema version."""
    path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(f"sqlite:///{path}")

    @event.listens_for(engine, "connect")
    def _pragmas(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA journal_mode = WAL")
        cursor.close()

    try:
        with engine.begin() as conn:
            version = conn.exec_driver_sql("PRAGMA user_version").scalar()
            if inspect(conn).get_table_names() and version != SCHEMA_VERSION:
                raise SchemaError(
                    f"{path} has schema version {version}, this service needs {SCHEMA_VERSION}. "
                    "Until there are migrations: move the file away and import again."
                )
            Base.metadata.create_all(conn)
            conn.exec_driver_sql(f"PRAGMA user_version = {SCHEMA_VERSION}")
    except Exception:
        engine.dispose()
        raise
    return sessionmaker(engine, expire_on_commit=False)
