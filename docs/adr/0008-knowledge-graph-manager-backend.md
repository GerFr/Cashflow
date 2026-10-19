# 0008 — Optional user-operated Knowledge Graph Manager backend

* Status: proposed, low priority (post-1.0; to be confirmed by a KGM spike before implementation)
* Date: 2026-10-19
* Requirements: KGM-01 … KGM-13, EXP-01, EXP-02, SEC-11, §6.11

## Context and problem statement

The Knowledge Graph Manager (KGM) is a knowledge-graph server built on Apache Jena and Spring Boot. Its REST API (OpenAPI 3.1) manages *projects* that contain ontology graphs, SHACL validation graphs, software mapping graphs and instance graphs, each with a versioned, revertible update history. It also offers SPARQL queries over the instance data, project-wide SHACL validation and Graphviz/Cytoscape views.

The maintainer wants Cashflow to support the KGM as a backend. At the same time, Cashflow is local-first: the project operates no server (RB-01), all core functions must work offline (NFR-USE-01), and data must be encrypted at rest (SEC-01). We have to decide what role a KGM can play without breaking these principles.

## Decision drivers

* Keep local-first, offline use and encryption at rest intact.
* Make the ontology-first model (ADR-0003) usable in a real knowledge-graph server: SPARQL, SHACL and history across all data.
* Exact money values and datatypes must survive the transfer.
* The KGM API is unauthenticated, so finance data must not be exposed by accident.
* Low coupling to an external API that may change.

## Considered options

1. **One-way publisher: SQLite stays the system of record; Cashflow mirrors vocabulary and data to a user-operated KGM project**
2. KGM as the primary store (the app reads and writes only through the KGM API)
3. Two-way sync between SQLite and the KGM in 1.0
4. No KGM support; users import the RDF export (EXP-01) by hand

## Decision outcome

**Option 1.** A new crate `cf-kgm` publishes Cashflow's vocabulary (ontology, categories, SHACL shapes, software mapping) and data (a master-data graph plus one instance graph per import run or receipt batch) to a KGM project. Data is uploaded as Turtle, so `xsd:decimal` and `xsd:date` values survive. Later changes are sent as SPARQL UPDATEs from an op-log outbox. The binding is optional, off by default, limited to loopback URLs unless HTTPS and authentication are configured, and every request is logged (SEC-11). Two-way sync is deferred to after 1.0 (KGM-12); using the KGM as the primary store is rejected (KGM-13).

### Consequences

* ➕ Users with a KGM get server-side SPARQL, validation, graph history and visualisation over their full data, and can combine it with other graphs.
* ➕ One instance graph per import run matches provenance (§5.7): undoing an import deletes exactly one graph.
* ➕ The publisher is built on the existing RDF export and op-log, so the extra code is mostly HTTP and bookkeeping.
* ➖ Data on the KGM is outside Cashflow's encryption and access control. Mitigation: consent dialog, redaction profiles, loopback-only default (KGM-07).
* ➖ The KGM's 400-on-invalid behaviour and lack of idempotency keys need extra client logic (update-history markers, drift detection, KGM-04/05).
* ➖ Instance IRIs must be rewritten to the KGM prefix `http://knowledge-graph-manager/instance#` and back.
* ➖ Some API quirks (404 for empty lists, upload media type, semantic pagination) must be handled and checked by contract tests (KGM-11).

### Why not the others

* **KGM as primary store:** breaks offline use, mobile use without a server, encryption at rest and the P2P sync model (ADR-0002, ADR-0005).
* **Two-way sync in 1.0:** edits in the KGM arrive as arbitrary SPARQL UPDATEs that would have to become domain operations, with conflict handling. That work is too large for 1.0 and only useful once the one-way path has proven itself.
* **Manual RDF import only:** possible today, but it loses incremental updates, consistent IDs and the validation feedback loop.

### Licensing

Cashflow talks to the KGM only over HTTP and contains none of its code, so the KGM's licence does not affect Cashflow's AGPL-3.0 licence (ADR-0007).

## Validation

Spike before implementation (after 1.0) against a running KGM: project and vocabulary setup; upload of the 100 000-transaction fixture as Turtle with `validateData=true`; the reference queries in `ontology/queries/` return the same results through `POST …/instances/sparql` as locally; check of the multipart upload format, the 404-for-empty-list behaviour and the `X-API-Version: 1.1` request bodies against the pinned OpenAPI document.
