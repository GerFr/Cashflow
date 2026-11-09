# Roadmap

A local Python service first, one phase at a time; a phone app only if the tool proves useful. Durations are rough guesses for evenings and weekends. Features per phase: [PRODUCT.md](PRODUCT.md).

| Phase | Goal | Done when |
|---|---|---|
| **P0 Skeleton** ✓ | uv project `cashflow/` (package layout `src/cashflow`); the connector engine moved from `tools/` into the package; golden connector tests in pytest; `GET /api/health` and `POST /api/parse` (parse only, nothing stored); UI shell at `/app/` with the tabs and an upload that shows the parsed rows; CI on uv. | CI is green; `uv run dev` → `http://127.0.0.1:8000/app/` opens in the browser; uploading a fixture shows the records of its `expected.json`. |
| **P1 Import & storage** ✓ | SQLite database with `op_log`; import with preview and commit; de-duplication, pending → booked; accounts; balance anchors from exports and opening balances; `balance_daily`. | Importing the Sparkasse and DKB files twice adds nothing the second time; account balances match the bank's. |
| **P2 See your money** (2–4 weeks) | Default categories from `ontology/categories.ttl`; rules and manual correction (Inbox); splits; the [main views](DESIGN.md#views): net-worth line chart with per-date account donut, in/out chart over time, movement bubbles with drill-down (day/week/month/year), trend lines; search. | Real data: net worth for any date, monthly bubbles down to single payments; metrics and the net-worth check match [DESIGN.md](DESIGN.md#metric-definitions). |
| **P3 More sources** | PayPal, more cards and brokers, ING, N26, …; transfers between own accounts; PayPal/card linking; mapping helper for unknown CSVs; anonymiser. | Combined data from all sources shows no double counting. |
| **P4 Smarter** | Categorisation model trained on own corrections; subscriptions, anomalies, forecast; CSV and RDF export (RDF checked against the SHACL shapes in CI). | ≥ 90 % of automatic categories correct on own data; export passes SHACL. |
| **Later** | Phone app (Kotlin Multiplatform, Android first — [DECISIONS.md](DECISIONS.md) #8), receipts with OCR, sync, tax tagging, line-item analytics, Knowledge Graph Manager backend, live bank access, budgets. | — |

## Next actions (P2)

1. Categories: load `ontology/categories.ttl` (rdflib) into a `categories` table at start; `category_assignments` with source (rule, user); `GET /api/categories`.
2. Rules (`merchant/text contains …` → category) and manual correction in the Inbox; user decisions are never overwritten. Transfers between own accounts (same IBAN on both sides) marked as such.
3. Metrics endpoints implementing DESIGN.md: net worth series (`balance_daily` of liquid accounts), money in/out per week/month/year with transfers separate, bubbles per period and level.
4. Vendor ECharts and d3-hierarchy into `resources/ui/assets/vendor/`; Net worth tab (line + donut for a date), Movements, Bubbles with drill-down, Trends.
