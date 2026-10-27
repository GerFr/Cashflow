# Decisions

Short records of the big choices. To change one, add a new entry that replaces it.

## 1. Kotlin Multiplatform + Compose, Android first (2026-10-21)

**Context:** The first draft chose Rust + Tauri + Svelte. The developer knows Java and Python; Rust's learning curve would slow everything down. The phone (receipt capture, quick checks) matters more early on than the laptop.
**Decision:** Kotlin Multiplatform with Compose Multiplatform. Android first, desktop (Compose Desktop) and iOS later from the same `shared` code. Build with JetBrains Amper; if Amper can't handle the database or camera setup in P0, switch to Gradle Kotlin DSL.
**Consequences:** Familiar JVM ecosystem and tooling. iOS needs a Mac later. Bubble charts are drawn with Compose Canvas instead of D3.

## 2. Encrypted SQLite with an operation log (2026-10-19)

**Context:** All data lives on the user's devices; it must be durable, fast, encrypted and undoable.
**Decision:** One SQLite database per profile, encrypted with SQLCipher. Every change is appended to `op_log` and applied to normal tables in the same transaction.
**Consequences:** Simple queries and debugging; undo and audit for free; a ready-made feed for sync later. All writes must go through one storage API.

## 3. Ontology as vocabulary, relational at runtime (2026-10-19)

**Context:** Many heterogeneous sources need one precise model; data should be portable.
**Decision:** An OWL 2 ontology (with SKOS categories, SHACL shapes, PROV-O provenance) defines the terms. The app stores data relationally with the same terms and exports RDF. No triple store in the app.
**Consequences:** Clear shared vocabulary and open exports; two representations to keep aligned (checked once RDF export exists, P5).

## 4. Declarative connectors with golden fixtures (2026-10-19)

**Context:** Bank export formats are many and change without notice.
**Decision:** Tabular formats are described in YAML definitions interpreted by a connector engine. Each definition ships synthetic fixtures with a golden `expected.json`. A Python reference interpreter is the executable specification; the Kotlin engine must match it.
**Consequences:** New banks without code; formats are reviewable data. Exotic formats (PDF, ZIP) need code connectors later.

## 5. On-device AI first, cloud only as opt-in (2026-10-19)

**Context:** Financial data is sensitive; phones can run small models.
**Decision:** Categorisation and receipt reading run on the device (ONNX Runtime, ML Kit to start). Hosted models only per request, with the user's own key and a local log. Models are trained in a Python workbench.
**Consequences:** Privacy by default; quality limited by small models at first. ML Kit is proprietary, so an F-Droid build later needs PaddleOCR via ONNX.

## 6. Licensing (2026-10-19)

**Decision:** Code AGPL-3.0-or-later; ontology, categories and examples CC BY 4.0.
**Consequences:** Improvements to the app stay open; the vocabulary can be reused freely with attribution. Dependencies and models must be AGPL-compatible.

## 7. Sync deferred (2026-10-21)

**Context:** Peer-to-peer sync is a large piece of work and only useful once a second device runs Cashflow.
**Decision:** No sync until P6. The op-log and deterministic IDs keep the option open. First step then: an encrypted backup file; after that LAN sync or iroh.
**Consequences:** Phase 1–5 are single-device.
