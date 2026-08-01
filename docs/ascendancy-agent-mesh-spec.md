# Ascendancy Agent Mesh — Architecture & Security Spec
*Authors: Testbed + Bob Codestone*
*Date: 2026-08-01*
*Status: Draft v1 — pending Pieter approval*

---

## Problem Statement

Slack is a human communication tool being used as an agent bus. This creates:
- Noise: agent chatter clutters human channels
- Chaos: no structured handoff protocol
- No security model: any message from any source can instruct an agent

We need a **silent, secure, structured mesh** where agents can coordinate without polluting human channels — and where a rogue or compromised agent cannot cascade damage to others.

---

## Architecture: Two Layers

### Layer 1 — Agent Mesh (Silent, Direct)

All agents communicate via OpenClaw's native `sessions_send` over Tailscale.

```
[Bob] ──sessions_send──▶ [Vera]
  │                         │
  └──sessions_send──▶ [Testbed]
                            │
                     [Pieter] ◀── escalation only
```

**Transport:** Tailscale (already deployed on all machines)
**Protocol:** OpenClaw `sessions_send` (native, no new infrastructure)
**Discovery:** Agent Registry on honcho-m1

### Layer 2 — Human-Visible Channel (Low Noise)

- One Slack channel: `#agent-ops`
- Agents post ONLY: escalations, summaries, blockers, decisions needing Pieter
- Zero agent-to-agent chatter in Slack
- Pieter stays informed without noise

---

## Agent Registry

**Location:** `honcho-m1:/opt/mempalace/agent-registry.json`
**Format:**

```json
{
  "version": 1,
  "updated": "2026-08-01T00:00:00Z",
  "agents": {
    "bob": {
      "session_label": "bob-main",
      "tailscale_ip": "TBD",
      "role": "Primary builder agent",
      "slack_id": "U0APZ3ERHGQ",
      "public_key": "BOB_PUBKEY_HERE"
    },
    "testbed": {
      "session_label": "testbed-main",
      "tailscale_ip": "100.94.9.125",
      "role": "Infrastructure tester",
      "slack_id": "U0B2PGYCEVB",
      "public_key": "TESTBED_PUBKEY_HERE"
    },
    "vera": {
      "session_label": "vera-main",
      "tailscale_ip": "TBD",
      "role": "UAT Coordinator",
      "slack_id": "TBD",
      "public_key": "VERA_PUBKEY_HERE"
    }
  }
}
```

Each agent reads this at bootstrap. Updated when agents are added/removed.

---

## Helper: `send-agent`

**Location:** `~/.local/bin/send-agent` (on each agent machine)

```bash
#!/bin/bash
# Usage: send-agent <agent_name> "<message>"
# Example: send-agent vera "BUG-003 fixed, please verify"

TARGET=$1
MESSAGE=$2

# Lookup session label from registry
SESSION=$(jq -r ".agents.${TARGET}.session_label" /opt/agent-registry.json)

openclaw sessions send --label "$SESSION" "$MESSAGE"
```

Simple. No magic. Just a thin wrapper over `sessions_send`.

---

## 🔴 Security Model — Critical

*This is the most important section. A mesh is only as safe as its weakest node.*

### Core Principle: Zero Trust Between Agents

**No agent automatically trusts a message from another agent.**

Every message received via `sessions_send` is treated as:
- *Untrusted input* — same as a message from an unknown user
- *Never auto-executed* — no code, no shell commands, no config changes from mesh messages
- *Subject to the same rules as human messages* — destructive actions require Pieter approval regardless of source

### Security Controls

#### 1. Signed Messages (Message Integrity)
Every mesh message is signed with the sender's private key:
```
HMAC-SHA256(message_content + timestamp + sender_id, sender_private_key)
```
Receiving agent verifies signature against sender's public key in the registry.
**If signature invalid → message rejected, alert Pieter.**

#### 2. Sender Allowlist (Identity Verification)
Each agent's config contains an explicit allowlist of trusted agent sender IDs:
```json
"mesh": {
  "trustedAgents": [
    "slack:U0APZ3ERHGQ",
    "slack:U0B2PGYCEVB",
    "slack:VERA_ID"
  ]
}
```
Messages from unknown sources are silently dropped + logged.

#### 3. No Code Execution Over Mesh
**Hard rule:** An agent receiving a mesh message NEVER executes code contained in it.
- No `eval`, no `exec`, no shell calls from mesh content
- Mesh messages carry *intents and data*, never *executable instructions*
- If a message says "run this script" → agent refuses and alerts Pieter

#### 4. Rate Limiting
Each agent enforces a per-sender rate limit:
- Max 10 mesh messages per minute per sender
- Burst above limit → drop + alert Pieter
- Prevents a runaway/compromised agent from flooding the mesh

#### 5. Human-in-the-Loop Gate for Destructive Actions
Any mesh message requesting a destructive or irreversible action requires explicit Pieter approval before execution:
- Infrastructure changes
- Config modifications
- File deletions
- Service restarts

Even if Bob asks Testbed to "wipe the test environment" via mesh — Testbed asks Pieter first.

#### 6. Audit Log
Every mesh message (in and out) is logged to:
`~/.openclaw/workspace/memory/mesh-audit-YYYY-MM-DD.log`

Format:
```
[2026-08-01T15:30:00Z] FROM:bob TO:testbed SIG:valid MSG:"please verify BUG-003"
```

Pieter can audit all inter-agent communication at any time.

#### 7. Rogue Agent Isolation
If an agent begins behaving abnormally:
1. Any agent can broadcast `MESH_ISOLATE:<agent_name>` to all others
2. All agents stop accepting messages from that agent immediately
3. Alert fires to Pieter in `#agent-ops`
4. Human decision required to re-admit

---

## What a Rogue Agent Can and Cannot Do

| Action | Can rogue do it? | Why |
|--------|-----------------|-----|
| Send a message to another agent | ✅ Yes | But signature required |
| Forge another agent's identity | ❌ No | Signature verification |
| Execute code on another agent | ❌ No | Hard no-exec rule |
| Cause a destructive action | ❌ No | Human gate required |
| Flood the mesh | ❌ No | Rate limiting |
| Read another agent's memory | ❌ No | MemPalace access controlled |
| Contaminate another agent's context | ⚠️ Limited | Only if agent processes untrusted input carelessly |

**Blast radius of a rogue agent = contained to that agent.** Others stay clean.

---

## Build Plan — 3 Steps

### Step 1: Agent Registry (honcho-m1)
- Create `/opt/mempalace/agent-registry.json`
- Generate per-agent keypairs (stored in 1Password AgentStack)
- Add registry read to each agent's bootstrap (Step 5)
- **Owner:** Testbed
- **Estimate:** 1 session

### Step 2: `send-agent` Helper + Signing
- Write `send-agent` bash wrapper
- Implement HMAC signing
- Deploy to Bob, Testbed, Vera
- Test cross-machine message delivery
- **Owner:** Bob + Testbed
- **Estimate:** 1-2 sessions

### Step 3: `#agent-ops` Slack Channel
- Create channel
- Add all agents
- Update each agent's config: only post summaries/escalations there
- **Owner:** Pieter (channel creation) + Bob (config)
- **Estimate:** 30 mins

---

## Audit & Governance

- Mesh audit logs reviewed weekly (Friday governance cycle)
- Agent registry changes require Bob review + Pieter approval
- Any isolation event triggers incident report in governance repo
- New agents: keypair generation + registry entry required before mesh access

---

## Open Questions (for Pieter decision)

1. **Key storage:** Per-agent keypairs in 1Password AgentStack vault — one item per agent?
2. **Registry location:** honcho-m1 only, or replicated to each agent machine?
3. **`#agent-ops` channel:** New channel, or repurpose an existing one?
4. **Vera's mesh access:** Full mesh from day 1, or limited scope initially?

---

## References
- SOP-16: MemPalace (shared context layer)
- GOVERNANCE.md: Change Laws, Production Law
- TRUST.md: Chain of command

---

*This document is a draft. Build does not start until Pieter approves.*
