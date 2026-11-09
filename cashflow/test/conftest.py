from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from cashflow.app import app
from cashflow.utils.config import get_settings


@pytest.fixture
def data_dir(tmp_path, monkeypatch):
    """Every test gets its own empty database."""
    monkeypatch.setenv("CASHFLOW_DATA_DIR", str(tmp_path))
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


@pytest.fixture
def client(data_dir):
    with TestClient(app) as test_client:
        yield test_client
