# Cashflow ontology

The canonical data model of Cashflow: an OWL 2 ontology for personal payments, a SKOS category taxonomy, SHACL shapes for validation and PROV-O based provenance. Design rationale: [ADR-0003](../docs/adr/0003-ontology-first-domain-model.md); full description: [SPECIFICATION §5](../docs/SPECIFICATION.md#5-data-model--ontology-produktdaten).

| File | Content |
|---|---|
| [`cashflow.ttl`](cashflow.ttl) | OWL 2 ontology (`cf:`): parties & accounts, transactions, categorisation, documents & line items, tax tagging, provenance, analytics helpers. English and German labels. |
| [`categories.ttl`](categories.ttl) | Default category scheme (`cfcat:`), SKOS, 15 top-level and 55 subcategories, stable notations, German synonyms. |
| [`shapes.ttl`](shapes.ttl) | SHACL shapes (`cfsh:`); exported data must conform. |
| [`examples/example-data.ttl`](examples/example-data.ttl) | Synthetic example: salary, rent, a receipt-itemised and split purchase, a PayPal-funded subscription, tax tagging, provenance. |
| [`examples/invalid/`](examples/invalid/) | Negative tests: every `ex:bad-*` resource must be reported by the shapes. |
| [`queries/`](queries/) | SPARQL reference implementations of key metrics (bubble input, monthly trend, tax-year report). |

## Namespaces

| Prefix | IRI |
|---|---|
| `cf` | `https://gerfr.github.io/Cashflow/ontology/cashflow#` |
| `cfcat` | `https://gerfr.github.io/Cashflow/ontology/categories#` |
| `cfsh` | `https://gerfr.github.io/Cashflow/ontology/shapes#` |

Instance data exported by the app uses `urn:uuid:` IRIs (UUIDv7 for user-created entities, name-based UUIDv8 for imported transactions; see SPECIFICATION §5.6). The namespace IRIs resolve once the documentation site is published (M1); a permanent w3id.org identifier is open question OQ-01.

## Core ideas in one picture

```
             cf:account                    cf:documentedBy
 Account ◄─────────────── Transaction ───────────────────► Receipt ── cf:lineItem ──► LineItem
                           │   │   │                                                    │
           cf:amount ──────┘   │   └── cf:split ──► Split ── cf:derivedFromLineItem ────┘
   (value ≥ 0 + direction)     │                     │
                               └── cf:category ──► Category (skos:Concept, kind via top concept)
                                                     ▲
                                          cf:category┘
```

* Amounts are non-negative decimals; `cf:direction` (`cf:Debit`/`cf:Credit`) carries the sign, as in ISO 20022.
* Transfers between own accounts are `cf:InternalTransfer`s linked by `cf:transferCounterpart` and are excluded from spending.
* If a transaction has splits, analytics use the splits.
* Every class and property is annotated with the corresponding ISO 20022 camt.053 element where one exists (`cf:iso20022Path`).

## Validate

```bash
pip install -r tools/requirements.txt   # or: uv pip install -r tools/requirements.txt
python tools/validate.py
```

The script lints the ontology (every `cf:` term used anywhere must be declared and documented in English and German), validates the categories and examples against the shapes, checks that every negative example is caught, runs the SPARQL queries against expected results, and runs the connector conformance suite.

## Explore

* Open `cashflow.ttl` in [Protégé](https://protege.stanford.edu/) (OWL 2 DL, no imports needed).
* Query the example with any SPARQL engine, e.g. Python:

```python
from rdflib import Graph
g = Graph()
for f in ["ontology/cashflow.ttl", "ontology/categories.ttl", "ontology/examples/example-data.ttl"]:
    g.parse(f)
for row in g.query(open("ontology/queries/spend-by-top-category.rq").read()):
    print(row.name, row.spend)
```

## Changing the ontology

1. Discuss larger changes in an issue first; record significant decisions as an ADR.
2. Add English and German `rdfs:label`s and an English `skos:definition` to every new term.
3. Extend `shapes.ttl` where the new term needs constraints, and add positive and negative examples.
4. Run `python tools/validate.py`.
5. Before 1.0.0, breaking changes are allowed but must be noted in the PR. Afterwards semantic versioning applies (`owl:versionInfo`, `owl:versionIRI`).

## Licence

Everything in this directory is licensed under [CC BY 4.0](LICENSE). The rest of the repository is AGPL-3.0-or-later.
