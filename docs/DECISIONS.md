# Decisions

Short records of the big choices. To change one, add a new entry that replaces it.

## 1. Python-first local service; phone app later (2026-11-08)

**Context:** Cashflow is first of all a personal utility. A phone app (decision 8) is a lot of work before it is clear the tool is worth it; the developer is fastest in Python.
**Decision:** A local FastAPI service, managed with uv in package layout (`cashflow/src/cashflow`), that also serves a static frontend (plain JavaScript, vendored ECharts and d3-hierarchy, no build step). SQLite via SQLAlchemy. It binds to `127.0.0.1` only. The existing Python connector interpreter becomes the import engine.
**Consequences:** Working views within weeks, in a familiar language. No phone use for now. Domain logic stays free of web code, so the rules, metric definitions, connector definitions and fixtures carry over to an app.

## 2. SQLite with an operation log (2026-11-08, replaces the SQLCipher version of 2026-10-19)

**Context:** All data lives on the user's own computer; it must be durable, fast and undoable.
**Decision:** One SQLite database in a data directory outside the repository (`~/.local/share/cashflow` by default). Every change is appended to `op_log` and applied to the normal tables in the same transaction. No database encryption for now: the data relies on disk encryption and the service listens on localhost only. SQLCipher comes with the phone app.
**Consequences:** Simple queries and debugging; undo and audit for free; a ready-made feed for sync later. All writes must go through one storage API.

## 3. Ontology as vocabulary, relational at runtime (2026-10-19)

**Context:** Many heterogeneous sources need one precise model; data should be portable.
**Decision:** An OWL 2 ontology (with SKOS categories, SHACL shapes, PROV-O provenance) defines the terms. The app stores data relationally with the same terms and exports RDF. No triple store in the app.
**Consequences:** Clear shared vocabulary and open exports; two representations to keep aligned (checked once RDF export exists, P4).

## 4. Declarative connectors with golden fixtures (2026-10-19)

**Context:** Bank export formats are many and change without notice.
**Decision:** Tabular formats are described in YAML definitions interpreted by a connector engine. Each definition ships synthetic fixtures with a golden `expected.json`. The Python engine in the service runs them; a later app engine must produce the same output.
**Consequences:** New banks without code; formats are reviewable data. Exotic formats (PDF, ZIP) need code connectors later.

## 5. Local AI first, cloud only as opt-in (2026-11-08)

**Context:** Financial data is sensitive; small models run fine locally.
**Decision:** Categorisation (and receipt reading later) runs locally in Python: scikit-learn first, small ONNX or embedding models later. Hosted models only per request, with the user's own key and a local log.
**Consequences:** Privacy by default; quality limited by small models at first.

## 6. Licensing (2026-10-19)

**Decision:** Code AGPL-3.0-or-later; ontology, categories and examples CC BY 4.0.
**Consequences:** Improvements to the app stay open; the vocabulary can be reused freely with attribution. Dependencies and models must be AGPL-compatible.

## 7. Sync deferred (2026-10-21)

**Context:** Peer-to-peer sync is a large piece of work and only useful once a second device runs Cashflow.
**Decision:** No sync until there is a phone app. The op-log and deterministic IDs keep the option open. First step then: an encrypted backup file; after that LAN sync or iroh.
**Consequences:** Single device until then.

## 8. Later: Kotlin Multiplatform app, Android first (2026-10-21, deferred 2026-11-08)

**Context:** The first draft chose Rust + Tauri + Svelte; the developer knows Java and Python, so Kotlin is the easier path to a phone app.
**Decision:** If the local service proves useful, the app is built with Kotlin Multiplatform and Compose Multiplatform: Android first, desktop and iOS later, with JetBrains Amper (Gradle Kotlin DSL as fallback) and SQLCipher. Notes: [learning/KOTLIN.md](learning/KOTLIN.md).
**Consequences:** The service's domain logic is the specification for the app; the connector fixtures check both.
