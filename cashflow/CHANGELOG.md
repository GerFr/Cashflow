# 0.2.0

- SQLite database in `CASHFLOW_DATA_DIR` (schema version checked on start); money stored as integer minor units; every change logged in `op_log`.
- Import with preview and commit: `POST /api/imports`, `POST /api/imports/{id}/commit`, `GET /api/imports`. Duplicates skipped by transaction id, pending rows replaced by their booked version, outdated pending rows removed.
- Accounts created from imports (`GET/PATCH /api/accounts`): name, liquid flag, opening balance.
- Balances: closing balances from exports and opening balances as anchors; `balance_daily` per account and day; mismatching anchors reported. `GET /api/accounts/{id}/balances`.
- UI: Import tab with preview and import button; new Accounts tab with balances, liquid flag, opening balances and the liquid total.

# 0.1.0

- Package skeleton (uv, hatchling, `src/cashflow`), `dev` / `prod` / `update-golden` scripts.
- Connector engine moved from `tools/connector_ref.py`; parses bytes and detects the format from the header.
- `GET /api/health`, `GET /api/connectors`, `POST /api/parse`.
- Static UI under `/app/` with an import tab that parses a bank export.
- Connector conformance suite and API/UI tests in pytest.
- Code connectors behind the same interface as YAML definitions; first one `de.traderepublic.pdf-statement` (PDF statement, checked against the running balance and the account overview).
- New connector `de.dkb.visa-csv-2023` (DKB Visa credit card); `de.dkb.csv-2023` checked against a real export.
