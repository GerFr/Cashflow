# Roadmap

A local Python service first, one phase at a time; a phone app only if the tool proves useful. Durations are rough guesses for evenings and weekends. Features per phase: [PRODUCT.md](PRODUCT.md).

| Phase | Goal | Done when |
|---|---|---|
| **P0 Skeleton** ✓ | uv project `cashflow/` (package layout `src/cashflow`); the connector engine moved from `tools/` into the package; golden connector tests in pytest; `GET /api/health` and `POST /api/parse` (parse only, nothing stored); UI shell at `/app/` with the tabs and an upload that shows the parsed rows; CI on uv. | CI is green; `uv run dev` → `http://127.0.0.1:8000/app/` opens in the browser; uploading a fixture shows the records of its `expected.json`. |
| **P1 Import & storage** (1–2 weeks) | SQLite database with `op_log`; import with preview and commit; de-duplication, pending → booked; accounts; balance anchors from exports and opening balances; `balance_daily`. | Importing the Sparkasse and DKB files twice adds nothing the second time; account balances match the bank's. |
| **P2 See your money** (2–4 weeks) | Default categories from `ontology/categories.ttl`; rules and manual correction (Inbox); splits; the [main views](DESIGN.md#views): net-worth line chart with per-date account donut, in/out chart over time, movement bubbles with drill-down (day/week/month/year), trend lines; search. | Real data: net worth for any date, monthly bubbles down to single payments; metrics and the net-worth check match [DESIGN.md](DESIGN.md#metric-definitions). |
| **P3 More sources** | PayPal, credit card, broker, ING, N26, …; transfers between own accounts; PayPal/card linking; mapping helper for unknown CSVs; anonymiser. | Combined data from all sources shows no double counting. |
| **P4 Smarter** | Categorisation model trained on own corrections; subscriptions, anomalies, forecast; CSV and RDF export (RDF checked against the SHACL shapes in CI). | ≥ 90 % of automatic categories correct on own data; export passes SHACL. |
| **Later** | Phone app (Kotlin Multiplatform, Android first — [DECISIONS.md](DECISIONS.md) #8), receipts with OCR, sync, tax tagging, line-item analytics, Knowledge Graph Manager backend, live bank access, budgets. | — |

## Next actions (P1)

1. Add SQLAlchemy; `CASHFLOW_DATA_DIR` setting (default `~/.local/share/cashflow`); models for accounts, transactions, source files and records, import runs, balance observations, `op_log`; tables created in the lifespan.
2. `POST /api/imports` (parse + de-duplicate → preview kept in memory) and `POST /api/imports/{id}/commit` (one database transaction, every write logged in `op_log`); pending rows replaced by their booked version.
3. Accounts: `GET/PATCH /api/accounts` with the liquid flag and an opening balance; closing balances from the exports stored as anchors.
4. `balance_daily`, updated after each import; check that anchors agree.
5. Import tab: preview (new / duplicate / replaced) and an Import button; an accounts list with balances.
