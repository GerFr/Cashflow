from __future__ import annotations

import pytest
from support.fixtures import CASES, case_id, read_case

from cashflow.utils.config import Settings


def post_file(client, content: bytes, filename: str | None = "export.csv", **params):
    headers = {"X-Filename": filename} if filename is not None else {}
    return client.post("/api/parse", content=content, headers=headers, params=params)


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["connectors"] == len(client.app.state.connectors)
    assert response.headers["cache-control"] == "no-store"


def test_connectors_lists_every_definition(client):
    response = client.get("/api/connectors")
    assert response.status_code == 200
    ids = {c["id"] for c in response.json()}
    assert ids == set(client.app.state.connectors.definitions)
    assert all(c["institution"] and c["status"] for c in response.json())


@pytest.mark.parametrize(("connector_id", "case"), CASES, ids=case_id)
def test_parse_detects_format_and_matches_golden(client, connector_id, case):
    content, expected = read_case(case)
    response = post_file(client, content)
    assert response.status_code == 200, response.text
    assert response.json() == expected


def test_parse_with_explicit_connector(client):
    connector_id, case = CASES[0]
    content, expected = read_case(case)
    response = post_file(client, content, connector=connector_id)
    assert response.status_code == 200
    assert response.json() == expected


def test_parse_accepts_url_encoded_filename(client):
    content, _ = read_case(CASES[0][1])
    assert post_file(client, content, filename="Ums%C3%A4tze%202026.csv").status_code == 200


@pytest.mark.parametrize(("filename", "detail"), [(None, "required"), ("", "required"), ("a%0Ab.csv", "invalid")])
def test_parse_rejects_bad_filenames(client, filename, detail):
    response = post_file(client, b"x", filename=filename)
    assert response.status_code == 400
    assert detail in response.json()["detail"]


def test_parse_unknown_connector_is_404(client):
    response = post_file(client, b"x", connector="xx.nope")
    assert response.status_code == 404


def test_parse_unrecognised_file_is_422(client):
    response = post_file(client, b"Datum;Betrag\n01.01.2026;1,00\n")
    assert response.status_code == 422
    assert "no connector" in response.json()["detail"]


def test_parse_malformed_row_is_422(client):
    content, _ = read_case(next(case for cid, case in CASES if cid == "de.dkb.csv-2023"))
    broken = content.replace(b'"-3,20"', b'"drei Euro"')
    response = post_file(client, broken)
    assert response.status_code == 422
    assert "not a decimal" in response.json()["detail"]


def test_parse_wrong_encoding_for_forced_connector_is_422(client):
    response = post_file(client, b"\xff\xfe\xfa", connector="de.dkb.csv-2023")
    assert response.status_code == 422


def test_parse_too_large_is_413(client, monkeypatch):
    monkeypatch.setattr(Settings, "max_upload_mb", 0)
    response = post_file(client, b"x")
    assert response.status_code == 413
