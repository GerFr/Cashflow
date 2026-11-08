# Cashflow

**See where your money goes: privately, on your own devices.**

Cashflow is a planned open-source, local-first personal finance tool. It reads the exports of your banks, cards and payment services, puts them into one consistent data model, and shows your **liquid net worth** over time and where your money moves as **bubbles per day, week and month**. It runs as a small local service on your computer with a browser page; nothing goes to a cloud server.

> **Status: planning → phase P0.** A Python FastAPI service (managed with uv) that also serves the frontend; a phone app may follow later. No service code yet; this repository holds the docs, the ontology and the connector definitions with their tests.

## Documents

| Document | Content |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Vision, scenarios, feature checklist (now / next / later) |
| [docs/DESIGN.md](docs/DESIGN.md) | Stack, architecture, storage, identity, metric definitions |
| [docs/DECISIONS.md](docs/DECISIONS.md) | The big choices and why |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases P0–P4 and next actions |
| [ontology/](ontology/) | Data model: OWL ontology, SKOS categories, SHACL shapes |
| [connectors/](connectors/) | Bank export definitions (YAML) with synthetic test files |

## Run the checks

```bash
pip install -r tools/requirements.txt
python tools/validate.py     # connector definitions reproduce their golden outputs
```

From P0 on, the service lives in `cashflow/`:

```bash
cd cashflow
uv sync
uv run dev                   # http://127.0.0.1:8000/app/  ·  API docs: /docs
uv run pytest
```

## Repository layout

```
docs/         product, design, decisions, roadmap
ontology/     OWL ontology, SKOS categories, SHACL shapes (CC BY 4.0)
connectors/   connector definitions, JSON Schema, fixtures with golden outputs
tools/        connector interpreter + golden tests (moves into cashflow/ in P0)
cashflow/     (P0) FastAPI service + static frontend, uv package src/cashflow
```

## Licence

* Code and connector definitions: [GNU AGPL v3.0 or later](LICENSE).
* Everything in `ontology/`: [CC BY 4.0](ontology/LICENSE).
