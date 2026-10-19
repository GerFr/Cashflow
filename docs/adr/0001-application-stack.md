# 0001 — Application stack: Rust core, Tauri 2, Svelte 5, Python ML workbench

* Status: proposed (to be confirmed by spikes SP-1, SP-2, SP-4, SP-7)
* Date: 2026-10-19
* Requirements: NFR-PORT-01, NFR-PERF-*, SEC-01, §3.3

## Context and problem statement

Cashflow must run on Windows, macOS, Linux, Android and iOS from one codebase, with no backend. It needs fast parsing, an encrypted embedded database, on-device ML inference, P2P networking and rich interactive charts. The maintainer knows Java, Python and some C, and wants to learn current technology.

## Decision drivers

* One codebase for desktop **and** mobile.
* All heavy work (parsing, ML, sync, crypto) local, fast and memory-safe.
* Rich, animated data visualisation (bubbles).
* Strong ecosystem for ONNX/llama.cpp, SQLite, QUIC/P2P, RDF.
* Learning value; a sustainable, contributor-friendly stack.

## Considered options

1. **Rust core + Tauri 2 + Svelte 5 UI; Python only for the ML workbench**
2. Kotlin Multiplatform + Compose Multiplatform; Python for ML training
3. TypeScript PWA (SQLite-WASM/DuckDB-WASM, transformers.js); Python for ML training
4. Python core + local web UI (Streamlit/marimo/NiceGUI)
5. Flutter (Dart)

## Decision outcome

**Option 1.** Rust gives native performance and memory safety on every target, and its ecosystem covers our needs: `rusqlite` + SQLCipher, `ort` (ONNX Runtime), llama.cpp bindings, iroh (QUIC P2P), Oxigraph (RDF), Wasmtime (plugins). Tauri 2 ships the same Rust core to desktop and mobile with a system webview, keeping apps small. Svelte 5 + D3 gives full control over animated SVG/canvas bubble charts. Python stays where it is strongest — model training, evaluation, data generation, notebooks — without becoming a runtime dependency. The maintainer's C background eases the way into Rust, and Java/Python carry over to TypeScript and the workbench.

### Consequences

* ➕ Single core for CLI, desktop, mobile and Python bindings (PyO3).
* ➕ Small binaries; no bundled browser engine.
* ➖ Three languages (Rust, TypeScript, Python). Mitigation: strict boundaries; the UI holds no domain logic, and Python is not shipped.
* ➖ Tauri mobile is younger than native toolkits; camera capture, keystores and background work may need small Kotlin/Swift plugins (risk R-02).
* ➖ Webview differences (WebKit vs. Chromium vs. WebView2) need cross-platform UI tests.

### Why not the others

* **KMP/Compose:** closest to Java and strong on mobile, but weaker for ONNX/llama.cpp integration on all targets, RDF tooling and web-grade data visualisation.
* **PWA:** simplest distribution, but browser storage can be evicted, background sync and P2P are limited, and in-browser ML on phones is constrained.
* **Python core:** best data-science ecosystem, but no credible mobile story and heavy desktop packaging.
* **Flutter:** good cross-platform UI, but a small ecosystem for ML runtimes, RDF and P2P compared with Rust.

## Validation

Spikes SP-1 (Tauri on five platforms), SP-2 (SQLCipher), SP-4 (ONNX on mobile) and SP-7 (bubble performance in webviews) must pass. If Tauri mobile fails SP-1/SP-7 on iOS or Android, fall back to native shells (Kotlin/Swift) around the same Rust core via UniFFI.
