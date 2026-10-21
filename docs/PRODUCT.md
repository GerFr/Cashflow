# Cashflow — Product

## Vision

**Cashflow shows where my money goes: privately, on my own devices.** It reads the exports of my banks, cards and payment services, puts them into one consistent data model, and shows my spending per category as **bubbles per week and month**. Receipts photographed with the phone are read on the device and split the matching payment into categories. There is no server: the data stays on my phone (and later my laptop).

## Why

* Money is spread over several banks, a credit card, PayPal, a broker and online shops. Each app shows only its own part.
* PayPal and card payments appear on the bank statement as "PayPal Europe" or "credit card settlement". The real merchant is hidden, and combining sources counts amounts twice.
* Spreadsheets are tedious. Most finance apps are cloud services that want my bank data.
* Receipts are not itemised anywhere, so "groceries" can't be broken down.

## User

One person in Germany with several accounts (two checking accounts, a credit card, PayPal, a broker), an **Android phone** and a laptop. Comfortable downloading CSV exports; cares about privacy.

## Key scenarios

1. **First import:** share a bank CSV to the app → it's recognised → preview → import → last month's bubbles in under 5 minutes.
2. **Weekly check:** open the app, compare this week with a typical week, confirm a few uncertain categories.
3. **Monthly import:** import the exports of all providers; duplicates are skipped, PayPal and card payments are linked to their bank entries.
4. **Supermarket receipt:** photograph it; the matching bank payment is split into groceries, drugstore and household.
5. **Own analysis:** export everything and explore it in a Python notebook.

## Features

### Now (phases P0–P3)

- [ ] Import bank exports via share sheet or file picker, with automatic format detection and a preview
- [ ] First connectors: **Sparkasse** and **DKB** CSV
- [ ] Re-importing overlapping exports never creates duplicates; pending entries are replaced by booked ones
- [ ] Every transaction can be traced back to its file, row and connector version
- [ ] New banks can be added with a YAML file and a synthetic sample file, no code
- [ ] Encrypted local database; nothing leaves the phone
- [ ] Default categories (English/German), rules, manual correction, splits, tags and notes
- [ ] **Spending bubbles** per week and month with drill-down (category → subcategory → merchant → transactions)
- [ ] Comparison with a typical week/month; trends per category
- [ ] **Receipt capture** with the camera; on-device text recognition; match to the bank payment; split into categories

### Next (P4–P5)

- [ ] More connectors: PayPal, credit cards, ING, comdirect, N26, Revolut, Trade Republic, camt.053, …
- [ ] Transfers between own accounts are recognised and not counted as spending
- [ ] PayPal, card and Amazon payments linked to the bank entries, showing the real merchant
- [ ] Mapping wizard for unknown CSV formats; anonymiser for sharing sample files
- [ ] Categorisation that learns from corrections (on-device model)
- [ ] Subscriptions with monthly cost and price changes; unusual transactions; month-end forecast
- [ ] Export as CSV and as RDF following the [ontology](../ontology/)

### Later (P6 and after)

- [ ] Laptop app (Compose Desktop) and sync between phone and laptop without a server
- [ ] iOS app
- [ ] Tax tagging: own tax categories, tax-year report, ZIP of receipts (no tax advice)
- [ ] Line-item analytics and a personal inflation index from receipts
- [ ] Optional self-hosted Knowledge Graph Manager backend (Apache Jena + Spring Boot): publish ontology and data for server-side SPARQL and validation
- [ ] Live bank access (FinTS/PSD2), budgets, household mode

## Constraints

* **No backend run by the project**, no accounts, no telemetry. A server the user runs themselves may be connected as an option.
* **Local first:** everything except opt-in features works offline.
* **AI on the device first;** third-party AI services only as explicit opt-in.
* **Generic taxes:** no country-specific tax logic, no tax advice.
* **Germany first** for connectors; the design stays international.
* **Open source:** AGPL-3.0-or-later for code, CC BY 4.0 for the ontology.

## Out of scope

* Making payments or changing anything at the bank.
* Storing online-banking passwords; scraping banking websites.
* Portfolio tracking (brokers count only with their cash flows).
* Tax calculation or filing; business bookkeeping.

## Open questions

* Which exact banks, cards and payment services do I use? This decides which connectors come first.
* Weeks start Monday (ISO) and months are calendar months, or should months follow the salary date?
* Keep receipt photos forever, or shrink them after some months?
* Is "Cashflow" free to use as a product name?
