# AscMesh — Work Division
**Project:** Agent Communication Mesh
**Date:** 2026-08-02
**Status:** Approved by Pieter — ready to build

---

## Snapshots Taken (pre-build, confirmed available)

| Machine | Snapshot Name | ID | Status |
|---|---|---|---|
| testbed-m1 | pre-ascmesh-build-testbed-2026-08-02-2016 | 415654051 | ✅ available |
| honcho-m1 | pre-ascmesh-build-honcho-2026-08-02-2017 | 415654054 | ✅ available |
| bobwebdev-m1 | pre-ascmesh-build-bob-TBD | TBD | ⏳ Bob to confirm |

---

## BobWebDev 🏗️ does...

| # | Task | Detail |
|---|---|---|
| B-01 | Hetzner snapshot of bobwebdev-m1 | Name: `pre-ascmesh-build-bob-2026-08-02-HHMM` — report ID in channel |
| B-02 | Ed25519 key generation script | `generate_mesh_key.py` — runs on each agent machine, outputs pubkey hex, saves private key chmod 600 |
| B-03 | `mesh_client.py` — ascmesh worker | Python client: `mesh_write()`, `mesh_read()`, `mesh_inbox()`, `mesh_subscribe()`, `mesh_escalate()` |
| B-04 | ascmesh Docker container (agent-side) | Dockerfile + compose for the worker that runs on each agent machine |
| B-05 | Deploy worker to bobwebdev-m1 | Install, configure, connect to honcho-m1 mesh-api |
| B-06 | Send public key to Pieter | For Pieter to add to SQLite registry on honcho-m1 |
| B-07 | Integration test — receive side | Confirm Bob's worker receives Testbed's first test message and replies |

**Bob's lane:** Everything that runs ON the agent machines. Client code, worker container, key tooling.

---

## Testbed 🧪 does...

| # | Task | Detail |
|---|---|---|
| T-01 | ✅ Snapshot testbed-m1 | DONE — ID: 415654051 |
| T-02 | ✅ Snapshot honcho-m1 | DONE — ID: 415654054 |
| T-03 | Docker Compose on honcho-m1 | Three containers: mesh-api + Redis + SQLite |
| T-04 | Redis container config | redis:7-alpine, appendonly, password from 1Password, internal only |
| T-05 | SQLite schema + init | WAL mode, messages/audit/registry/cursors tables |
| T-06 | mesh-api (FastAPI) | POST /write, GET /read, GET /inbox, GET /health — auth, signing, rate limiting, content validation |
| T-07 | Generate testbed keypair | Send pubkey to Pieter for registry |
| T-08 | Deploy ascmesh worker to testbed-m1 | After Bob delivers B-03/B-04 |
| T-09 | Integration test — send side | Send first test message to Bob, confirm delivery |
| T-10 | Test rejection path | Bad signature → confirm #agent-ops alert fires |
| T-11 | Document results | Full test report to Pieter |

**Testbed's lane:** Everything that runs ON honcho-m1. Server infrastructure, API, database, containers.

---

## Shared / Sequential

| # | Task | Who | Depends on |
|---|---|---|---|
| S-01 | Pieter adds both pubkeys to SQLite registry | Pieter | T-06 + B-06 |
| S-02 | First message: Testbed → Bob | Both | T-08 + B-05 + S-01 |
| S-03 | Multi-turn confirmed (3+ exchanges) | Both | S-02 |
| S-04 | Rejection test passes | Testbed sends, Bob receives alert | S-03 |
| S-05 | Results report to Pieter | Testbed | S-04 |
| S-06 | Pieter approves expansion to Vera + Mason | Pieter | S-05 |

---

## Hard Rules — No Exceptions

- Bob does not touch honcho-m1 infrastructure
- Testbed does not touch bobwebdev-m1
- Neither agent touches the other's private key
- No code merges without the other reviewing
- Any blocker → post in #testing-env immediately, do not work around it

---

## Timeline Target

| Milestone | Target |
|---|---|
| Snapshots done | ✅ Tonight (Testbed done, Bob pending) |
| honcho-m1 Docker stack live | Tonight |
| Both workers deployed | Tonight / early tomorrow |
| First message exchanged | Tomorrow morning CDT |
| Multi-turn confirmed | Tomorrow midday CDT |
| Results to Pieter | Tomorrow midday CDT |

---

## Reference Documents (Fast.io Collaboration folder)

- `mesh-architecture-final.md` — consolidated architecture (Testbed + Bob)
- `mesh-requirements.md` — full requirements
- `work-division.md` — this document

---

*Work Division v1 | 2026-08-02 | Testbed 🧪 + BobWebDev 🏗️*
