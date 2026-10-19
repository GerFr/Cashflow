# Cashflow

**See where your money goes: privately, on your own devices.**

Cashflow is a planned open-source, local-first personal finance analyser. It reads the exports of your banks, cards and payment services, translates them into one well-defined ontology, and shows your spending per category as **bubbles per week and month**, with data-science insights on top. Receipts photographed with your phone are broken down into line items by **on-device AI**, which also helps you collect tax-relevant expenses. There is **no server**: your laptop and phone sync directly with each other.

> **Status: planning (milestone M0).** This repository currently holds the requirements (Lastenheft) and the milestone roadmap. The technical specification, ontology and connector language follow in the next pull request; code starts in M1.

## Documents

| Document | Content |
|---|---|
| [docs/LASTENHEFT.md](docs/LASTENHEFT.md) | **Lastenheft & feature tracker**: goals, constraints, every feature with acceptance criterion, priority, milestone and status |
| [docs/ROADMAP.md](docs/ROADMAP.md) | **Milestones M0–M8**: deliverables, exit criteria and learning focus |
| [docs/learning/RUST.md](docs/learning/RUST.md) | **Rust learning path** for Java/Python/C developers, tied to the milestones |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |

## Planned features

* **Connectors for your banks**: Sparkasse, DKB, ING, comdirect, VR banks, N26, Revolut, Wise, Trade Republic, PayPal, Amazon orders, credit cards, ISO 20022 camt.053, and more. New banks can be added without programming.
* **One ontology** (OWL) for accounts, payments, categories, receipts and tax tags.
* **Spending bubbles** per week and month, a category × week bubble timeline, comparison with your typical week, trends.
* **Data science & AI**: categorisation that learns from your corrections (embedding models or typed decision models running on the device; hosted models such as TypeSafe Jev only as an opt-in), subscription detection, anomalies, forecasts, export for your own notebooks.
* **Receipts** (bonus): capture with the phone; line items extracted on the device; the bank payment is split automatically.
* **Tax helper**: your own tax categories, tax-year report, ZIP of all receipts. No tax advice, any country.
* **Private by design**: encrypted, no telemetry, peer-to-peer sync between laptop and phone, third-party AI only with your consent.
* **Everywhere**: Windows, macOS, Linux, Android, iOS (Rust + Tauri 2 + Svelte).

## Licence

[GNU AGPL v3.0 or later](LICENSE). The ontology will be published under CC BY 4.0.
