# 0003 — Ontology-first domain model with a relational runtime

* Status: proposed
* Date: 2026-10-19
* Requirements: EXP-01, CON-03, CAT-01, §5

## Context and problem statement

Cashflow integrates many heterogeneous sources (banks, PayPal, cards, brokers, receipts, e-invoices) into one model. The brief asks for an OWL ontology of payments. We must decide how central the ontology is and how it relates to the runtime database.

## Decision drivers

* A precise, shared vocabulary for connector authors and contributors.
* Interoperability and long-term data portability.
* Machine-checkable data quality.
* Runtime performance on phones.

## Considered options

1. **Ontology-first vocabulary (OWL 2 + SKOS + PROV-O), SHACL for validation, relational runtime, RDF at the boundaries**
2. Ontology as runtime store (triple store + reasoner in the app)
3. No ontology; a conventional relational schema with JSON exports

## Decision outcome

**Option 1.** The ontology (`ontology/cashflow.ttl`) defines every term; categories are a SKOS concept scheme; provenance follows PROV-O; SHACL shapes define what valid data looks like. The app stores data relationally (ADR-0002) using the same terms and exports lossless RDF that must conform to the shapes. Alignment to ISO 20022, schema.org and (later) FIBO keeps the model grounded in standards.

### Consequences

* ➕ One normative vocabulary for UI, database, connectors and exports; `cf:iso20022Path` annotations guide connector authors.
* ➕ SHACL gives executable data-quality rules, also for ML-extracted receipts (warnings for sums that do not add up).
* ➕ Users own their data in an open, self-describing format; SPARQL for power users.
* ➖ Two representations (relational and RDF) must stay in sync. Mitigation: round-trip tests in CI (§4.5).
* ➖ OWL expertise needed for changes. Mitigation: lint in `tools/validate.py`, examples and negative tests.

## Validation

CI (`tools/validate.py`) checks that every used term is declared and documented in English and German, that examples conform and negative examples fail, and that reference queries return the expected metrics. From M1, database exports are validated too.
