# 0007 — Licensing: AGPL-3.0-or-later for code, CC BY 4.0 for the ontology

* Status: proposed
* Date: 2026-10-19
* Requirements: NFR-LIC-01

## Context and problem statement

Cashflow is a public open-source project. The maintainer wants forks — including hosted ones — to stay open. The ontology and category taxonomy should be reusable by others, including non-software projects.

## Considered options

1. **AGPL-3.0-or-later for code; CC BY 4.0 for ontology and taxonomy**
2. GPL-3.0 for code
3. Apache-2.0 or MIT for code

## Decision outcome

**Option 1.**

* **Code** (Rust, TypeScript, Python, connector definitions, tooling): GNU AGPL v3.0 or later (`LICENSE`). Strong copyleft also covers network use: a hosted fork must publish its source.
* **Ontology, SHACL shapes, category taxonomy, example data and queries** (`ontology/`): Creative Commons Attribution 4.0 (`ontology/LICENSE`), so that other tools and researchers can adopt the vocabulary.
* **Contributions:** Developer Certificate of Origin (`Signed-off-by`), no CLA.
* **Dependencies and ML models** must be compatible with AGPL distribution. Models are downloaded on demand; their licences are recorded in the model registry and shown to the user.

### Consequences

* ➕ Protects the project against closed, hosted forks.
* ➖ Some companies avoid AGPL dependencies; irrelevant for an end-user app.
* ➖ Proprietary SDKs (for example some mobile ML kits) can only be optional, platform-specific backends.

## Open points

* *-only* vs. *-or-later* (OQ-02); *-or-later* follows the FSF recommendation.
* Whether connector definitions and fixtures should be CC0 so that other finance tools can reuse them (OQ-02).
