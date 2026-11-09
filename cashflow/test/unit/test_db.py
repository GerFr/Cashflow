from __future__ import annotations

import sqlite3
import uuid
from contextlib import closing

import pytest

from cashflow.db import SchemaError, connect, uuid7


def test_uuid7_is_version_7_and_time_ordered():
    ids = [uuid7() for _ in range(50)]
    assert all(uuid.UUID(i).version == 7 for i in ids)
    assert [i[:13] for i in ids] == sorted(i[:13] for i in ids)  # millisecond prefix never decreases


def test_connect_creates_the_schema(tmp_path):
    connect(tmp_path / "sub" / "cashflow.db").kw["bind"].dispose()
    with closing(sqlite3.connect(tmp_path / "sub" / "cashflow.db")) as conn:
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master")}
    assert {"accounts", "transactions", "op_log", "balance_daily", "balance_observations"} <= tables


def test_connect_refuses_another_schema_version(tmp_path):
    path = tmp_path / "cashflow.db"
    connect(path).kw["bind"].dispose()
    with closing(sqlite3.connect(path)) as conn:
        conn.execute("PRAGMA user_version = 99")
    with pytest.raises(SchemaError, match="schema version 99"):
        connect(path)
