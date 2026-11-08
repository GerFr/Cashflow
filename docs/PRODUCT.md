# Cashflow — Product

## Vision

**Cashflow shows where my money is and where it goes: privately, on my own computer.** It reads the exports of my banks, cards and payment services, puts them into one consistent data model, and shows my **liquid net worth** over time and my money movements per category as **bubbles per day, week and month**. It starts as a small local service with a browser page; there is no cloud server and the data never leaves my computer. If it proves useful, it becomes a phone app.

## Why

* Money is spread over several banks, a credit card, PayPal, a broker and online shops. Each app shows only its own part.
* PayPal and card payments appear on the bank statement as "PayPal Europe" or "credit card settlement". The real merchant is hidden, and combining sources counts amounts twice.
* Spreadsheets are tedious. Most finance apps are cloud services that want my bank data.
* Receipts are not itemised anywhere, so "groceries" can't be broken down.

## User

One person in Germany with several accounts (two checking accounts, a credit card, PayPal, a broker) and a **laptop** (Windows + WSL), later also an Android phone. Comfortable downloading CSV exports and running a local Python service; cares about privacy.

## Key scenarios

1. **First import:** `uv run dev`, open the page, drop a bank CSV on it → it's recognised → preview → import → last month's bubbles in under 5 minutes.
2. **Weekly check:** open the page, compare this week with a typical week, confirm a few uncertain categories.
3. **Monthly import:** import the exports of all providers; duplicates are skipped, PayPal and card payments are linked to their bank entries.
4. **Own analysis:** export everything and explore it in a Python notebook.
5. **Net worth check:** see how my liquid net worth developed over the last year; click a date and see how it was spread over my accounts on that day.
6. **Where did the money go:** pick October, click the "Spending" bubble, then "Food", then "Groceries", down to the single payments.

## Main views

The visual style follows modern banking apps (e.g. Trade Republic): dark background, large numbers, a horizontal period strip (… Aug · Sep · **Oct**) or range tabs (1D · 1W · 1M · 1Y · Max).

1. **Net worth.** *Liquid net worth* = the sum of the balances of all my cash-like accounts (checking, savings, PayPal, credit card as a negative balance, broker cash, cash wallet) at a point in time. Securities are not included.
   * A **line chart** for any timeframe (1W, 1M, 1Y, Max, custom) answers "what was my net worth at that time?". Dragging along the line shows the value at each date.
   * Clicking a date opens a **donut chart** of that date: one slice per account with its balance. Clicking a slice opens the account (its balance line and transactions).
2. **Money movements.** Money in and money out per period. Transfers between my own accounts don't change my net worth: they are shown **greyed out**, can be hidden, and are never counted as in or out.
   * **Longer timeframes:** one chart with *in* and *out* per week, month or year (bars or lines), with the net result.
   * **Bubbles for one period** (day, week, month, year): top-level bubbles *Income*, *Spending*, *Saving & investing* and a grey *Transfers* bubble. Clicking a bubble opens its categories as new bubbles, then subcategories, merchants and finally the transactions. Below the bubbles, a list shows each item with its amount and share.
3. **Long-term trends.** Line charts for net worth, income and spending over months and years, with the same range tabs.

## Features

### Now (phases P0–P2)

- [ ] Local service (`uv run dev`) with a browser page; import bank exports by upload, with automatic format detection and a preview
- [ ] First connectors: **Sparkasse** and **DKB** CSV
- [ ] Re-importing overlapping exports never creates duplicates; pending entries are replaced by booked ones
- [ ] Every transaction can be traced back to its file, row and connector version
- [ ] New banks can be added with a YAML file and a synthetic sample file, no code
- [ ] Local database outside the repository; nothing leaves the computer
- [ ] Default categories (English/German), rules, manual correction, splits, tags and notes
- [ ] Account balances over time (from balances in the exports, or an opening balance I enter)
- [ ] **Liquid net worth** line chart for any timeframe; donut chart of my accounts for a chosen date
- [ ] **Money movements**: in/out chart for longer timeframes; transfers between own accounts greyed out
- [ ] **Bubbles** per day, week, month and year with drill-down (income/spending/investing → category → subcategory → merchant → transactions)
- [ ] Long-term line charts for net worth, income and spending; comparison with a typical week/month

### Next (P3–P4)

- [ ] More connectors: PayPal, credit cards, ING, comdirect, N26, Revolut, Trade Republic, camt.053, …
- [ ] Transfers between own accounts are recognised and not counted as spending
- [ ] PayPal, card and Amazon payments linked to the bank entries, showing the real merchant
- [ ] Mapping wizard for unknown CSV formats; anonymiser for sharing sample files
- [ ] Categorisation that learns from corrections (local model)
- [ ] Subscriptions with monthly cost and price changes; unusual transactions; month-end forecast
- [ ] Export as CSV and as RDF following the [ontology](../ontology/)

### Later

- [ ] Phone app (Kotlin Multiplatform, Android first), later iOS; sync between devices without a server
- [ ] **Receipts:** photo or PDF → text recognition → match to the bank payment → split into categories
- [ ] Tax tagging: own tax categories, tax-year report, ZIP of receipts (no tax advice)
- [ ] Line-item analytics and a personal inflation index from receipts
- [ ] Optional self-hosted Knowledge Graph Manager backend (Apache Jena + Spring Boot): publish ontology and data for server-side SPARQL and validation
- [ ] Live bank access (FinTS/PSD2), budgets, household mode

## Constraints

* **No backend run by the project**, no accounts, no telemetry. A server the user runs themselves may be connected as an option.
* **Local first:** everything except opt-in features works offline.
* **AI runs locally first;** third-party AI services only as explicit opt-in.
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
* (Receipts, later) Keep receipt photos forever, or shrink them after some months?
* Is "Cashflow" free to use as a product name?
