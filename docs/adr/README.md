# Architecture decision records

Architecturally significant decisions are recorded here in the [MADR](https://adr.github.io/madr/) format. An ADR is immutable once *accepted*. To change a decision, write a new ADR that supersedes the old one.

| ADR | Title | Status |
|---|---|---|
| [0001](0001-application-stack.md) | Application stack: Rust core, Tauri 2, Svelte 5, Python ML workbench | proposed |
| [0002](0002-local-first-storage.md) | Local-first storage: encrypted SQLite with an operation log | proposed |
| [0003](0003-ontology-first-domain-model.md) | Ontology-first domain model with a relational runtime | proposed |
| [0004](0004-connector-architecture.md) | Three-tier connector architecture with a declarative DSL | proposed |
| [0005](0005-p2p-sync.md) | Peer-to-peer sync with iroh and an HLC operation log | proposed |
| [0006](0006-on-device-ml.md) | On-device ML first, opt-in third-party processing | proposed |
| [0007](0007-licensing.md) | Licensing: AGPL-3.0-or-later for code, CC BY 4.0 for the ontology | proposed |

ADRs stay *proposed* until the M0 spikes have confirmed or refuted their assumptions ([ROADMAP](../ROADMAP.md#m0--planning--foundations-)).

## Template

```markdown
# NNNN — Title

* Status: proposed | accepted | superseded by NNNN
* Date: YYYY-MM-DD
* Requirements: IDs from SPECIFICATION.md

## Context and problem statement
## Decision drivers
## Considered options
## Decision outcome
### Consequences
## Validation
```
