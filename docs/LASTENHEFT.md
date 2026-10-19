# Cashflow — Lastenheft (requirements & feature tracker)

| | |
|---|---|
| **Document** | Lastenheft: what Cashflow must do, from the user's point of view, and the tracker for features and milestones |
| **Version** | 0.1.0 — draft for review |
| **Date** | 2026-10-19 |
| **Client (Auftraggeber)** | Project maintainer |
| **Follow-up documents** | [Milestone roadmap](ROADMAP.md) · Pflichtenheft (technical specification, next PR) · [Rust learning path](learning/RUST.md) |

---

## How to use this document

This Lastenheft is the **single list of everything Cashflow should do** and the place where progress is tracked.

* Every feature has an ID `LF-<area>-<nn>`, a **priority** and a **target milestone**.
  * Priorities follow MoSCoW: **M**ust, **S**hould, **C**ould, **W**on't (in 1.0).
  * Milestones `M0`–`M8` are described in the [roadmap](ROADMAP.md); `post` means after 1.0.
* **Status** (update it in the pull request that changes it):

  | Symbol | Meaning |
  |---|---|
  | ⚪ | planned |
  | 🔵 | specified: covered by the Pflichtenheft |
  | 🟡 | in progress |
  | ✅ | done: acceptance criterion met (§8) |
  | ⏸ | deferred |
  | ❌ | dropped |

* **New wishes** start as an issue (template *Feature request*). Once agreed, they get a row here.
* The Pflichtenheft (next PR) turns each feature into detailed, testable technical requirements and references these IDs.

---

## 1. Goals (Zielbestimmung)

### 1.1 Vision

> **Cashflow shows where my money goes: privately, on my own devices.** It reads the exports of all my banks, cards and payment services, translates them into one well-defined ontology, and shows my spending per category as **bubbles per week and month**, with data-science insights on top. Receipts photographed with my phone are broken down into line items by on-device AI, which also helps me collect tax-relevant expenses. There is no server: laptop and phone sync directly with each other.

### 1.2 Initial situation (Ausgangssituation)

* Money is spread over several banks, a credit card, PayPal, a broker and online shops. Each app shows only its own part, with its own categories.
* PayPal and card payments show up on the bank statement as "PayPal Europe" or "credit card settlement", so the real merchant is hidden and amounts are counted twice when sources are combined.
* Spreadsheets are tedious. Most finance apps are cloud services that require handing over bank data, or bookkeeping tools that require manual entry.
* Receipts are not itemised anywhere, so "groceries" cannot be broken down, and tax-relevant purchases get lost.

### 1.3 Goals

| ID | Goal |
|---|---|
| G-1 | See at a glance what I spend in which categories, **per week and per month**. |
| G-2 | Bring all my financial sources into **one consistent model** (an ontology), without double counting. |
| G-3 | Keep all data **private**: on my devices only, no server, no telemetry. |
| G-4 | Use **data science and AI** to categorise automatically and to surface insights (subscriptions, anomalies, forecasts). |
| G-5 | *Bonus:* itemise purchases with **receipts** and collect **tax-relevant** items. |
| G-6 | Build it as a **public open-source** project that is maintainable, and a good way to learn current technology (Rust, local AI). |

---

## 2. Product use (Produkteinsatz)

### 2.1 Target user

One person with several accounts (e.g. two checking accounts, a credit card, PayPal, a broker, occasionally a neobank abroad), living in Germany, shopping online, using **a laptop and a phone**. Comfortable downloading CSV exports; cares about privacy.

### 2.2 Key scenarios

| ID | Scenario |
|---|---|
| S-01 | **First run:** install, drop the first bank export, and see the spending bubbles of last month in under 5 minutes. |
| S-02 | **Weekly review:** open the app, compare this week with a typical week, confirm a handful of uncertain categories. |
| S-03 | **Monthly import:** drop the exports of all providers at once; duplicates are skipped, PayPal and card payments are linked. |
| S-04 | **Supermarket receipt:** photograph it; later the matching bank payment is split into groceries, drugstore and household. |
| S-05 | **Subscriptions:** see all subscriptions with their monthly cost and get notified about price increases. |
| S-06 | **Tax year:** export all items of my own tax categories plus their receipts for the tax software or adviser. |
| S-07 | **Two devices:** pair phone and laptop once; they keep each other up to date at home without any server. |
| S-08 | **Own analysis:** export everything and explore it in a Python notebook. |

---

## 3. Constraints (Rahmenbedingungen)

These were decided in the kickoff on 2026-10-19.

| ID | Constraint |
|---|---|
| RB-01 | **No backend.** The project operates no server; there are no user accounts. |
| RB-02 | **Single user**, several accounts, laptop **and** phone. |
| RB-03 | **Cross-platform** from one codebase: Windows, macOS, Linux, Android, iOS. Stack: Rust core, Tauri 2, Svelte UI; Python only for developing ML models. |
| RB-04 | **Peer-to-peer sync** between the user's devices, without a central server. |
| RB-05 | **On-device AI first.** Third-party AI services are possible only as an explicit opt-in. |
| RB-06 | **Taxes are generic:** no country-specific tax logic in the core, no tax advice. |
| RB-07 | **Germany first** for connectors; the design stays international. |
| RB-08 | **Open source:** AGPL-3.0-or-later for code; CC BY 4.0 for the ontology. Developed in public on GitHub. |
| RB-09 | **Languages:** documentation in English; app in English and German. |

---

## 4. Features (Funktionale Anforderungen)

### 4.1 Import & connectors (`IMP`)

Connectors translate each provider's export into Cashflow's ontology. They are a central part of the product.

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-IMP-01 | Import files by drag & drop (desktop) or share sheet (mobile); the format is detected automatically and previewed before import. | A supported file shows a correct preview without any manual configuration. | M | M1 | ⚪ |
| LF-IMP-02 | First connectors: **Sparkasse** and **DKB** CSV exports. | Real exports (checked locally) import without errors. | M | M1 | ⚪ |
| LF-IMP-03 | ISO 20022 **camt.053** bank statements (offered by many banks). | Sample statements of several camt.053 versions import correctly. | M | M1 | ⚪ |
| LF-IMP-04 | **PayPal** activity export. | Purchases, top-ups, refunds and fees are imported correctly. | M | M1 | ⚪ |
| LF-IMP-05 | Re-importing or overlapping exports **never create duplicates**; pending entries are replaced by booked ones. | Importing the same month twice changes nothing. | M | M1 | ⚪ |
| LF-IMP-06 | Every transaction can be **traced back** to its file, row and connector version. | The source row is shown in the transaction details. | M | M1 | ⚪ |
| LF-IMP-07 | New banks can be added **without programming**, through a small declarative file plus a synthetic sample file. | A contributor adds a bank with one YAML file and one sample; automated tests check it. | M | M1 | ⚪ |
| LF-IMP-08 | More German banks: **ING, comdirect, Volks- und Raiffeisenbanken, Commerzbank, Deutsche Bank, Postbank**. | Each checked against a real export. | M | M3 | ⚪ |
| LF-IMP-09 | **Neobanks & brokers:** N26, Revolut, Wise, bunq, Trade Republic, Scalable Capital (cash flows only, no portfolio tracking). | Each checked against a real export. | M | M3 | ⚪ |
| LF-IMP-10 | **Credit cards:** American Express, Barclays, DKB Visa and others. | Each checked against a real export. | M | M3 | ⚪ |
| LF-IMP-11 | **Transfers between own accounts** (card settlement, PayPal top-up, savings transfer) are recognised and not counted as spending. | Combined data of all sources shows no double counting. | M | M3 | ⚪ |
| LF-IMP-12 | **PayPal, card and Amazon payments are linked** to the matching bank entries, so the real merchant is shown. | "PayPal Europe" bank entries show the actual shop. | M | M3 | ⚪ |
| LF-IMP-13 | **Amazon order history:** the ordered items are attached to the matching payment. | An Amazon card payment shows its items. | S | M3 | ⚪ |
| LF-IMP-14 | **Mapping wizard** for unknown CSV formats; the mapping is saved and can be shared anonymised. | Any reasonable CSV export can be imported after mapping its columns once. | M | M3 | ⚪ |
| LF-IMP-15 | **Anonymiser** that turns a real export into a shareable sample file. | The output contains no real names, IBANs or amounts but keeps the structure. | S | M3 | ⚪ |
| LF-IMP-16 | Unusual formats (PDF statements, ZIP exports) via **sandboxed plugins**. | One PDF or ZIP format works through a plugin. | C | M3 | ⚪ |
| LF-IMP-17 | Legacy **MT940** statements. | Sample files import correctly. | C | M3 | ⚪ |
| LF-IMP-18 | **Live bank access** (FinTS/HBCI or PSD2) instead of manual exports. | Transactions are fetched directly from the bank. | C | post | ⚪ |

### 4.2 Data model & ontology (`DAT`)

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-DAT-01 | An **OWL ontology for payments**: the account the money came from or went to, amount, currency, booking and value date, counterparty, purpose, status, SEPA references. | All imported data can be expressed in the ontology. | M | M1 | ⚪ |
| LF-DAT-02 | The ontology also covers **categories, receipts with line items, tax tags and the origin** (provenance) of every piece of data. | Receipts, line items and tax tags of the examples are expressible. | M | M1 | ⚪ |
| LF-DAT-03 | **Automatic data-quality rules**, e.g. splits and receipt lines must add up to the total. | Inconsistent data is reported, not silently stored. | S | M1 | ⚪ |

### 4.3 Categorisation (`CAT`)

AI-based categorisation uses two kinds of models:

* **Embedding + classifier models** that learn from my own corrections on the device.
* **Typed decision models** ("System One" models) that answer a typed question such as "which of these categories?" with probabilities instead of free text. Examples: **Laya**, reported as open-weight (Apache-2.0, about 322 M parameters in its multilingual variant), which could run on the device; and **TypeSafe Jev** (released September 2026), which is a closed, hosted model and can therefore only be an opt-in cloud option. Both are evaluated in M4; facts to be verified then.

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-CAT-01 | A **default category set** (English/German) that I can edit: add, rename, move, merge, hide. | Categories can be changed without losing history. | M | M2 | ⚪ |
| LF-CAT-02 | **Rules** such as "everything from REWE → Groceries", with a preview of what they change. | A new rule shows the number of affected transactions before it is applied. | M | M2 | ⚪ |
| LF-CAT-03 | **Review inbox** for uncategorised or uncertain transactions, fast to work through with the keyboard (desktop) or swipes (mobile); "always like this" creates a rule. | A week's review takes under 5 minutes. | M | M2 | ⚪ |
| LF-CAT-04 | **Clean merchant names** ("REWE SAGT DANKE 4411…" → "REWE"). | Common German merchants are recognised. | M | M2 | ⚪ |
| LF-CAT-05 | **Split** a payment into several categories. | Splits always add up to the payment amount. | M | M2 | ⚪ |
| LF-CAT-06 | **Tags and notes** on transactions. | Tags can be used as filters in all views. | M | M2 | ⚪ |
| LF-CAT-07 | Automation **never overwrites my own decisions**, and every automatic category can explain **why** it was chosen. | Each automatic category has a visible reason. | M | M2 | ⚪ |
| LF-CAT-08 | **On-device AI categorisation** that learns from my corrections and shows its confidence. | After a few hundred corrections, at least 90 % of the automatically applied categories are correct. | M | M4 | ⚪ |
| LF-CAT-09 | **Typed decision models on the device** (e.g. open-weight Laya), benchmarked against the embedding approach; the better one is used. | Benchmark report on synthetic and own data; choice documented. | S | M4 | ⚪ |
| LF-CAT-10 | **Opt-in cloud categorisation** with hosted models such as TypeSafe Jev or other AI APIs, using my own key, for new merchants or uncertain cases; only minimal data is sent. | Nothing is sent without consent; I can see exactly what is sent. | C | M4 | ⚪ |

### 4.4 Analytics & visualisation (`ANA`) — main focus

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-ANA-01 | **Bubble chart** of spending per category for a week or a month; zoom from category to subcategory to merchant to individual transactions. | The home screen answers "where did my money go this week/month?" without any configuration. | M | M2 | ⚪ |
| LF-ANA-02 | **Step through weeks and months** with animated transitions in which each bubble keeps its place. | Switching periods feels instant (under 0.1 s). | M | M2 | ⚪ |
| LF-ANA-03 | **Bubble timeline:** all categories × all weeks (or months) in one view. | Weekly and monthly patterns are visible at a glance. | M | M2 | ⚪ |
| LF-ANA-04 | **Trends** per category over time. | Any category can be followed over at least 2 years. | M | M2 | ⚪ |
| LF-ANA-05 | **Filters** (accounts, tags, include/exclude transfers and savings) and saved views. | Filters apply to every chart. | M | M2 | ⚪ |
| LF-ANA-06 | Clear, documented **definitions** of spending, income, savings and savings rate, used identically everywhere. | Numbers in all views and exports agree. | M | M2 | ⚪ |
| LF-ANA-07 | **Comparison with a typical week/month** ("+13 % vs. typical") and a list of what changed. | Deviations are highlighted in the bubbles. | S | M4 | ⚪ |
| LF-ANA-08 | **Subscriptions & recurring payments** with monthly and yearly cost and price-change alerts. | Known subscriptions are detected automatically. | S | M4 | ⚪ |
| LF-ANA-09 | **Unusual spending** flagged: unusually large amounts, duplicate charges, unusual weeks. | Every flag explains itself. | S | M4 | ⚪ |
| LF-ANA-10 | **Forecast** of end-of-month spending and balance, with an uncertainty band. | Back-tests show the band is reliable. | S | M4 | ⚪ |
| LF-ANA-11 | **Calendar heatmap**, **Sankey** (income → spending → savings) and **merchant statistics**. | Available for any period. | S | M4 | ⚪ |
| LF-ANA-12 | **Own data science:** export to Parquet, access from Python notebooks, SPARQL queries on the ontology. | An example notebook reproduces the bubble numbers. | S | M4 | ⚪ |
| LF-ANA-13 | **Product-level analytics** from receipts: price history per product, personal inflation rate. | Price history is shown for products bought repeatedly. | S | M7 | ⚪ |
| LF-ANA-14 | **Questions in natural language** ("restaurants this summer vs. last year?"). | The generated query is always shown. | C | M8 | ⚪ |
| LF-ANA-15 | **Budgets** per category. | Budget shown as bubble outline. | C | post | ⚪ |

### 4.5 Receipts (`REC`) — bonus

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-REC-01 | **Photograph receipts** with the phone (edge detection, perspective correction); import images and PDFs on any device. | A crumpled receipt is captured readably. | S | M6 | ⚪ |
| LF-REC-02 | **Line items**, totals, VAT, date and shop are **extracted on the device**. | Totals and dates are correct for ≥ 97 % of typical supermarket receipts. | S | M6 | ⚪ |
| LF-REC-03 | Results are **checked** (do the lines add up?) and easy to **correct** next to the image. | Every receipt that fails a check lands in review. | S | M6 | ⚪ |
| LF-REC-04 | Receipts are **matched to the bank payment**, which is then **split** by the line items' categories. | Most receipts are matched automatically. | S | M6 | ⚪ |
| LF-REC-05 | **E-invoices** (ZUGFeRD, XRechnung) and PDF receipts are read **without OCR**. | Sample e-invoices import exactly. | S | M6 | ⚪ |
| LF-REC-06 | Hard receipts use **larger local AI models**, or are processed on the paired laptop. | Measurably better results on a set of hard receipts. | S | M7 | ⚪ |
| LF-REC-07 | **Opt-in cloud extraction** with my own key for receipts that fail on the device. | Nothing is sent without consent. | C | M7 | ⚪ |
| LF-REC-08 | **Warranty dates** of purchases with reminders. | A reminder appears before the warranty ends. | C | M7 | ⚪ |

### 4.6 Taxes (`TAX`) — generic

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-TAX-01 | Define my **own tax categories** (e.g. "work equipment", "medical", "donations"). | Any number of categories, any country. | S | M7 | ⚪ |
| LF-TAX-02 | **Tag** payments, splits or receipt lines, by hand, by rule or by suggestion. | Suggestions are never applied without my confirmation. | S | M7 | ⚪ |
| LF-TAX-03 | **Tax-year report** plus a **ZIP with all linked receipts**. | Report and ZIP open on any computer. | S | M7 | ⚪ |
| LF-TAX-04 | List of tax-tagged items **without a receipt**. | The list is shown in the report. | S | M7 | ⚪ |
| LF-TAX-05 | Optional **community rule packs** per country, clearly marked "no tax advice". | Off by default. | C | M7 | ⚪ |

### 4.7 Devices & sync (`SYN`)

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-SYN-01 | **Encrypted backup** to a file and restore. | Restore yields exactly the same data. | M | M1 | ⚪ |
| LF-SYN-02 | **Pair** phone and laptop by scanning a QR code. | Pairing takes under a minute. | M | M5 | ⚪ |
| LF-SYN-03 | **Automatic peer-to-peer sync** on the same Wi-Fi, with no server. | Changes appear on the other device within seconds. | M | M5 | ⚪ |
| LF-SYN-04 | Optional **sync over the internet** (relay, can be self-hosted). | Works between different networks when enabled; off by default. | S | M5 | ⚪ |
| LF-SYN-05 | **No data loss or duplicates** when both devices change or import data at the same time. | Importing the same file on both devices yields each transaction once. | M | M5 | ⚪ |
| LF-SYN-06 | **Receipt images** are synced; the phone may keep only thumbnails of older ones. | Receipts captured on the phone open on the laptop. | M | M5 | ⚪ |

### 4.8 Privacy & security (`PRV`)

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-PRV-01 | All data **stays on my devices**: no account, no server, no telemetry. | No network traffic without an explicit action. | M | M1 | ⚪ |
| LF-PRV-02 | Data is **encrypted** on disk. | The database file is unreadable without the key. | M | M1 | ⚪ |
| LF-PRV-03 | **Export everything** and **delete everything**. | After deletion, nothing is recoverable. | M | M1 | ⚪ |
| LF-PRV-04 | **Third-party AI only with explicit consent**, showing exactly what would be sent; API keys stored securely. | Every request is listed in a local log. | M | M4 | ⚪ |
| LF-PRV-05 | **App lock** with fingerprint/face or PIN on mobile. | Locked after a configurable time. | M | M5 | ⚪ |
| LF-PRV-06 | **Network transparency** screen listing every network access (sync, model downloads, opt-in AI). | The list is complete. | M | M5 | ⚪ |

### 4.9 Export (`EXP`)

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-EXP-01 | Export all data as **RDF** following the ontology. | The export passes the ontology's validation rules. | M | M1 | ⚪ |
| LF-EXP-02 | Export transactions as **CSV/Excel**. | Opens correctly in LibreOffice and Excel. | M | M2 | ⚪ |
| LF-EXP-03 | Export to plain-text accounting tools (Beancount, hledger). | Valid journals. | C | post | ⚪ |

### 4.10 App & usability (`APP`)

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-APP-01 | **Command line** for import, export and maintenance (useful before the app exists). | Daily imports possible with the CLI alone. | S | M1 | ⚪ |
| LF-APP-02 | **English and German** user interface. | All texts translated; numbers and dates localised. | M | M2 | ⚪ |
| LF-APP-03 | **Quick start:** from installation to the first bubbles in under 5 minutes (S-01). | Observed with three test users. | M | M2 | ⚪ |
| LF-APP-04 | **Light and dark** themes, colour-blind-safe colours. | Checked with a colour-blindness simulator. | M | M2 | ⚪ |
| LF-APP-05 | **Undo** for every change, including bulk changes. | Any bulk recategorisation can be undone. | M | M2 | ⚪ |
| LF-APP-06 | **Mobile quick actions:** capture receipt, enter cash expense, review inbox. | Each reachable in two taps. | S | M5 | ⚪ |
| LF-APP-07 | **Accessible** (WCAG 2.2 AA); every chart also available as a table. | Accessibility audit passed. | M | M8 | ⚪ |

### 4.11 Platforms & distribution (`PLT`)

| ID | Feature | Acceptance criterion | Prio | MS | Status |
|---|---|---|---|---|---|
| LF-PLT-01 | **Desktop apps** for Windows, macOS and Linux. | Signed installers for all three. | M | M2 | ⚪ |
| LF-PLT-02 | **Mobile apps** for Android and iOS. | Installable beta builds for both. | M | M5 | ⚪ |
| LF-PLT-03 | **Public 1.0 release** through common channels (GitHub Releases, Flathub, F-Droid, App Store/TestFlight). | v1.0.0 published. | M | M8 | ⚪ |

---

## 5. Data (Produktdaten)

Cashflow manages the following data, all stored only on the user's devices (details: Pflichtenheft and ontology, next PR):

* accounts and institutions; transactions with amounts, dates, counterparties, purposes and SEPA references;
* categories, rules, tags, notes, splits and the reasons behind automatic decisions;
* receipts, invoices and online orders with their line items and images;
* tax categories and tax tags;
* the origin of every record (file, row, connector version, AI model used);
* device keys for sync; downloaded AI models.

Design volume: up to 30 accounts, 200 000 transactions (≈ 20 years) and 30 000 receipts.

---

## 6. Quality requirements (Qualitätsanforderungen)

| ID | Quality | Target | Prio | From | Status |
|---|---|---|---|---|---|
| LQ-01 | **Privacy** | No data leaves a device without an explicit user action; opt-in requests are logged. | M | M1 | ⚪ |
| LQ-02 | **Speed** | 10 000 rows imported in ≤ 2 s on a laptop; period switch in bubbles ≤ 0.1 s; app ready in ≤ 1.5 s (laptop) / ≤ 2.5 s (phone). | M | M1 | ⚪ |
| LQ-03 | **Reliability** | No data loss on crash or power failure; same input always gives the same result. | M | M1 | ⚪ |
| LQ-04 | **Offline** | Everything except sync, model downloads and opt-in AI works without network. | M | M1 | ⚪ |
| LQ-05 | **Usability & accessibility** | Keyboard-first on desktop, thumb-first on mobile; WCAG 2.2 AA. | M | M2 | ⚪ |
| LQ-06 | **Portability** | Same features on all five platforms, except where hardware limits apply. | M | M5 | ⚪ |
| LQ-07 | **Maintainability** | Automated tests and CI from the first code; decisions documented as ADRs; every connector tested with sample files. | M | M0 | ⚪ |
| LQ-08 | **Openness** | Open formats (RDF, CSV, Parquet); AGPL code; CC BY ontology; AI models with compatible licences only. | M | M0 | ⚪ |
| LQ-09 | **Scale** | Targets above hold for 200 000 transactions and 30 000 receipts. | S | M4 | ⚪ |

---

## 7. Milestones (overview)

Details, deliverables and exit criteria: [ROADMAP.md](ROADMAP.md).

| Milestone | Theme | Features | Release |
|---|---|---|---|
| **M0** | Planning & foundations: Lastenheft, Pflichtenheft, ontology v0.1, connector language, technical spikes | — (planning) | — |
| **M1** | Core & first connectors (command line) | IMP-01…07, DAT-01…03, SYN-01, PRV-01…03, EXP-01, APP-01 | v0.1 |
| **M2** | Desktop app: **see your spending** (bubbles) | CAT-01…07, ANA-01…06, EXP-02, APP-02…05, PLT-01 | v0.2 alpha |
| **M3** | More connectors & linking | IMP-08…17 | v0.3 |
| **M4** | Data science & AI categorisation | CAT-08…10, ANA-07…12, PRV-04 | v0.4 |
| **M5** | Mobile apps & P2P sync | SYN-02…06, PRV-05…06, APP-06, PLT-02 | v0.5 beta |
| **M6** | Receipts v1 | REC-01…05 | v0.6 |
| **M7** | Receipts v2 & taxes | REC-06…08, TAX-01…05, ANA-13 | v0.7 |
| **M8** | Hardening & 1.0 | ANA-14, APP-07, PLT-03 | **v1.0** |
| post | After 1.0 | IMP-18, ANA-15, EXP-03 | — |

(Feature IDs abbreviated without the `LF-` prefix.)

---

## 8. Acceptance (Abnahme)

* A **feature** is ✅ when its acceptance criterion is demonstrably met (automated test, benchmark report or documented demo), its documentation is updated and the Pflichtenheft requirements derived from it are fulfilled.
* A **milestone** is accepted when all its *Must* features are ✅ and the exit criteria in the [roadmap](ROADMAP.md) are met. *Should* and *Could* features may move to a later milestone (status ⏸ with the new milestone).
* Acceptance happens in the pull request that completes the milestone; the status columns here are updated in the same PR.

---

## 9. Out of scope (Abgrenzung)

* A server or cloud service run by the project; user accounts.
* Making payments or changing anything at the bank.
* Storing online-banking passwords; scraping banking websites.
* Portfolio tracking (securities, performance); brokers count only with their cash flows.
* Tax advice, tax calculation or filing.
* Business bookkeeping.
* Multiple users or households in 1.0 (possible later).

---

## 10. Open questions

| ID | Question |
|---|---|
| OQ-01 | Which exact banks, cards and payment services do I use? This decides which connectors get verified first. |
| OQ-02 | iOS distribution: App Store (developer account), TestFlight only, or EU alternative app stores? |
| OQ-03 | Week starts Monday (ISO) and months are calendar months, or should "months" follow my salary date? |
| OQ-04 | Keep receipt photos forever, or shrink them after some months? |
| OQ-05 | Internet sync off by default (LAN only)? |
| OQ-06 | Budgets already in 1.0? |
| OQ-07 | Is "Cashflow" free to use as a product name (trademark check)? |

---

## 11. Change log

| Version | Date | Change |
|---|---|---|
| 0.1.0 | 2026-10-19 | First version from the kickoff Q&A; AI categorisation with typed decision models (Laya on-device, TypeSafe Jev opt-in) added. |
