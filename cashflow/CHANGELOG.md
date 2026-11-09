# 0.1.0

- Package skeleton (uv, hatchling, `src/cashflow`), `dev` / `prod` / `update-golden` scripts.
- Connector engine moved from `tools/connector_ref.py`; parses bytes and detects the format from the header.
- `GET /api/health`, `GET /api/connectors`, `POST /api/parse`.
- Static UI under `/app/` with an import tab that parses a bank export.
- Connector conformance suite and API/UI tests in pytest.
- Code connectors behind the same interface as YAML definitions; first one `de.traderepublic.pdf-statement` (PDF statement, checked against the running balance and the account overview).
- New connector `de.dkb.visa-csv-2023` (DKB Visa credit card); `de.dkb.csv-2023` checked against a real export.
