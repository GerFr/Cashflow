from __future__ import annotations

from support.api import account, fixture_bytes, import_file

SPARKASSE = "de.sparkasse.csv-camt-v2"


def sparkasse(client):
    import_file(client, fixture_bytes(SPARKASSE))
    return next(a for a in client.get("/api/accounts").json() if a["institution"].startswith("Sparkasse"))


def test_account_without_balance_in_the_export(client):
    acc = sparkasse(client)
    assert acc["balance"] is None
    assert acc["opening_balance"] is None


def test_opening_balance_defaults_to_the_day_before_the_first_transaction(client):
    acc = sparkasse(client)
    response = client.patch(f"/api/accounts/{acc['id']}", json={"opening_balance": {"amount": "1000.00"}})
    assert response.status_code == 200, response.text
    updated = response.json()
    first = min(p["date"] for p in client.get(f"/api/accounts/{acc['id']}/balances").json())
    assert updated["opening_balance"]["date"] == first
    assert updated["opening_balance"]["amount"] == "1000.00"
    assert updated["balance"] is not None


def test_opening_balance_can_be_removed(client):
    acc = sparkasse(client)
    client.patch(f"/api/accounts/{acc['id']}", json={"opening_balance": {"amount": "10", "date": "2026-01-01"}})
    removed = client.patch(f"/api/accounts/{acc['id']}", json={"opening_balance": None}).json()
    assert removed["opening_balance"] is None
    assert removed["balance"] is None


def test_wrong_opening_balance_shows_a_mismatch(client):
    import_file(client, fixture_bytes("de.dkb.csv-2023"))
    dkb = account(client, "DE02120300000000202051")
    updated = client.patch(
        f"/api/accounts/{dkb['id']}", json={"opening_balance": {"amount": "0", "date": "2026-09-30"}}
    ).json()
    # the export says 2345.67 on 08.10.; from 0 on 30.09. the booked rows (3210 + 45 - 31.50 - 3.20) reach 3220.30
    assert [(m["date"], m["source"], m["difference"]) for m in updated["mismatches"]] == [
        ("2026-10-08", "export", "-874.63")
    ]
    assert updated["balance"]["amount"] == "2345.67"


def test_rename_and_liquid_flag(client):
    acc = sparkasse(client)
    updated = client.patch(f"/api/accounts/{acc['id']}", json={"name": " Giro ", "liquid": False}).json()
    assert (updated["name"], updated["liquid"]) == ("Giro", False)


def test_invalid_changes_are_rejected(client):
    acc = sparkasse(client)
    assert client.patch(f"/api/accounts/{acc['id']}", json={"name": "  "}).status_code == 422
    too_precise = {"opening_balance": {"amount": "1.005"}}
    assert client.patch(f"/api/accounts/{acc['id']}", json=too_precise).status_code == 422
    assert client.patch("/api/accounts/nope", json={"liquid": True}).status_code == 404


def test_balances_can_be_filtered_by_date(client):
    import_file(client, fixture_bytes("de.dkb.csv-2023"))
    dkb = account(client, "DE02120300000000202051")
    points = client.get(f"/api/accounts/{dkb['id']}/balances", params={"from": "2026-10-05", "to": "2026-10-06"}).json()
    assert points == [{"date": "2026-10-05", "balance": "2303.87"}, {"date": "2026-10-06", "balance": "2348.87"}]
