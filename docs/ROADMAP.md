# Roadmap

Android first, one phase at a time. Durations are rough guesses for evenings and weekends. Features per phase: [PRODUCT.md](PRODUCT.md).

| Phase | Goal | Done when |
|---|---|---|
| **P0 Setup** (≈1 week) | JDK 21 + Android SDK in WSL, Amper, IntelliJ IDEA; hello-world Compose app on the phone; CI builds the APK and runs the tests. Two-day spike: Amper + Compose + database library + SQLCipher. | An APK built in CI installs on the phone and opens an encrypted database. |
| **P1 Core & import** (2–4 weeks) | Domain types (`Money`, `Account`, `Transaction`, `Category`); encrypted database with `op_log`; Kotlin connector engine (port of `tools/connector_ref.py`); import via share sheet / file picker with preview and de-duplication; balances from exports and opening balances stored as anchors. | The Kotlin engine reproduces every `connectors/fixtures/*/expected.json`; sharing a Sparkasse CSV shows its transactions; re-importing adds nothing; account balances match the bank's. |
| **P2 See your money** (4–6 weeks) | Default categories from `ontology/categories.ttl`; rules and manual correction; splits; the [main views](DESIGN.md#views): net-worth line chart with per-date account donut, in/out chart over time, movement bubbles with drill-down (day/week/month/year), trend lines; search. | Real data on the phone: net worth for any date, monthly bubbles down to single payments; metrics and the net-worth check match [DESIGN.md](DESIGN.md#metric-definitions). |
| **P3 Receipts v1** (≈4 weeks) | Camera capture and crop; encrypted image storage; OCR on the device; total, date and merchant parsed; matched to the transaction; split into categories. | Photographing a receipt splits the matching payment. |
| **P4 Connectors & linking** | PayPal, credit card, ING, N26, …; transfers between own accounts; PayPal/card linking; mapping wizard; anonymiser. | Combined data from all sources shows no double counting. |
| **P5 Smarter** | On-device categorisation model (trained in `ml/`); subscriptions, anomalies, forecast; CSV and RDF export (RDF checked against the SHACL shapes in CI). | ≥ 90 % of automatic categories correct on own data; export passes SHACL. |
| **P6 Laptop & sync** | Compose Desktop app; encrypted backup file; sync between phone and laptop. | Phone and laptop show the same data. |
| **P7 iOS & release** | iOS build (needs a Mac or a CI Mac runner); signed releases; F-Droid build without ML Kit. | Public release. |
| **Later** | Tax tagging, line-item analytics, Knowledge Graph Manager backend, live bank access, budgets. | — |

## Next actions (P0)

1. Install JDK 21 (SDKMAN) and the Android command-line tools in WSL; pair the phone with `adb pair` (wireless debugging).
2. Create the Amper project (`shared/`, `android-app/`) and get a Compose screen onto the phone.
3. Spike: database library + SQLCipher under Amper. If it fails within two days, switch to Gradle and update [DECISIONS.md](DECISIONS.md).
4. Extend CI: build the APK, run the Kotlin tests, keep the Python connector check.
