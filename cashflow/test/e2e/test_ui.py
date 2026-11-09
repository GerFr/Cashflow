from __future__ import annotations

import pytest

from cashflow import app as app_module


def test_root_redirects_to_ui(client):
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 308)
    assert response.headers["location"] == "/app/"


@pytest.mark.parametrize("path", ["/app", "/app/"])
def test_ui_index_is_served(client, path):
    response = client.get(path)
    assert response.status_code == 200
    for marker in ['id="import-form"', 'data-view="networth"', 'data-view="bubbles"', "/app/assets/app.css"]:
        assert marker in response.text


def test_every_script_in_the_index_exists(client):
    html = client.get("/app/").text
    scripts = [part.split('"')[0] for part in html.split('<script src="')[1:]]
    assert scripts
    for src in scripts:
        response = client.get(src)
        assert response.status_code == 200, src
        assert "javascript" in response.headers["content-type"]


def test_stylesheet_and_missing_asset(client):
    stylesheet = client.get("/app/assets/app.css")
    assert stylesheet.status_code == 200
    assert "text/css" in stylesheet.headers["content-type"]
    assert client.get("/app/assets/missing.js").status_code == 404


def test_missing_ui_assets_return_503(client, monkeypatch, tmp_path):
    monkeypatch.setattr(app_module, "UI_INDEX_PATH", tmp_path / "index.html")
    response = client.get("/app/")
    assert response.status_code == 503
    assert "UI assets missing" in response.text
