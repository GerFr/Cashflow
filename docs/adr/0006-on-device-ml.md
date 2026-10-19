# 0006 — On-device ML first, opt-in third-party processing

* Status: proposed (to be confirmed by spikes SP-4, SP-5, SP-6)
* Date: 2026-10-19
* Requirements: CAT-04, REC-02, REC-03, REC-10, REC-11, SEC-06, NFR-LIC-01, §8

## Context and problem statement

ML is used for categorisation, merchant normalisation and receipt extraction. Financial data and receipts are highly sensitive. The maintainer decided that ML must run on the device by default, with third-party services as an opt-in possibility.

## Decision drivers

* Privacy: nothing leaves the device by default.
* Accuracy on hard receipts (long, crumpled, unusual layouts).
* Performance on phones; app size.
* Licences compatible with an AGPL app.
* Explainability of automatic decisions.

## Considered options

1. **On-device tiered pipelines with a model registry; opt-in cloud as the last tier**
2. Cloud-first (best accuracy, simplest)
3. Strictly on-device, no cloud option at all

## Decision outcome

**Option 1.**

* **Categorisation:** small multilingual embedding model (ONNX via `ort`) + kNN and logistic regression trained on the user's own labels, calibrated with abstention. In addition, **typed decision models** that answer "which of these categories?" with probabilities are evaluated on the device (candidate: open-weight Laya, reported Apache-2.0). A bake-off in M4 decides which approach, or which combination, ships.
* **Receipts:** pre-processing → PP-OCRv5 mobile OCR (ONNX) → structure via a line classifier and a small JSON-constrained LLM → deterministic checks → optional VLM tier (GGUF via llama.cpp) → optional cloud tier. Heavy work can be deferred to a paired laptop.
* **Model registry:** models are downloaded on demand, pinned by hash, with licence metadata shown before download.
* **Opt-in cloud:** user-supplied endpoint and key (Anthropic API, OpenAI-compatible including self-hosted servers, or hosted typed decision models such as TypeSafe Jev for categorisation), per-request consent with payload preview, data minimisation, local request log.

### Consequences

* ➕ Privacy by default with an escape hatch for accuracy.
* ➕ Deterministic checks catch hallucinated or misread numbers regardless of the model.
* ➖ More engineering (several runtimes, tiers, benchmarks) than cloud-first.
* ➖ Model choices change quickly; the registry and the workbench benchmarks keep switching costs low.

## Validation

SP-4 (embeddings and a typed decision model on mobile), SP-5 (OCR on device), SP-6 (local VLM on a laptop). Targets in §8.2 and §8.4 are checked in M4 and M6.
