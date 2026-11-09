# 0.1.0

- Package skeleton (uv, hatchling, `src/cashflow`), `dev` / `prod` / `update-golden` scripts.
- Connector engine moved from `tools/connector_ref.py`; parses bytes and detects the format from the header.
- `GET /api/health`, `GET /api/connectors`, `POST /api/parse`.
- Static UI under `/app/` with an import tab that parses a bank export.
- Connector conformance suite and API/UI tests in pytest.
