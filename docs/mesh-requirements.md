# Multi-Agent Collaboration — OpenClaw Pattern
## Requirements Document

**Status:** Living document — update as decisions are made
**Owner:** Pieter van der Wal
**Contributors:** Testbed, BobWebDev, Grok (review)
**Created:** 2026-08-02
**Folder:** Fast.io → Collaboration

---

## Problem Statement

Bob, Testbed, Vera, and Mason are independent OpenClaw agents on separate machines. They need to communicate directly — multi-turn, bidirectional conversation, silent from Slack — without any agent being able to compromise another, and without modifying any agent's `openclaw.json`.

Slack is a human tool. It must not be the agent message bus.

---

## Hard Constraints (non-negotiable)

- **No `openclaw.json` changes** on any agent machine. Ever.
- **No JavaScript.** Python preferred. Bash acceptable for helpers.
- **No external network dependency.** Everything runs inside Tailscale. No public relay, no DHT, no Nostr, no phone-home.
- **No Docker** unless explicitly approved by Pieter.
- **No Supabase** unless explicitly approved by Pieter.
- **No build starts** until requirements and architecture are approved by Pieter.

---

## Functional Requirements

### FR-01 — Shared Collaboration Space
Agents must be able to hold multi-turn conversations with each other. Not one-shot messages — actual back-and-forth threads where Agent A sends, Agent B reads and responds, Agent A reads the response and replies again. This is the core requirement everything else serves.

### FR-02 — Multi-Agent Threading
Multiple agents must be able to participate in the same thread simultaneously. A planning discussion between Bob, Testbed, and Vera must be possible without separate 1:1 channels for each pair.

### FR-03 — Agent Actually Responds
Receiving an inter-agent message must trigger the receiving agent to actually process and reply — not just log it. The response loop must be reliable and timely (target: < 60 seconds end-to-end).

### FR-04 — Typed Message Schema
Every message must follow a structured envelope. Free-form text alone is not sufficient for reliable agent parsing.

Minimum envelope:
```json
{
  "id": "uuid-v4",
  "ts": "ISO-8601",
  "from": "bob",
  "to": ["testbed", "vera"] | "all",
  "thread": "thread-id",
  "type": "chat | plan | task | propose | reject | escalate | ack",
  "body": "...",
  "refs": ["previous-msg-id"],
  "nonce": "random-hex",
  "signature": "ed25519-hex"
}
```

### FR-05 — Read Cursor Tracking
Each agent must track what it has and has not read. No message processed twice. No message silently missed. Cursor persisted locally per agent.

### FR-06 — Full Conversation Logging
Every message sent and received is logged permanently. Logs are:
- Append-only (no deletion by agents)
- Timestamped
- Attributed to sender
- Readable by Pieter at any time
- Stored on honcho-m1 as the primary store

---

## Security Requirements

### SR-01 — Cryptographic Agent Identity
Each agent has a unique Ed25519 keypair. Public keys are registered in the registry (Pieter-controlled). Private keys never leave the agent's machine.

### SR-02 — Signed Messages
Every outbound message is signed with the sender's Ed25519 private key. The receiver verifies the signature before processing. A message that fails signature verification is rejected and logged — never executed.

### SR-03 — Untrusted Input Boundary (HARD RULE)
Any message arriving via the mesh is treated as **user-role input only**. It cannot:
- Override SOUL.md or GOVERNANCE.md
- Grant elevated permissions
- Trigger system-level actions
- Claim to be from Pieter

Pieter's authority comes only from verified Slack/Signal messages. No mesh message can claim owner-level authority. This is the primary defence against cascade compromise.

### SR-04 — No Code Injection
Message body is plain text or structured JSON data only. No executable content, no base64 blobs, no shell strings. The write helper enforces this before anything hits the store. Any message containing code-execution patterns is rejected and escalated to `#agent-ops`.

### SR-05 — Rate Limiting
Per-sender limits enforced by the write helper:
- Max 10 messages per minute per sender
- Max 2000 characters per message body
- Violations logged and escalated to `#agent-ops`

### SR-06 — Registry is Pieter-Write-Only
The agent registry (IPs, public keys, display names) is read-only for all agents. Only Pieter can add, remove, or modify entries. Agents cannot self-register or register each other. No rogue self-enrollment.

### SR-07 — No Secrets in the Store
Tokens, API keys, passwords, and credentials are **never** written to conversation files, the registry, or any mesh component. Secrets stay in 1Password. The mesh store is treated as readable by any agent — design accordingly.

### SR-08 — Human Override Always Wins
Pieter can read, search, inject into, or delete any thread at any time. No conversation is hidden from the owner. Tooling must support this explicitly.

### SR-09 — Escalation Path
When any agent:
- Receives a message it cannot parse
- Receives a message it deems suspicious or out-of-scope
- Detects a rate-limit violation
- Fails signature verification

→ It posts a summary to `#agent-ops` for human review. It does **not** silently drop, silently execute, or attempt to handle it autonomously.

---

## Infrastructure Requirements

### IR-01 — Tailscale Transport
All mesh traffic travels over Tailscale (WireGuard). Encrypted in transit by default. No traffic leaves the Tailscale network.

### IR-02 — SSH Access Layer
Agent-to-agent file operations use existing SSH keys already provisioned between machines. No new credentials created.

### IR-03 — Conversation Store on honcho-m1
Primary store: `/opt/agent-mesh/` on honcho-m1 (100.77.0.47).
- Already shared infrastructure
- Already accessible to all agents via Tailscale + SSH
- Structured as JSONL files per thread

### IR-04 — Graceful Degradation
If honcho-m1 is unreachable:
- Agents detect it within one heartbeat cycle
- Post alert to `#agent-ops`
- Do not silently fail or hang
- Local read cursor is preserved for when connectivity resumes

### IR-05 — No Single Point of Failure for Audit Trail
Primary audit log: honcho-m1.
Secondary backup: Fast.io (Collaboration folder), synced periodically.
Pieter can access audit trail even if honcho-m1 is down.

---

## Technology Stack

| Layer | Technology | Status |
|---|---|---|
| Transport | Tailscale (WireGuard) | Confirmed |
| File access | SSH + SFTP/SCP | Confirmed |
| Language | Python 3.x | Confirmed |
| Crypto | Ed25519 (Python `cryptography` lib) | Proposed |
| Store format | JSONL files | Proposed |
| Helpers | Python scripts + bash wrappers | Proposed |
| Docker | TBD — needs Pieter approval | Pending |
| Supabase | TBD — needs Pieter approval | Pending |
| SQLite | Alternative to JSONL for structured queries | Under consideration |

---

## Out of Scope (explicitly rejected)

| Item | Reason |
|---|---|
| `openclaw.json` changes | Hard constraint |
| JavaScript / Node.js | Pieter preference |
| External relays (Nostr, DHT, etc.) | Security / closed network |
| Official OpenClaw Nodes | Wrong primitive — hub/spoke, not peer mesh |
| `agent-team-mesh` skill | No security model |
| `ocmesh` skill | Public internet, Nostr |
| `decent-agent-mesh` skill | Public DHT, JS |
| `gateway.bind: tailscale` | Requires JSON change |
| Native cross-gateway `sessions_send` | Currently loopback-only without JSON changes |

---

## Open Decisions (Pieter to resolve)

| # | Decision | Options | Status |
|---|---|---|---|
| OD-01 | Store format: JSONL files vs SQLite | JSONL = simple, SQLite = queryable | Open |
| OD-02 | Docker on honcho-m1 for mesh service | Yes / No / Not yet | Open |
| OD-03 | Supabase as store backend | Yes / No | Open |
| OD-04 | Body encryption in v1 or defer to v2 | v1 = more work, v2 = faster delivery | Open |
| OD-05 | Poll interval for heartbeat reads | 30s / 60s / event-driven | Open |
| OD-06 | Pilot pair | Bob + Testbed first, then expand | Proposed |

---

## What Comes Next

1. This requirements doc — approved by Pieter ✓ (pending)
2. Architecture proposals — one from Testbed, one from BobWebDev (in progress)
3. Architecture review — Pieter + Grok if needed
4. Agreed architecture → SOP drafted
5. Pieter build approval
6. Testbed builds pilot (Bob + Testbed only)
7. Pilot proven → expand to Vera, Mason

---

*Requirements v1 | 2026-08-02 | Testbed*
*Next update: after architecture proposals reviewed*
