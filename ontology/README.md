# Cashflow ontology

The shared vocabulary of Cashflow: an OWL 2 ontology for personal payments, a SKOS category list, SHACL shapes and PROV-O provenance. The app stores data relationally with these terms and exports RDF ([DESIGN.md](../docs/DESIGN.md#data-model)).

| File | Content |
|---|---|
| [`cashflow.ttl`](cashflow.ttl) | Ontology (`cf:`): parties & accounts, transactions & money, categorisation, provenance. English and German labels. |
| [`categories.ttl`](categories.ttl) | Default categories (`cfcat:`): 15 top-level, 55 subcategories, stable notations, German synonyms. |
| [`shapes.ttl`](shapes.ttl) | SHACL shapes (`cfsh:`) that exported data must satisfy. |
| [`examples/`](examples/) | Synthetic example data; `invalid/` holds deliberately broken data (`ex:bad-*`). |
| [`queries/`](queries/) | SPARQL versions of the spend metric. |

Namespaces: `cf` = `https://gerfr.github.io/Cashflow/ontology/cashflow#`, `cfcat` = `…/categories#`, `cfsh` = `…/shapes#`. Exported instance data uses `urn:uuid:` IRIs.

```
 Account ◄── cf:account ── Transaction ── cf:split ──► Split
                            │      │                    │
   cf:amount (value ≥ 0) ◄──┘      └── cf:category ──► Category ◄── cf:category
   + cf:direction (debit/credit)                   (skos:Concept, kind on top level)
```

Receipts, tax tagging and analytics helpers are left out until those features are built; the earlier drafts are in the git tag `archive/m0-drafts`.

The files are not checked in CI yet. Once the app exports RDF (phase P5), exports will be validated against `shapes.ttl`. To explore now, open `cashflow.ttl` in [Protégé](https://protege.stanford.edu/) or query the example with rdflib.

Licence: [CC BY 4.0](LICENSE).
