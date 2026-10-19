# 0002 — Local-first storage: encrypted SQLite with an operation log

* Status: proposed (to be confirmed by spike SP-2)
* Date: 2026-10-19
* Requirements: SEC-01, NFR-REL-01, NFR-PERF-*, APP-06, SYN-04, §4.4

## Context and problem statement

All data lives on the user's devices. We need durable, fast, encrypted storage that works identically on desktop and mobile, supports analytics at personal scale (≈ 10⁵ transactions), undo, an audit trail, and is a good basis for P2P sync.

## Decision drivers

* Durability and atomic imports.
* Encryption at rest on every platform.
* Query performance for interactive analytics.
* A natural unit for sync and undo.
* Mature tooling on all five platforms.

## Considered options

1. **SQLite (SQLCipher) + an append-only operation log written in the same transaction as the table changes**
2. Full event sourcing (the op-log as the only source of truth, tables as projections)
3. Embedded triple store (Oxigraph) as the primary database
4. DuckDB as the primary database
5. CRDT document store (Loro/Automerge) as the primary database

## Decision outcome

**Option 1.** SQLite is the most proven embedded database on every platform; SQLCipher adds transparent AES-256 encryption. Writing each mutation as an operation into `op_log` *and* applying it to normal tables in the same transaction gives us undo, an audit trail and the sync feed, without the complexity of rebuilding projections (option 2). Amounts are stored as `i64` minor units. Analytics run on indexed tables plus an incrementally maintained daily roll-up.

### Consequences

* ➕ Simple queries, migrations and debugging with standard tools.
* ➕ Op-log enables undo (APP-06) and sync (ADR-0005) from day one.
* ➖ Every write path must go through the op-log API (enforced by keeping table writes private to `cf-store`).
* ➖ SQLCipher builds add native-dependency complexity on mobile (risk R-09).

### Why not the others

* **Triple store:** great for the ontology, but slower and less mature for transactional, aggregated workloads; RDF stays at the boundaries (ADR-0003).
* **DuckDB:** excellent OLAP, but weaker for many small transactional writes and less proven on mobile; Parquet export covers OLAP use cases (ANA-17).
* **CRDT store:** attractive for sync, but a poor fit for relational data and large collections (ADR-0005).

## Validation

SP-2: SQLCipher via `rusqlite` works on all platforms; 100 000-transaction fixture meets NFR-PERF-02/03 with the roll-up table.
