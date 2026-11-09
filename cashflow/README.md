# Cashflow service

Local FastAPI service that reads bank exports with the declarative connectors in [`../connectors/`](../connectors/) and serves the Cashflow web page. It listens on `127.0.0.1` only; nothing leaves the computer.

> **Phase P0:** files are parsed and shown, nothing is stored yet. The database arrives in P1, the charts in P2 ([ROADMAP](../docs/ROADMAP.md)).

## Requirements

- [uv](https://docs.astral.sh/uv/) (it installs Python 3.13 if needed)
- A browser

## Setup

```bash
cd cashflow
cp .env.example .env    # optional, only to override defaults
uv sync
```

`uv sync` installs the package in editable mode; the service finds the connector definitions in `../connectors/` relative to this folder.

## Configuration

Only deployment values come from the environment (or `.env`). Everything else is fixed in `src/cashflow/utils/config.py`.

| Variable | Default |
|---|---|
| `CASHFLOW_HOST` | `127.0.0.1` |
| `CASHFLOW_PORT` | `8000` |
| `CASHFLOW_CONNECTORS_DIR` | `../connectors` (repository root) |

## Run

```bash
uv run dev     # development, auto-reload
uv run prod    # without reload
```

UI: `http://127.0.0.1:8000/app/` (from WSL also reachable in the Windows browser)

API base: `http://127.0.0.1:8000/api`

API docs: `http://127.0.0.1:8000/docs`

## UI

Plain HTML, CSS and JavaScript in `src/cashflow/resources/ui/`, served by FastAPI under `/app/`; no build step and no CDN. All `fetch` calls are in `assets/js/api.js`. The tabs Net worth, Movements, Bubbles, Trends and Inbox are placeholders until P2. **Import** parses a dropped or chosen bank export and shows the recognised format, accounts, closing balances and transactions.

## API

| Method | Path | Response |
|---|---|---|
| GET | `/api/health` | `{status, version, connectors}` |
| GET | `/api/connectors` | `[{id, name, version, status, institution}]` |
| POST | `/api/parse` | raw file bytes (CSV, or a Trade Republic PDF statement) + URL-encoded `X-Filename` header; optional `?connector=<id>` → canonical parse result (same shape as the fixtures' `expected.json`). `400` bad filename, `404` unknown connector, `413` larger than 20 MB, `422` not recognised or malformed |

`curl` example:

```bash
curl -H 'X-Filename: export.csv' --data-binary @export.csv http://127.0.0.1:8000/api/parse
```

## Tests

```bash
uv run pytest --cov
uv run ruff check && uv run ruff format --check
```

* `test/unit/test_connectors.py` is the connector conformance suite: every definition must be valid against the JSON Schema and reproduce each fixture's `expected.json`.
* `test/e2e/` drives the API and the static UI through FastAPI's `TestClient`.
* `test/support/traderepublic.py` builds synthetic Trade Republic statements; `uv run python test/support/traderepublic.py` rewrites the PDF fixture.

After changing a connector definition, regenerate its golden files and review every changed value:

```bash
uv run update-golden
git diff ../connectors/fixtures/
```
