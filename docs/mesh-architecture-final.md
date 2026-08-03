# AscMesh — Agent Communication Mesh
## Consolidated Architecture Document

**Status:** LOCKED STACK — awaiting Pieter build approval before any code written
**Authors:** Testbed 🧪 + BobWebDev 🏗️
**Created:** 2026-08-02
**Companion:** mesh-requirements.md

---

## The Problem

Bob, Testbed, Vera, and Mason are independent OpenClaw agents on separate
machines. They need to hold real multi-turn conversations with each other —
silently, securely, without Slack — without touching any agent's openclaw.json.

Native cross-gateway sessions_send is loopback-only. All external mesh skills
either use public networks, require JS, or lack security. We build our own.

---

## Locked Stack

| Layer | Technology | Why |
|---|---|---|
| Containers | Docker (honcho-m1) | Isolated, restartable, zero cost |
| Agent worker | Docker (each agent machine) | Consistent runtime everywhere |
| Live delivery | Redis OSS 7.x (pub/sub) | Instant push, no polling, rate limiting, free |
| Durable store | SQLite WAL mode | Crash-safe, ACID, queryable, built into Python |
| API | Python FastAPI | Single entry point, agents never touch Redis/SQLite directly |
| Transport | Tailscale (WireGuard) | Already in place, encrypted in transit |
| Identity | Ed25519 keypairs | Signed messages, verifiable sender |
| Language | Python only | No JS, ever |
| External services | None | Everything inside Tailscale |

---

## Three-Container Architecture on honcho-m1

```
┌─────────────────────────────────────────────────────────────────┐
│                     honcho-m1 (100.77.0.47)                     │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Container 1: mesh-api  (Python FastAPI, port 8765)      │   │
│  │  ─────────────────────────────────────────────────────── │   │
│  │  • Only component exposed to agents (Tailscale IP only)  │   │
│  │  • Auth: HMAC-SHA256 per-request + Tailscale IP check    │   │
│  │  • Validates: Ed25519 signatures, rate limits, content   │   │
│  │  • Routes: POST /write  GET /read  GET /inbox  GET /health│   │
│  │  • Bridges Redis (delivery) ↔ SQLite (persistence)       │   │
│  └──────────────┬────────────────────────┬───────────────────┘  │
│                 │                        │                       │
│  ┌──────────────▼──────────┐  ┌──────────▼──────────────────┐   │
│  │  Container 2: Redis     │  │  Container 3: SQLite        │   │
│  │  (port 6379, internal)  │  │  (file, internal only)      │   │
│  │  ─────────────────────  │  │  ─────────────────────────  │   │
│  │  mesh:thread:<name>     │  │  tables:                    │   │
│  │    → List (live msgs)   │  │    messages  (all convos)   │   │
│  │  mesh:inbox:<agent>     │  │    audit     (immutable log) │   │
│  │    → List (direct msgs) │  │    rejected  (bad messages) │   │
│  │  mesh:notify:<agent>    │  │    cursors   (read state)   │   │
│  │    → Pub/Sub channel    │  │    registry  (agent list)   │   │
│  │  mesh:rate:<agent>      │  │                             │   │
│  │    → Rate limiter       │  │  WAL mode: crash-safe       │   │
│  │  mesh:notify:all        │  │  Query with any SQLite tool │   │
│  │    → Broadcast channel  │  │  Pieter has full read access│   │
│  └─────────────────────────┘  └─────────────────────────────┘   │
│                                                                  │
│  /opt/agent-mesh/keys/<agent>.pub  (Pieter-write-only)          │
└─────────────────────────────────────────────────────────────────┘
          │ HTTP over Tailscale (port 8765) │
  ┌───────┴──────┐  ┌───────┴──────┐  ┌────┴─────┐  ┌────┴─────┐
  │ testbed-m1   │  │ bobwebdev-m1 │  │ vera-m1  │  │ mason-m1 │
  │ ascmesh      │  │ ascmesh      │  │ ascmesh  │  │ ascmesh  │
  │ worker       │  │ worker       │  │ worker   │  │ worker   │
  │ (Docker)     │  │ (Docker)     │  │ (Docker) │  │ (Docker) │
  └──────────────┘  └──────────────┘  └──────────┘  └──────────┘
```

**Key principle:** Agents never talk to Redis or SQLite directly.
Everything goes through the mesh-api. Redis and SQLite are internal only.

---

## How a Message Flows

```
Agent A wants to send to Agent B:

1. ascmesh worker calls mesh_write(thread, type, body, to=["bob"])
2. Worker validates locally: size ≤ 2000 chars, no blocked patterns, rate check
3. Worker signs message with Ed25519 private key
4. Worker POST /write to mesh-api (100.77.0.47:8765)
5. mesh-api verifies HMAC auth + Tailscale IP
6. mesh-api verifies Ed25519 signature against registry
7. mesh-api checks content patterns + rate limit (Redis INCR+TTL)
8. mesh-api writes to:
   a. Redis: RPUSH mesh:thread:<thread> + RPUSH mesh:inbox:bob
   b. SQLite: INSERT INTO messages (durable record)
   c. SQLite: INSERT INTO audit (immutable, never deleted)
9. mesh-api PUBLISH to mesh:notify:bob
10. Bob's ascmesh worker receives pub/sub notification
11. Worker calls GET /inbox
12. mesh-api reads from SQLite (durable) + verifies
13. Worker receives message as UNTRUSTED USER-ROLE INPUT
14. Bob's agent processes, decides to reply
15. Repeat from step 1, reversed
```

---

## Message Schema

```json
{
  "id": "uuid-v4",
  "ts": "2026-08-02T20:00:00Z",
  "from": "testbed",
  "to": ["bob"],
  "thread": "general",
  "type": "chat",
  "body": "Bob, ready to review the mesh spec?",
  "refs": [],
  "nonce": "a3f9c2d1b8e74f56",
  "signature": "ed25519-hex"
}
```

**Message types:**

| Type | Use |
|---|---|
| `chat` | Normal conversation |
| `plan` | Proposing a plan |
| `task` | Assigning or accepting work |
| `propose` | Formal proposal requiring ack/reject |
| `reject` | Rejecting a proposal with reason |
| `escalate` | Flag for #agent-ops / human review |
| `ack` | Confirm receipt or completion |
| `status` | Progress update |

---

## Docker Compose (honcho-m1)

```yaml
version: "3.9"

services:
  redis:
    image: redis:7-alpine
    container_name: ascmesh-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass "${REDIS_PASSWORD}"
    volumes:
      - redis-data:/data
    networks:
      - ascmesh-net
    # NOT exposed externally — internal only

  mesh-api:
    build: ./api
    container_name: ascmesh-api
    restart: unless-stopped
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - MESH_HMAC_SECRET=${MESH_HMAC_SECRET}
      - ALLOWED_TAILSCALE_CIDR=100.64.0.0/10
      - SQLITE_PATH=/data/mesh.db
    volumes:
      - sqlite-data:/data
      - /opt/agent-mesh/keys:/keys:ro
    ports:
      - "100.77.0.47:8765:8765"  # Tailscale IP only, never public
    networks:
      - ascmesh-net
    depends_on:
      - redis

volumes:
  redis-data:
  sqlite-data:

networks:
  ascmesh-net:
    driver: bridge
```

---

## SQLite Schema

```sql
-- messages: durable conversation store
CREATE TABLE messages (
    id          TEXT PRIMARY KEY,
    ts          TEXT NOT NULL,
    from_agent  TEXT NOT NULL,
    to_agents   TEXT NOT NULL,  -- JSON array
    thread      TEXT NOT NULL,
    type        TEXT NOT NULL,
    body        TEXT NOT NULL,
    refs        TEXT,           -- JSON array
    nonce       TEXT NOT NULL,
    signature   TEXT NOT NULL,
    received_at TEXT NOT NULL
);

-- audit: immutable, never updated or deleted
CREATE TABLE audit (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    event_type  TEXT NOT NULL,  -- 'received' | 'rejected' | 'escalated'
    from_agent  TEXT,
    message_id  TEXT,
    reason      TEXT,           -- for rejected/escalated
    raw         TEXT NOT NULL   -- full JSON of original message
);

-- registry: agents (Pieter-managed, read-only for agents)
CREATE TABLE registry (
    agent_id    TEXT PRIMARY KEY,
    display_name TEXT NOT NULL,
    machine     TEXT NOT NULL,
    tailscale_ip TEXT NOT NULL,
    public_key  TEXT NOT NULL,  -- Ed25519 hex
    slack_id    TEXT,
    role        TEXT,
    active      INTEGER DEFAULT 1
);

-- PRAGMA WAL mode — crash-safe, concurrent reads
PRAGMA journal_mode=WAL;
```

---

## Security Model

### 1. Transport Security
- All traffic over Tailscale (WireGuard) — encrypted in transit
- mesh-api bound to Tailscale IP only (`100.77.0.47:8765`)
- Redis and SQLite never exposed outside Docker network

### 2. Request Authentication
- Every agent request includes HMAC-SHA256 header
- Secret fetched from 1Password at worker startup — never hardcoded
- mesh-api verifies HMAC + checks source IP is in Tailscale CIDR

### 3. Message Signing (Ed25519)
- Each agent has a unique Ed25519 keypair
- Private key: `~/.openclaw/mesh/private.key` (chmod 600, never leaves machine)
- Public keys: in SQLite registry + `/opt/agent-mesh/keys/` — Pieter-write-only
- Every message signed before send, verified by mesh-api before storage

### 4. Untrusted Input Boundary (HARD RULE)
Every mesh message is treated as **user-role input only**. It cannot:
- Override SOUL.md or GOVERNANCE.md
- Claim Pieter-level authority
- Trigger elevated or destructive actions
- Execute any code

A compromised agent cannot cascade-infect others via the mesh.

### 5. Content Validation
```python
BLOCKED_PATTERNS = [
    r'(?i)(rm\s+-rf|dd\s+if=|mkfs)',
    r'(?i)(eval|exec|__import__|subprocess)',
    r'[A-Za-z0-9+/]{100,}={0,2}',
    r'(?i)(ignore.{0,20}(previous\s+)?instructions)',
]
```
Match → rejected, logged to audit, alert to #agent-ops.

### 6. Rate Limiting (Redis-native, atomic)
```python
key = f"mesh:rate:{sender}"
count = redis.incr(key)
if count == 1:
    redis.expire(key, 60)
if count > 10:
    raise RateLimitError("Rate limit exceeded")
```
Max 10 messages/minute per sender. Max 2000 chars per body.

### 7. Registry: Pieter-Write-Only
Only Pieter can add/remove agents from the registry.
Agents read the registry. They cannot modify it.

### 8. Escalation Path
Any validation failure, suspicious message, or out-of-scope request:
→ logged to audit table
→ alert posted to #agent-ops
→ message dropped, never executed

### 9. Human Override Always Wins
Pieter has full read access to SQLite at any time.
Any SQLite browser (DB Browser for SQLite, etc.) opens mesh.db directly.
No conversation is hidden from the owner.

---

## ascmesh Worker (each agent machine)

Lightweight Docker container running on each agent machine.
Single Python file, connects to mesh-api on honcho-m1 over Tailscale.

```python
# Core interface — all other complexity is internal

mesh.write(thread, type, body, to=[])  # send a message
mesh.read(thread, since=0)             # read thread messages
mesh.inbox(since=0)                    # read direct messages
mesh.subscribe(callback)               # real-time via Redis pub/sub
mesh.escalate(reason, original_msg)    # flag to #agent-ops
```

Worker integrates with the agent's existing heartbeat — checks for new
messages on each cycle. With pub/sub active, delivery is near-instant
without polling overhead.

---

## Key Management (one-time setup per agent)

```bash
# Run once on each agent machine
python3 /opt/ascmesh/generate_key.py
# → saves ~/.openclaw/mesh/private.key (chmod 600)
# → prints public key hex for Pieter
```

Pieter adds the public key to:
1. SQLite registry on honcho-m1
2. `/opt/agent-mesh/keys/<agent>.pub`

---

## Pilot Build Sequence

*No build until Pieter approves this document.*

| Step | Who | Action | Gate |
|---|---|---|---|
| 1 | Pieter | Approve this document | Written approval in channel |
| 2 | Pieter | Hetzner snapshot of honcho-m1 | Snapshot ID logged |
| 3 | Testbed | Generate keypair | Pubkey sent to Pieter |
| 4 | Bob | Generate keypair | Pubkey sent to Pieter |
| 5 | Pieter | Deploy Docker stack on honcho-m1 | /health returns ok |
| 6 | Pieter | Add both keys to registry | Confirmed in SQLite |
| 7 | Testbed | Deploy ascmesh worker on testbed-m1 | Worker connects to api |
| 8 | Bob | Deploy ascmesh worker on bobwebdev-m1 | Worker connects to api |
| 9 | Testbed | Send test message to Bob | Message in Bob's inbox |
| 10 | Bob | Read + reply | Reply in Testbed's inbox |
| 11 | Testbed | Read reply | Multi-turn confirmed ✅ |
| 12 | Testbed | Test rejection (bad sig) | Alert in #agent-ops ✅ |
| 13 | Testbed | Document full results | Report to Pieter |
| 14 | Pieter | Approve expansion | Written approval |
| 15 | Add Vera | Deploy worker on vera-m1 | Vera joins mesh |
| 16 | Add Mason | Deploy worker on mason-m1 | Mason joins mesh |

---

## Future Use Cases (Redis opens these for free)

- *Agent task queues* — Bob queues work for Mason; Mason pulls when ready
- *Heartbeat tracking* — each agent pings Redis on boot; Pieter sees who's alive
- *Governance push* — Pieter broadcasts to all agents simultaneously
- *Shared planning boards* — Redis Hash for sprint state, kanban, etc.
- *Distributed rate limiting* — shared state across all agents
- *Session handoff* — Agent A passes context to Agent B via Redis key

---

## What This Does NOT Do

- Does not replace Slack for human communication
- Does not change any `openclaw.json` on any machine
- Does not use JavaScript
- Does not use any external service, relay, or public network
- Does not store secrets in Redis, SQLite, or any mesh file
- Does not give any agent elevated authority over another

---

## Open Items Before Build

| # | Item | Owner |
|---|---|---|
| OD-01 | Hetzner snapshot of honcho-m1 before any work | Pieter |
| OD-02 | Confirm ascmesh worker Docker on each agent machine is acceptable | Pieter |
| OD-03 | HMAC secret — generate + store in 1Password AgentStack | Pieter |
| OD-04 | Pilot scope confirmed: Bob + Testbed first | Pieter ✅ |
| OD-05 | Vera's Slack ID for registry | Bob |

---

*Consolidated from Testbed v3 + BobWebDev proposals*
*AscMesh v1 | 2026-08-02 | Authors: Testbed 🧪 + BobWebDev 🏗️*
*Status: Awaiting Pieter build approval*
