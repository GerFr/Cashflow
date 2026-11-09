from __future__ import annotations

import sqlite3
from contextlib import closing

from support.api import account, fixture_bytes, import_file, preview

DKB = "de.dkb.csv-2023"
DKB_IBAN = "DE02120300000000202051"


def op_counts(data_dir) -> dict[str, int]:
    with closing(sqlite3.connect(data_dir / "cashflow.db")) as conn:
        return dict(conn.execute("SELECT op, count(*) FROM op_log GROUP BY op").fetchall())


def test_preview_writes_nothing(client, data_dir):
    result = preview(client, fixture_bytes(DKB))
    assert result["counts"] == {"new": 5, "duplicate": 0, "replaces_pending": 0, "removes_pending": 0}
    assert result["new_accounts"] == [DKB_IBAN]
    assert result["already_imported"] is False
    assert {tx["state"] for tx in result["transactions"]} == {"new"}
    assert client.get("/api/accounts").json() == []
    assert op_counts(data_dir) == {}


def test_import_creates_account_transactions_and_log(client, data_dir):
    run = import_file(client, fixture_bytes(DKB))
    assert (run["new"], run["duplicate"]) == (5, 0)
    dkb = account(client, DKB_IBAN)
    assert dkb["kind"] == "CheckingAccount"
    assert dkb["transactions"] == 5
    assert dkb["balance"] == {"amount": "2345.67", "date": "2026-10-08"}
    assert op_counts(data_dir) == {
        "account.create": 1,
        "source_file.create": 1,
        "transaction.create": 5,
        "balance_observation.save": 1,
        "import_run.create": 1,
    }
    assert [r["id"] for r in client.get("/api/imports").json()] == [run["id"]]


def test_reimport_adds_nothing(client):
    import_file(client, fixture_bytes(DKB))
    again = preview(client, fixture_bytes(DKB))
    assert again["already_imported"] is True
    assert again["counts"] == {"new": 0, "duplicate": 5, "replaces_pending": 0, "removes_pending": 0}
    run = client.post(f"/api/imports/{again['id']}/commit").json()
    assert run["new"] == 0
    assert account(client, DKB_IBAN)["transactions"] == 5


def test_pending_row_is_replaced_by_its_booked_version(client, data_dir):
    import_file(client, fixture_bytes(DKB))
    booked = fixture_bytes(DKB).replace(b'"Vorgemerkt"', b'"Gebucht"')
    result = preview(client, booked, "later.csv")
    assert result["counts"]["replaces_pending"] == 1
    import_file(client, booked, "later.csv")
    assert op_counts(data_dir)["transaction.update"] == 1
    # now booked, the train ticket counts: 2345.67 - 89.90 at the end of 08.10.
    balances = client.get(f"/api/accounts/{account(client, DKB_IBAN)['id']}/balances").json()
    assert balances[-1] == {"date": "2026-10-08", "balance": "2345.67"}
    assert balances[-2] == {"date": "2026-10-07", "balance": "2435.57"}


def test_outdated_pending_row_is_removed(client, data_dir):
    import_file(client, fixture_bytes(DKB))
    changed = fixture_bytes(DKB).replace(b'"Vorgemerkt"', b'"Gebucht"').replace(b'"-89,90"', b'"-79,90"')
    result = preview(client, changed, "later.csv")
    assert result["counts"]["new"] == 1
    assert result["counts"]["removes_pending"] == 1
    import_file(client, changed, "later.csv")
    assert op_counts(data_dir)["transaction.delete"] == 1
    assert account(client, DKB_IBAN)["transactions"] == 5


def test_preview_can_be_committed_once(client):
    item = preview(client, fixture_bytes(DKB))
    assert client.post(f"/api/imports/{item['id']}/commit").status_code == 200
    assert client.post(f"/api/imports/{item['id']}/commit").status_code == 404
    assert client.post("/api/imports/unknown/commit").status_code == 404


def test_stale_preview_does_not_duplicate(client):
    first, second = preview(client, fixture_bytes(DKB)), preview(client, fixture_bytes(DKB))
    client.post(f"/api/imports/{first['id']}/commit")
    run = client.post(f"/api/imports/{second['id']}/commit").json()
    assert (run["new"], run["duplicate"]) == (0, 5)


def test_trade_republic_and_card_balances(client):
    import_file(client, fixture_bytes("de.traderepublic.pdf-statement"), "statement.pdf")
    import_file(client, fixture_bytes("de.dkb.visa-csv-2023"), "visa.csv")
    tr = account(client, "DE02100100100006820101")
    assert (tr["kind"], tr["balance"], tr["mismatches"]) == (
        "BrokerageCashAccount",
        {"amount": "882.78", "date": "2026-11-08"},
        [],
    )
    card = account(client, "4111••••••••1111")
    assert card["kind"] == "CreditCardAccount"
    assert card["balance"] == {"amount": "-412.30", "date": "2026-11-09"}


def test_upload_errors_are_reported(client):
    assert client.post("/api/imports", content=b"x").status_code == 400
    response = client.post("/api/imports", content=b"Datum;Betrag\n", headers={"X-Filename": "x.csv"})
    assert response.status_code == 422
