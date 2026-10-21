# Cashflow

**See where your money goes: privately, on your own devices.**

Cashflow is a planned open-source, local-first personal finance app. It reads the exports of your banks, cards and payment services, puts them into one consistent data model, and shows your spending per category as **bubbles per week and month**. Receipts photographed with your phone are read on the device and split the matching payment. There is no server.

> **Status: planning → phase P0.** Android first, built with Kotlin Multiplatform and Compose. No app code yet; this repository holds the docs, the ontology and the connector definitions with their tests.

## Documents

| Document | Content |
|---|---|
| [docs/PRODUCT.md](docs/PRODUCT.md) | Vision, scenarios, feature checklist (now / next / later) |
| [docs/DESIGN.md](docs/DESIGN.md) | Stack, architecture, storage, identity, metric definitions |
| [docs/DECISIONS.md](docs/DECISIONS.md) | The big choices and why |
| [docs/ROADMAP.md](docs/ROADMAP.md) | Phases P0–P7 and next actions |
| [docs/learning/KOTLIN.md](docs/learning/KOTLIN.md) | Kotlin, Compose and Amper for a Java/Maven developer |
| [ontology/](ontology/) | Data model: OWL ontology, SKOS categories, SHACL shapes |
| [connectors/](connectors/) | Bank export definitions (YAML) with synthetic test files |

## Run the checks

```bash
pip install -r tools/requirements.txt
python tools/validate.py     # connector definitions reproduce their golden outputs
```

## Repository layout

```
docs/         product, design, decisions, roadmap, learning notes
ontology/     OWL ontology, SKOS categories, SHACL shapes, examples, SPARQL queries (CC BY 4.0)
connectors/   connector definitions, JSON Schema, fixtures with golden outputs
tools/        reference interpreter of the connector language + golden tests
```

## Licence

* Code and connector definitions: [GNU AGPL v3.0 or later](LICENSE).
* Everything in `ontology/`: [CC BY 4.0](ontology/LICENSE).
