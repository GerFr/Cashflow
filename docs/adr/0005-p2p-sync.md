# 0005 — Peer-to-peer sync with iroh and an HLC operation log

* Status: proposed (to be confirmed by spike SP-3)
* Date: 2026-10-19
* Requirements: SYN-01 … SYN-10, §9

## Context and problem statement

The user works on a laptop and a phone (receipt capture on the phone, analysis on the laptop). There must be no central server operated by the project. Sync must be secure, simple to reason about and robust against concurrent edits and identical imports on both devices.

## Decision drivers

* No project-operated infrastructure; works on a home LAN without internet.
* End-to-end encryption and mutual authentication.
* Convergence and no data loss under concurrency.
* Fit with the relational store and op-log (ADR-0002).
* Mobile constraints (NAT, battery, background limits).

## Considered options

Transport:

1. **iroh 1.x** (QUIC, dial by public key, hole punching, optional relays, mDNS discovery crate)
2. libp2p
3. Syncthing-style folder sync through a user-provided cloud folder
4. Plain TLS sockets with manual LAN discovery

Replication:

A. **Custom op-log with HLC timestamps, version vectors, per-field LWW, OR-sets, atomic LWW units for invariants**
B. Loro or Automerge documents
C. cr-sqlite (CRDT-enabled SQLite tables)

## Decision outcome

**Transport 1 + replication A.**

* iroh reached a stable 1.0 in June 2026. It authenticates peers by Ed25519 keys, punches holes through NATs, falls back to relays when needed, and supports LAN discovery via mDNS (separate `iroh-mdns-address-lookup` crate). Relays are off by default (LAN-only), optionally public or self-hosted.
* The op-log from ADR-0002 is the replication unit. HLC timestamps order concurrent writes; version vectors make exchange incremental; deterministic IDs (UUIDv8 from fingerprints) make imports converge without duplicates. Values that carry invariants (the split set of a transaction, the line items of a document) are replicated as atomic LWW units.

### Consequences

* ➕ No server; LAN sync works offline; internet sync optional.
* ➕ Merge rules are simple enough to explain to users and to test exhaustively (deterministic simulation).
* ➖ LWW can overwrite a concurrent edit. Mitigation: field granularity, user-over-automation rule, conflict log for recent local edits, undo.
* ➖ Mobile background sync is opportunistic (OS limits).
* ➖ Public relays and DNS discovery expose metadata (IPs, endpoint ids) when enabled; documented in the settings.

### Why not the others

* **libp2p:** powerful but more complex; iroh's dial-by-key model fits a two-device personal app better.
* **Folder sync:** depends on third-party services and is prone to file-level conflicts; kept only as an encrypted snapshot fallback (SYN-08).
* **Loro/Automerge:** excellent for documents and text; our data is relational with 10⁵ rows and needs SQL queries, so we would duplicate state. Remain candidates for collaborative features later.
* **cr-sqlite:** elegant, but ties us to a SQLite extension whose maintenance and mobile/SQLCipher compatibility would need verification.

## Validation

SP-3: laptop ↔ Android connect via mDNS and via relay. M5 exit: 10 000 random simulation schedules converge; concurrent identical imports produce no duplicates.
