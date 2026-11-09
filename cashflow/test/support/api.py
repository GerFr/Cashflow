from __future__ import annotations

from typing import Any

from support.fixtures import CASES, read_case


def fixture_bytes(connector_id: str) -> bytes:
    content, _ = read_case(next(case for cid, case in CASES if cid == connector_id))
    return content


def preview(client, content: bytes, filename: str = "export.csv") -> dict[str, Any]:
    response = client.post("/api/imports", content=content, headers={"X-Filename": filename})
    assert response.status_code == 201, response.text
    return response.json()


def import_file(client, content: bytes, filename: str = "export.csv") -> dict[str, Any]:
    """Preview and commit; returns the import run."""
    response = client.post(f"/api/imports/{preview(client, content, filename)['id']}/commit")
    assert response.status_code == 200, response.text
    return response.json()


def account(client, key: str) -> dict[str, Any]:
    return next(a for a in client.get("/api/accounts").json() if key in (a["iban"], a["external_id"]))
