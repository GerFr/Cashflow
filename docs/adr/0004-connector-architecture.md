# 0004 — Three-tier connector architecture with a declarative DSL

* Status: proposed (to be confirmed by spikes SP-8, SP-9)
* Date: 2026-10-19
* Requirements: CON-01 … CON-19, §6.2

## Context and problem statement

Connectors that translate provider exports into the ontology are a central part of Cashflow. There are dozens of providers, their formats change without notice, and most contributors will be users who just want *their* bank supported. Connectors process highly sensitive data, so they must be safe to run and easy to review.

## Decision drivers

* Low barrier for contributions (no Rust needed for the common case).
* Safety: a connector must not exfiltrate data or execute arbitrary code.
* Reviewability and testability (golden fixtures).
* Coverage of standards (camt.053, MT940) and odd formats (ZIPs, PDFs).
* Portability across all platforms, including iOS (no JIT).

## Considered options

1. **Three tiers: native standard parsers (Rust) + declarative YAML definitions + sandboxed WASM components**
2. Only native Rust connectors
3. Scripted connectors (embedded Lua/JavaScript/Python)
4. RML/YARRRML mappings directly to RDF

## Decision outcome

**Option 1.**

* **Tier 1** — standards such as ISO 20022 camt.05x and MT940 are parsed natively for performance and correctness.
* **Tier 2** — tabular exports are described by YAML definitions validated by a JSON Schema (`connectors/schema/connector.schema.json`). Definitions are data: easy to write, review, diff and share, and safe to execute. The Python reference interpreter (`tools/connector_ref.py`) is the executable specification; the Rust engine must reproduce its golden outputs (conformance suite).
* **Tier 3** — formats that need real code run as WebAssembly components with no ambient capabilities (input bytes in, canonical records out), on Wasmtime (Pulley interpreter where JIT is not allowed).

All tiers produce the same canonical record; mapping to the ontology happens once, in the core.

### Consequences

* ➕ Most new banks need only a YAML file + anonymised fixture.
* ➕ Untrusted code never runs unsandboxed.
* ➕ Definitions could be reused by other open-source finance tools.
* ➖ The DSL must stay small; anything complex moves to tier 3. Feature requests for the DSL are weighed against this.
* ➖ Two interpreters (Python reference, Rust production) must agree; the fixture suite enforces it.

### Why not the others

* **Native only:** high barrier for contributors; every format change needs a release.
* **Scripting:** a sandboxing and security burden; harder to analyse statically.
* **RML/YARRRML:** standard and elegant for RDF generation, but our runtime is relational (ADR-0003), and bank-specific cleaning (encodings, signs, preambles, cases) is awkward in RML. The canonical record is easier to test.

## Validation

SP-8 (Wasmtime component model on desktop, Android, and Pulley on iOS) and SP-9 (camt.053 parsing). M1 exit: Rust engine output equals the golden files for every fixture.
