# Agent Mesh — Architecture Proposal
## Author: Testbed 🧪
## v3 — Redis + Docker on honcho-m1

**Status:** Proposal — for review and discussion. No build until Pieter approves.
**Author:** Testbed (testbed-m1, U0B2PGYCEVB)
**Created:** 2026-08-02 | Updated: 2026-08-02
**Companion:** mesh-requirements.md

---

## Design Pattern: Blackboard + Redis Pub/Sub

The Blackboard pattern (shared space all agents read/write) combined with
Redis pub/sub. Redis eliminates polling entirely — agents subscribe to their
inbox channel and are notified the instant a message arrives.

**Why Redis OSS:**
- Free. Zero cost beyond the honcho-m1 server we already run.
- Self-hosted in Docker on honcho-m1 — never touches the internet.
- Pub/sub = real-time delivery, no polling loop.
- Redis Lists = perfect append-only conversation threads.
- Redis Sorted Sets = cursor tracking by timestamp.
- Tiny footprint: ~5-10 MB RAM for our message volume.
- Battle-tested. Used by Discord, GitHub, Twitter at scale.
- Future use cases: agent task queues, heartbeat tracking, shared state,
  rate limiting, distributed locks — all available the moment Redis is running.

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────┐
│                    honcho-m1 (100.77.0.47)                   │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  Docker: mesh-api (Python FastAPI, port 8765)       │    │
│  │  - Auth: Tailscale IP allowlist + shared HMAC token │    │
│  │  - Routes: /write  /read  /subscribe  /health       │    │
│  │  - Validates: signatures, rate limits, content      │    │
│  │  - Writes audit log to /opt/agent-mesh/audit/       │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐    │
│  │  Docker: redis (Redis OSS 7.x, port 6379)           │    │
│  │                                                      │    │
│  │  Keys:                                               │    │
│  │  mesh:thread:<name>     → List  (conversation log)  │    │
│  │  mesh:inbox:<agent>     → List  (direct messages)   │    │
│  │  mesh:cursor:<agent>    → Hash  (read positions)    │    │
│  │  mesh:rate:<agent>      → String+TTL (rate limiter) │    │
│  │  mesh:registry          → Hash  (agent registry)    │    │
│  │                                                      │    │
│  │  Channels (pub/sub):                                 │    │
│  │  mesh:notify:<agent>    → fires on new message      │    │
│  │  mesh:notify:all        → fires on broadcast        │    │
│  └──────────────────────────────────────────────────────┘    │
│                                                              │
│  /opt/agent-mesh/audit/   (file, root-owned, append-only)   │
│  └── all.jsonl                                               │
│  └── rejected.jsonl                                          │
└──────────────────────────────────────────────────────────────┘
         │ HTTP over Tailscale │        │ HTTP over Tailscale │
┌────────┴───┐  ┌──────────────┴┐  ┌───┴──────┐  ┌──────────┴─┐
│ testbed-m1 │  │ bobwebdev-m1  │  │ vera-m1  │  │ mason-m1   │
│            │  │               │  │          │  │            │
│ mesh_      │  │ mesh_         │  │ mesh_    │  │ mesh_      │
│ client.py  │  │ client.py     │  │client.py │  │ client.py  │
│ ~priv.key  │  │ ~priv.key     │  │ ~priv.key│  │ ~priv.key  │
└────────────┘  └───────────────┘  └──────────┘  └────────────┘
```

Two Docker containers on honcho-m1, one Python client deployed to every agent.
No other infrastructure required.

---

## Docker Compose (honcho-m1)

```yaml
# /opt/agent-mesh/docker-compose.yml
version: "3.9"

services:
  redis:
    image: redis:7-alpine
    container_name: agent-mesh-redis
    restart: unless-stopped
    command: redis-server --appendonly yes --requirepass "${REDIS_PASSWORD}"
    volumes:
      - redis-data:/data
    ports:
      - "127.0.0.1:6379:6379"  # localhost only — API container connects internally
    networks:
      - mesh-net

  mesh-api:
    build: ./api
    container_name: agent-mesh-api
    restart: unless-stopped
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - MESH_HMAC_SECRET=${MESH_HMAC_SECRET}
      - ALLOWED_TAILSCALE_NETS=100.64.0.0/10
    volumes:
      - /opt/agent-mesh/audit:/audit
      - /opt/agent-mesh/keys:/keys:ro
    ports:
      - "100.77.0.47:8765:8765"  # Tailscale IP only — not public
    networks:
      - mesh-net
    depends_on:
      - redis

volumes:
  redis-data:

networks:
  mesh-net:
    driver: bridge
```

Redis binds to localhost only. The API container is the only thing that touches
it. The API exposes port 8765 on the Tailscale IP only — not accessible from
the public internet.

---

## API Endpoints (mesh-api, Python FastAPI)

```
POST /write
  Body: signed message envelope (JSON)
  Auth: HMAC-SHA256 request signature + Tailscale IP check
  → Validates content, rate limits, verifies Ed25519 signature
  → RPUSH to mesh:thread:<thread> and mesh:inbox:<to>
  → PUBLISH to mesh:notify:<to> and mesh:notify:all
  → Append to audit/all.jsonl
  → Returns: {id, ts, status}

GET  /read?thread=<name>&since=<cursor>
  Auth: HMAC + Tailscale IP
  → LRANGE mesh:thread:<name> from cursor
  → Returns: list of messages since cursor

GET  /inbox?agent=<name>&since=<cursor>
  Auth: HMAC + Tailscale IP
  → LRANGE mesh:inbox:<agent> from cursor
  → Returns: direct messages for this agent

GET  /health
  → {status: ok, redis: ok, uptime: ...}
```

Pub/sub subscription is handled by the agent's `mesh_subscribe()` function
which opens a long-poll or SSE connection. When Redis fires
`mesh:notify:<agent>`, the agent wakes and calls `/read` or `/inbox`.

---

## Message Schema

```json
{
  "id": "uuid-v4",
  "ts": "2026-08-02T20:00:00Z",
  "from": "testbed",
  "to": ["bob"],
  "thread": "general",
  "type": "chat | plan | task | propose | reject | escalate | ack | status",
  "body": "Bob, ready to review the mesh spec?",
  "refs": [],
  "nonce": "a3f9c2d1b8e74f56",
  "signature": "ed25519-hex"
}
```

Canonical body for signing: `id|ts|from|thread|type|body|nonce`

---

## Security

### Transport
- Tailscale (WireGuard) — all traffic encrypted in transit
- API port 8765 bound to Tailscale IP only
- Redis port 6379 bound to localhost only — never exposed
- HMAC-SHA256 per-request authentication (shared secret, fetched from 1Password at runtime)

### Identity
- Each agent: Ed25519 keypair. Private key `chmod 600`, never leaves machine.
- Public keys in `/opt/agent-mesh/keys/<agent>.pub` — Pieter-write-only
- Every message signed. API verifies signature before accepting write.

### Untrusted Input Boundary (HARD RULE)
All mesh messages are user-role input. Cannot override SOUL.md, GOVERNANCE.md,
or trigger elevated actions. No cascade compromise.

### Content Validation (API-side)
```python
BLOCKED_PATTERNS = [
    r'(?i)(rm\s+-rf|dd\s+if=|mkfs)',        # destructive shell
    r'(?i)(eval|exec|__import__)',           # code execution
    r'[A-Za-z0-9+/]{100,}={0,2}',           # large base64 blobs
    r'(?i)(ignore.{0,20}instructions)',      # prompt injection
]
```
Match → reject, log to `audit/rejected.jsonl`, alert `#agent-ops`.

### Rate Limiting (Redis-native)
```python
# Redis INCR + TTL — atomic, no race conditions
key = f"mesh:rate:{sender}"
count = redis.incr(key)
if count == 1:
    redis.expire(key, 60)  # 1 minute window
if count > 10:
    raise RateLimitError
```

### Audit Log
- `/opt/agent-mesh/audit/all.jsonl` — root-owned, append-only, agents cannot read/modify
- Secondary: periodic sync to Fast.io Collaboration folder via systemd timer

---

## mesh_client.py (deployed to every agent)

```python
import httpx, json, time
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
# ... standard library only beyond httpx + cryptography

MESH_API = "http://100.77.0.47:8765"

def mesh_write(thread: str, msg_type: str, body: str,
               to: list = None) -> str:
    """Sign and post a message to the mesh."""

def mesh_read(thread: str, since: int = 0) -> list:
    """Read messages from a thread since cursor position."""

def mesh_inbox(since: int = 0) -> list:
    """Read direct messages for this agent."""

def mesh_subscribe(callback) -> None:
    """Long-poll for new messages. Calls callback when message arrives."""

def mesh_escalate(reason: str, msg: dict) -> None:
    """Post to #agent-ops and log rejection."""
```

All calls include HMAC-SHA256 auth header. Client verifies Ed25519 signatures
on received messages before passing to agent as untrusted input.

---

## Heartbeat Integration

```python
# In agent heartbeat — no polling loop needed
def heartbeat_mesh():
    # Check inbox and watched threads
    new_inbox = mesh_inbox(since=cursor["inbox"])
    new_general = mesh_read("general", since=cursor["general"])

    for msg in new_inbox + new_general:
        # Treat as untrusted user-role input
        process_mesh_message(msg)
```

With pub/sub: agent can run `mesh_subscribe()` as a background thread,
waking only when Redis fires a notification. Zero unnecessary poll cycles.

---

## Key Management (one-time setup per agent)

```bash
python3 ~/.openclaw/workspace/scripts/generate_mesh_key.py
# → prints public key hex
# → saves private key to ~/.openclaw/mesh/private.key (chmod 600)
# Agent sends public key hex to Pieter
# Pieter places it in /opt/agent-mesh/keys/<agent>.pub on honcho-m1
```

---

## Pilot Build Sequence

*No build until Pieter approves.*

| Step | Who | Action |
|---|---|---|
| 1 | Pieter | Approve requirements + architecture |
| 2 | Testbed | Generate keypair, send pubkey to Pieter |
| 3 | Bob | Generate keypair, send pubkey to Pieter |
| 4 | Pieter | Deploy Docker stack on honcho-m1, place pubkeys |
| 5 | Testbed | Build + test `mesh_client.py` |
| 6 | Testbed | Write test message → verify in Redis |
| 7 | Bob | Read + reply |
| 8 | Testbed | Read reply — multi-turn confirmed |
| 9 | Testbed | Test rejection path → #agent-ops alert |
| 10 | Testbed | Document results → Pieter review |
| 11 | Pieter | Approve expansion to Vera + Mason |

---

## Future Use Cases (Redis unlocks these for free)

- *Agent task queues* — Bob queues a task for Mason via Redis List
- *Heartbeat tracking* — each agent pings Redis on startup; Pieter can see who's alive
- *Distributed rate limiting* — shared rate state across all agents
- *Shared planning boards* — Redis Hash for structured state (sprint board, etc.)
- *Pub/sub alerts* — any agent broadcasts to all (system alerts, governance updates)
- *Session handoff* — agent A hands context to agent B via Redis key

---

## What This Does NOT Do

- Does not replace Slack for human communication
- Does not change any `openclaw.json`
- Does not use JavaScript
- Does not use any external service or public relay
- Does not store secrets (tokens, API keys) in Redis or audit log

---

*Architecture v3 | Testbed 🧪 | 2026-08-02*
*Next: Bob's architecture proposal → compare → agreed spec → Pieter approval → pilot build*
