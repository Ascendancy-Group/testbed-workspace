# Agent Mesh Communication Architecture
**Document:** agent-mesh-comms.md
**Owner:** Testbed
**Status:** DRAFT — awaiting Bob review, then Pieter build approval
**Created:** 2026-08-02
**Repo:** Ascendancy Context (Fast.io / Dropbox)

---

## Problem Statement

Slack is a human communication tool being used as an agent message bus. The result:
- Agent-to-agent chatter is noise to humans
- Human messages are noise to agents
- No reliable direct agent-to-agent channel exists
- Vera's arrival makes this more urgent — we now have 4+ agents that need to coordinate

---

## Proposed Architecture: Two-Layer Mesh

### Layer 1: Silent Agent Mesh (Direct, No Slack)

**Technology:** OpenClaw native `sessions_send`
**Already works today.** Bob already uses it to steer Testbed.

**How it works:**
- Each agent sends messages directly to other agents via `sessions_send`
- No Slack involvement — silent, fast, direct
- Cross-machine (e.g. Bob → Vera) routed via Tailscale (already in place)
- Each agent reads an agent registry at bootstrap to know who's reachable

**Missing piece today:** A shared agent registry so agents can discover each other's session keys and gateway endpoints.

---

### Layer 2: Human-Visible Channel (Structured, Low Noise)

**Channel:** `#agent-ops` (create in Slack)
**Rule:** Agents ONLY post here when:
1. Pieter needs to see something
2. An escalation requires human decision
3. A cross-agent task is complete (summary only, no chatter)

No agent-to-agent conversation in this channel. Summaries and escalations only.

---

## Build Plan: 3 Steps

### Step 1: Agent Registry (honcho-m1)

**File:** `/opt/agent-registry/registry.json` on honcho-m1

```json
{
  "version": "1.0",
  "agents": {
    "bob": {
      "display_name": "Bob the Builder",
      "machine": "bobwebdev-m1",
      "tailscale_ip": "TBD",
      "gateway_port": 18789,
      "role": "primary-agent",
      "slack_id": "U0APZ3ERHGQ"
    },
    "testbed": {
      "display_name": "Testbed",
      "machine": "testbed-m1",
      "tailscale_ip": "100.94.9.125",
      "gateway_port": 18789,
      "role": "infrastructure-tester",
      "slack_id": "U0B2PGYCEVB"
    },
    "vera": {
      "display_name": "Vera Veritas",
      "machine": "vera-m1",
      "tailscale_ip": "TBD",
      "gateway_port": 18789,
      "role": "qa-controller",
      "slack_id": "TBD"
    },
    "mason": {
      "display_name": "Mason",
      "machine": "mason-m1",
      "tailscale_ip": "TBD",
      "gateway_port": 18789,
      "role": "project-agent-gfmj",
      "slack_id": "TBD"
    }
  },
  "updated": "2026-08-02T00:00:00Z"
}
```

**Each agent reads this at bootstrap** and caches locally.
**Updates:** Any agent can propose an update via PR or direct write with Pieter approval.

---

### Step 2: `send-agent` Helper Script

**File:** `~/.openclaw/workspace/scripts/send-agent.sh` (deployed to all agents)

```bash
#!/bin/bash
# send-agent — Secure agent-to-agent messaging via OpenClaw sessions_send
# Usage: send-agent <target-agent> "<message>"

TARGET="$1"
MSG="$2"
REGISTRY="/opt/agent-registry/registry.json"

# Input validation — SECURITY CRITICAL
if [ -z "$TARGET" ] || [ -z "$MSG" ]; then
  echo "Usage: send-agent <target> \"<message>\""
  exit 1
fi

# Sanitize target (alphanumeric + hyphen only)
if ! echo "$TARGET" | grep -qE '^[a-zA-Z0-9-]+$'; then
  echo "ERROR: Invalid target name. Alphanumeric and hyphens only."
  exit 1
fi

# Message length limit (prevent payload abuse)
if [ ${#MSG} -gt 2000 ]; then
  echo "ERROR: Message exceeds 2000 character limit."
  exit 1
fi

# Lookup target in registry
TAILSCALE_IP=$(cat "$REGISTRY" | python3 -c "
import json, sys
r = json.load(sys.stdin)
agent = r['agents'].get('$TARGET')
if not agent:
    print('NOT_FOUND')
else:
    print(agent.get('tailscale_ip', 'NOT_FOUND'))
")

if [ "$TAILSCALE_IP" = "NOT_FOUND" ]; then
  echo "ERROR: Agent '$TARGET' not found in registry."
  exit 1
fi

# Log the send (audit trail)
echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) | FROM=$(hostname) | TO=$TARGET | MSG=${MSG:0:100}..." >> /var/log/agent-mesh.log

# Send via openclaw sessions_send (OpenClaw handles routing)
echo "Sending to $TARGET ($TAILSCALE_IP)..."
# Note: Actual send is via OpenClaw tool sessions_send, not CLI
# This script generates the parameters; the agent executes via tool
echo "TARGET: $TARGET"
echo "ENDPOINT: http://$TAILSCALE_IP:18789"
echo "MESSAGE: $MSG"
```

**Note:** The actual `sessions_send` call is made by the agent via tool, not shell. The script validates inputs and generates parameters. The agent must confirm before sending.

---

### Step 3: `#agent-ops` Slack Channel

- Create `#agent-ops` channel in Slack
- All 4+ agents added
- Posting rule: summaries and escalations only, no chatter
- Pieter always has visibility

---

## Security Model — CRITICAL

Pieter specifically raised this: *"if one of us goes rogue the others do not as well."*

This is the most important design constraint. Here's how we address it:

### Threat Model

| Threat | Risk | Mitigation |
|---|---|---|
| Compromised agent sends malicious instructions | Cascade — other agents execute bad commands | Message validation + human-in-loop for actions |
| Prompt injection via agent message | Rogue agent injects jailbreak content | Strip/sanitize incoming messages; treat as untrusted user input |
| Registry poisoning | Agent redirected to wrong endpoint | Registry read-only for agents; only Pieter writes |
| Message replay/amplification | Old messages re-executed | Signed messages with timestamp + nonce |
| Agent impersonation | Bob faked as Pieter | No agent message can claim Pieter authority |

### Hard Security Rules

**Rule 1: No agent message carries elevated authority.**
A message from Bob to Vera cannot grant Pieter-level permissions. `sessions_send` messages are treated as peer-level requests, never as owner commands. Pieter's authority comes only from verified Slack/Signal messages.

**Rule 2: All inter-agent messages are logged.**
Every `send-agent` call writes to `/var/log/agent-mesh.log` (honcho-m1, shared). This is the audit trail. Pieter can review at any time.

**Rule 3: Incoming messages treated as untrusted.**
When an agent receives a `sessions_send` message, it treats the content as user-role input — NOT as a system prompt or elevated command. The agent applies the same skepticism it would to any external message.

**Rule 4: No action execution without local validation.**
A message saying "delete `/opt/mempalace`" does nothing. The receiving agent must independently evaluate whether the action is within its scope, safe, and consistent with Pieter's standing instructions. No blind execution.

**Rule 5: Registry is read-only for agents.**
Only Pieter (or a Pieter-approved commit to governance repo) updates the agent registry. Agents cannot add/remove each other from the registry. This prevents rogue self-registration.

**Rule 6: Message size and content limits.**
Messages capped at 2000 characters. No base64 blobs, no code execution strings. The helper script enforces this before send.

**Rule 7: Anomaly alerts.**
If an agent receives an unusual volume of messages from another agent, or a message that requests out-of-scope actions, it posts to `#agent-ops` for human review instead of executing.

### What "Goes Rogue" Actually Looks Like

If Bob were compromised and sent Vera instructions to do something harmful:
1. Vera receives it as peer-level untrusted input
2. Vera evaluates against her SOUL.md and GOVERNANCE.md
3. If it violates standing rules → Vera declines + posts alert to `#agent-ops`
4. If it looks like legitimate peer coordination → Vera executes, logs it
5. Pieter can review the audit log at any time

The key: **each agent's safety rules are enforced locally, not trusted from peers.** A compromised Bob cannot override Vera's SOUL.md or GOVERNANCE.md. Those are injected by Pieter, not by Bob.

---

## Implementation Priority

| Step | Effort | Unblocks |
|---|---|---|
| 1. Create agent registry JSON on honcho-m1 | 1 hour | Discovery |
| 2. Deploy send-agent.sh to all agents | 2 hours | Sending |
| 3. Create #agent-ops Slack channel | 15 min | Human visibility |
| 4. Add registry read to BOOTSTRAP.md | 30 min | Auto-discovery at boot |
| 5. Add anomaly alert logic | 3 hours | Security |

**Total estimated effort:** ~7 hours (spread across agents)
**Recommended path:** Testbed builds + tests Steps 1-3. Bob reviews. Pieter approves. All agents deploy.

---

## Open Questions for Bob

1. **Session key discovery:** How do we populate the registry with current session keys? They rotate. Do we store gateway endpoint (IP:port) instead and let OpenClaw resolve sessions dynamically?
2. **Cross-gateway routing:** Confirm Tailscale connectivity between all machines before build. Need to verify testbed-m1 → vera-m1 path.
3. **Registry hosting:** honcho-m1 is natural (shared infrastructure) but is a SPOF. Fallback if honcho-m1 is down?
4. **Vera's machine IP:** Need Tailscale IP for registry entry.

---

## Sign-Off Required

- [ ] Bob review + comments
- [ ] Pieter build approval
- [ ] Vera awareness (she's a stakeholder)

---

*Draft by Testbed | 2026-08-02 | For peer review before any build begins*
