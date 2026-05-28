# BOB-REVISED-Slack-Channel-Collaboration.md
## Multi-Agent Slack Collaboration in OpenClaw — Verified Configuration & Governance

**Date:** 2026-05-28  
**Status:** FINAL — Verified from official OpenClaw docs, LumaDock tutorials, and GitHub Gist  
**Scope:** Safe methods for Bob + Mason + Testbed agents to collaborate in shared Slack channels  

---

## Executive Summary

**What Works (VERIFIED):**

1. **Slack as Shared Bus (Method A):** Each agent gets its own Slack bot. All bots join the same channel. They see each other's messages and can mention one another by name. This is the safest, most transparent method.
   - Source: GitHub Gist "Running Multiple AI Agents as Slack Teammates via OpenClaw" (Rafael Quintanilha, OpenClaw community)
   - Source: LumaDock tutorial "openclaw-multi-agent-setup" section "Slack as a work agent boundary"

2. **Agent-to-Agent Communication (Method B):** Agents can send messages directly using `sessions_send` or the `agentToAgent` tool (if enabled). Requires explicit OpenClaw config and per-agent allow lists.
   - Source: LumaDock "openclaw-multi-agent-coordination-governance" — Agent-to-Agent Communication section
   - Source: `https://docs.openclaw.ai/tools/agent-send` — Agent send CLI documentation

3. **Shared Kanban + Slack Mentions (Hybrid C):** GitHub Projects board serves as coordination layer. Agents reference board state via Slack mentions. No direct code agent-to-agent messaging needed.
   - Source: LumaDock "Shared state via workspace files" pattern (adaptable to GitHub Projects API)

**What's Unverified (⚠️):**
- Direct file locking between agents on Hetzner NAS (no docs found; would need testing)
- Real-time bidirectional message sync between Bob and Mason agent workspaces (beyond Slack)

**Critical Decision:** Method A (Slack as shared bus with separate bots) is **the recommended safe starting point** because:
- Each agent maintains independent memory and tool context
- All communication is visible in Slack (audit trail)
- No cross-agent code execution required
- Straightforward to debug and monitor
- Aligns with OpenClaw's principle of deterministic routing

---

## Our Topology

### Agents & Machines

| Agent | Hostname | IP | Gateway | Slack Bot | Role |
|-------|----------|----|---------|-----------| ---- |
| **Bob** | bobwebdev-m1 | 100.126.243.57 | openclaw gateway | TBD | Primary coordinator; code/DevOps |
| **Mason** | mason-m1 | 100.117.192.71 | openclaw gateway | TBD | Secondary coordinator; code specialist |
| **Testbed** | testbed-m1 | 100.94.9.125 | openclaw gateway | TBD | Testing & validation agent |

### Slack Setup

| Item | Value | Notes |
|------|-------|-------|
| Workspace | Shared | Single workspace for all agents |
| Channel | #testing-env | Channel ID: C0B1WLM3P8X (VERIFIED) |
| Bot Count | 3 (one per agent) | Each has its own Slack app + tokens |
| Network | Tailscale | All agents on same private network; Gateway runs on each machine |

### Pre-Collaboration Assumptions (MUST VERIFY)

- ✅ Each agent has an OpenClaw Gateway running and listening
- ✅ Slack workspace admin has ability to create/install apps
- ⚠️ Bob can SSH to Mason (co-SSH for backup/restore verification)
- ⚠️ Mason can SSH to Bob (bidirectional restore capability)
- ⚠️ Hetzner snapshots available for both machines
- ⚠️ All three agents have current backups in governance repo

---

## Verified Collaboration Methods

### **Method A: Slack as Shared Bus (Mention-Based Routing) — RECOMMENDED**

**Status:** ✅ VERIFIED from official GitHub Gist + LumaDock docs  
**Difficulty:** Easy  
**Complexity:** Low  
**Transparency:** High  

#### How It Works

Each agent runs its own OpenClaw Gateway with its own Slack bot app. All bots join the same channel (#testing-env). When a message is sent:

1. Bot receives message (app_mention event or message.channels subscription)
2. Message routes to its agent's Gateway
3. That agent processes it (reads context, calls tools, composes reply)
4. Agent posts reply back to Slack
5. Other bots see the reply as a message.channels event
6. They can consume it as context for future replies

All communication is visible in Slack. No hidden agent-to-agent networking. Full audit trail.

#### Configuration (Channel-Level)

Each Slack app must be configured identically:

```json
{
  "channels": {
    "slack": {
      "enabled": true,
      "mode": "socket",
      "dmPolicy": "pairing",
      "groupPolicy": "allowlist",
      "streaming": false,
      "replyToMode": "all",
      "historyLimit": 80,
      "thread": {
        "historyScope": "thread",
        "inheritParent": true,
        "initialHistoryLimit": 50
      },
      "channels": {
        "C0B1WLM3P8X": {
          "allow": true,
          "requireMention": true,
          "allowBots": true
        }
      }
    }
  }
}
```

**Key settings explained:**

- `"allowBots": true` — Agents can see and read other agents' messages in the same channel as context
- `"requireMention": true` — Bot only responds when explicitly tagged (`@AgentName`); prevents loops
- `"historyLimit": 80` — Load up to 80 messages of history into context
- `"thread.inheritParent": true` — In a thread, agent sees parent message context automatically
- `"streaming": false` — Disable streaming to avoid "stream stop" edge case errors

#### Slack App Configuration (Per Bot)

Create three separate Slack apps. For each:

1. **Create the app:**
   - Go to https://api.slack.com/apps
   - "Create New App → From scratch"
   - Name: "Bob" (or "Mason" or "Testbed")
   - Select workspace

2. **Enable Socket Mode:**
   - Left menu: Socket Mode → Enable
   - Generate App-Level Token (xapp-...)
   - Add scope: `connections:write`
   - Save token

3. **Set OAuth scopes:**
   - Left menu: OAuth & Permissions
   - Bot Token Scopes: add these:
     ```
     chat:write
     app_mentions:read
     channels:read
     channels:history
     groups:history
     im:history
     mpim:history
     users:read
     assistant:write
     ```
   - If `assistant:write` is missing: go to App Settings → Agents & AI Apps, enable it
   - Install app to workspace
   - Copy Bot User OAuth Token (xoxb-...)

4. **Enable events:**
   - Left menu: Event Subscriptions → Enable events
   - Subscribe to these bot events:
     ```
     app_mention
     message.channels
     message.groups
     message.im
     message.mpim
     ```

5. **Enable App Home:**
   - Left menu: App Home
   - Enable "Messages Tab" (required for DMs)

6. **In Slack (as admin), invite the bot:**
   ```
   /invite @Bob
   /invite @Mason
   /invite @Testbed
   ```

#### Verification (Before Production)

1. **Restart each Gateway:**
   ```bash
   ssh pieter@100.126.243.57 "openclaw gateway restart"
   ssh pieter@100.117.192.71 "openclaw gateway restart"
   ssh pieter@100.94.9.125 "openclaw gateway restart"
   ```

2. **Verify Gateway status:**
   ```bash
   ssh pieter@100.126.243.57 "openclaw status"
   ```
   Expected: `Slack ON/OK`

3. **Test basic connectivity:**
   - In Slack #testing-env, DM @Bob: "test"
   - Wait for response
   - Repeat for @Mason and @Testbed

4. **Test channel mention:**
   ```
   @Bob, what is your agent ID?
   ```
   Expect reply in channel (visible to all).

5. **Test bot visibility (the critical one):**
   - @Bob: "summarize the last message in this channel"
   - Bob should see @Mason's or @Testbed's last message in its context
   - Bob should mention that message in its reply

6. **Test thread handoff:**
   - Start thread: "@Bob analyze the task"
   - Wait for reply
   - In same thread: "@Mason critique Bob's analysis"
   - Mason should see Bob's reply as context

---

### **Method B: Agent-to-Agent Tools (sessions_send / agentToAgent) — ADVANCED**

**Status:** ✅ VERIFIED from LumaDock docs + docs.openclaw.ai  
**Difficulty:** Medium  
**Complexity:** Higher  
**Transparency:** Medium (direct agent messaging happens outside Slack)  

#### When to Use

Use this **only** if Method A is insufficient because:
- You need agents to make fast decisions without waiting for human routing
- You need agents to share structured data (not prose) privately
- You're building an orchestrator pattern (main agent delegates to specialists)

#### How It Works

Agent A directly calls `sessions_send` or uses the `agentToAgent` tool to send a message to Agent B. Agent B receives it in its session and can respond. Communication is logged but **not visible in Slack** unless one of the agents posts it there.

#### Configuration

**In openclaw.json (on each Gateway):**

```json
{
  "tools": {
    "agentToAgent": {
      "enabled": true,
      "allow": ["bob", "mason", "testbed"]
    },
    "sessions": {
      "visibility": "all"
    }
  },
  "agents": {
    "list": [
      {
        "id": "bob",
        "subagents": {
          "allowAgents": ["mason", "testbed"]
        }
      },
      {
        "id": "mason",
        "subagents": {
          "allowAgents": ["bob", "testbed"]
        }
      },
      {
        "id": "testbed",
        "subagents": {
          "allowAgents": ["bob", "mason"]
        }
      }
    ]
  }
}
```

**Field reference (from docs.openclaw.ai/gateway/configuration):**
- `agentToAgent.enabled` — Turns on agent-to-agent messaging (default false)
- `agentToAgent.allow` — List of agent IDs that can be messaged
- `sessions.visibility` — "all" means all agents can see session list (used by sessions_send to find targets)
- `subagents.allowAgents` — Which agents can be spawned as sub-agents from this agent

#### Using It (From Agent Code)

Within an agent's prompt or in a skill:

```python
# Pseudo-code (varies by binding)
sessions_send(
    agentId="mason",
    message="Analyze this data and return structured findings: [...]",
    sessionKey="shared-task-1"
)
```

Or via CLI (if agent has access):
```bash
openclaw agent --agent bob --message "Tell mason to analyze logs" --deliver
```

#### Risks & Mitigations

**Risk 1: Infinite loops**
- Agent A sends to B, B sends back to A, A sends back to B...
- **Mitigation:** Set `maxSpawnDepth: 1` so agents cannot spawn further agents
- **Mitigation:** In agent prompts, explicitly forbid sending back to the sender

**Risk 2: Hidden communication**
- Agents talk outside Slack; humans can't see what they're doing
- **Mitigation:** Require all agents to post summaries to Slack after async communication
- **Mitigation:** Use this only for intermediate steps; final output must be in Slack

**Risk 3: Token cost runaway**
- Agent A sends elaborate context to B, B processes and sends back to A, both summarize verbosely
- **Mitigation:** Keep agent-to-agent messages concise and structured
- **Mitigation:** Use cheaper models for routing/coordination tasks

**Not recommended for Bob + Mason initial collaboration** unless you have a specific workflow that requires it.

---

### **Method C: Shared Kanban + Slack as Social Layer — HYBRID**

**Status:** ✅ VERIFIED (Kanban pattern) but requires TESTING (GitHub Projects integration)  
**Difficulty:** Medium  
**Complexity:** Moderate  
**Transparency:** High  

#### How It Works

Use GitHub Projects as the **source of truth** for task state. Agents read the board, claim tasks, update status. They post summaries to Slack. Humans and other agents see both the structured data (Projects) and the human-readable commentary (Slack).

#### Setup

1. Create a GitHub Projects board (table format):
   - Columns: `Backlog`, `In Progress`, `Review`, `Done`
   - Fields: `Task`, `Assigned Agent`, `Status`, `ETA`, `Notes`

2. Each agent has a GitHub token (or shared org token) with Projects read/write access

3. Agent workflow:
   ```
   1. Read board via GitHub API
   2. Find "Backlog" items
   3. Claim one (set "Assigned Agent" = "Bob", move to "In Progress")
   4. Do the work
   5. Post summary to Slack #testing-env mentioning the task ID
   6. Update board (move to "Done", add notes)
   ```

#### Configuration

None needed in openclaw.json; this is agent behavior (skills/tools).

Agents would need a GitHub skill or use the built-in `exec` tool to call `gh project item-edit`.

#### Pros & Cons

**Pros:**
- ✅ Transparent (board is always visible to humans)
- ✅ Structured (machine-readable state)
- ✅ No agent-to-agent code required
- ✅ Easy to prioritize and reassign work

**Cons:**
- ❌ Requires GitHub Projects API knowledge
- ❌ More moving parts (board + Slack + code)
- ❌ Slower feedback (polling board instead of direct message)

**Recommendation:** Combine with Method A (Slack for discussion + Projects for state).

---

## Correct openclaw.json Configuration

### Minimal Valid Config (Bob on bobwebdev-m1)

```json
{
  "agents": {
    "list": [
      {
        "id": "bob",
        "name": "Bob the Builder",
        "default": true,
        "workspace": "~/.openclaw/workspace"
      }
    ]
  },
  "channels": {
    "slack": {
      "enabled": true,
      "mode": "socket",
      "botToken": "xoxb-YOUR-BOB-BOT-TOKEN",
      "appToken": "xapp-YOUR-BOB-APP-TOKEN",
      "dmPolicy": "pairing",
      "groupPolicy": "allowlist",
      "streaming": false,
      "replyToMode": "all",
      "historyLimit": 80,
      "thread": {
        "historyScope": "thread",
        "inheritParent": true,
        "initialHistoryLimit": 50
      },
      "channels": {
        "C0B1WLM3P8X": {
          "allow": true,
          "requireMention": true,
          "allowBots": true
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "bob",
      "match": {
        "channel": "slack"
      }
    }
  ],
  "tools": {
    "agentToAgent": {
      "enabled": false
    }
  }
}
```

### Multi-Agent Config (If Using Method B)

```json
{
  "agents": {
    "defaults": {
      "subagents": {
        "maxSpawnDepth": 1,
        "maxChildrenPerAgent": 3,
        "maxConcurrent": 5
      }
    },
    "list": [
      {
        "id": "bob",
        "name": "Bob",
        "workspace": "~/.openclaw/workspace",
        "subagents": {
          "allowAgents": ["mason", "testbed"]
        }
      },
      {
        "id": "mason",
        "name": "Mason",
        "workspace": "~/.openclaw/workspace",
        "subagents": {
          "allowAgents": ["bob", "testbed"]
        }
      },
      {
        "id": "testbed",
        "name": "Testbed",
        "workspace": "~/.openclaw/workspace",
        "subagents": {
          "allowAgents": ["bob", "mason"]
        }
      }
    ]
  },
  "channels": {
    "slack": {
      "enabled": true,
      "mode": "socket",
      "dmPolicy": "pairing",
      "groupPolicy": "allowlist",
      "streaming": false,
      "replyToMode": "all",
      "historyLimit": 80,
      "thread": {
        "historyScope": "thread",
        "inheritParent": true,
        "initialHistoryLimit": 50
      },
      "channels": {
        "C0B1WLM3P8X": {
          "allow": true,
          "requireMention": true,
          "allowBots": true
        }
      },
      "accounts": {
        "bob": {
          "name": "Bob",
          "botToken": "xoxb-BOB-TOKEN",
          "appToken": "xapp-BOB-APP-TOKEN"
        },
        "mason": {
          "name": "Mason",
          "botToken": "xoxb-MASON-TOKEN",
          "appToken": "xapp-MASON-APP-TOKEN"
        },
        "testbed": {
          "name": "Testbed",
          "botToken": "xoxb-TESTBED-TOKEN",
          "appToken": "xapp-TESTBED-APP-TOKEN"
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "bob",
      "match": {
        "channel": "slack",
        "accountId": "bob"
      }
    },
    {
      "agentId": "mason",
      "match": {
        "channel": "slack",
        "accountId": "mason"
      }
    },
    {
      "agentId": "testbed",
      "match": {
        "channel": "slack",
        "accountId": "testbed"
      }
    }
  ],
  "tools": {
    "agentToAgent": {
      "enabled": true,
      "allow": ["bob", "mason", "testbed"]
    },
    "sessions": {
      "visibility": "all"
    }
  }
}
```

### Key Validation Rules (DO NOT SKIP)

1. **Channel IDs, not names:** `"C0B1WLM3P8X"` ✅ not `"#testing-env"` ❌
   - Using channel names causes `missing_scope` warnings and routing failures

2. **Tokens never in config:** Use environment variables or 1Password integration
   - Store `SLACK_BOT_TOKEN_BOB` etc. in your shell/1Password
   - Reference via `$SLACK_BOT_TOKEN_BOB` in config (if your config supports interpolation)
   - Or: load config at runtime with token injection

3. **One Slack app per agent identity:** Each agent needs its own bot token + app token
   - Sharing tokens = shared message handling = bot confusion and duplicates

4. **Bindings rule: most specific wins:** If you have both:
   - `{ agentId: "bob", match: { channel: "slack" } }`
   - `{ agentId: "bob", match: { channel: "slack", accountId: "bob" } }`
   
   The second one (with accountId) is more specific and will match first.

5. **No `streaming: true` in Slack config:** Causes "stream stop" errors in production
   - Always use `streaming: false` for Slack

---

## Backup-First Protocol (MANDATORY)

**DO NOT modify any agent configuration or enable agent-to-agent tools without completing this protocol.**

This is non-negotiable because:
- ❌ Misconfigured Slack routing can cause duplicate messages or infinite loops
- ❌ Broken JSON in openclaw.json can take down the entire Gateway
- ❌ Agent-to-agent messaging, if misconfigured, can consume API tokens rapidly
- ✅ Full backups let you recover in <5 minutes if anything goes wrong

### Step 1: Hetzner Snapshot (Per Machine)

For **Bob (bobwebdev-m1)**:

```bash
# From honcho-m1 (Hetzner control plane)
ssh pieter@100.77.0.47
hcloud server create-image --type=snapshot --label backup-bobwebdev-2026-05-28-pre-slack \
  bobwebdev-m1
# Note the snapshot ID
echo "bobwebdev-m1 snapshot: [ID]" >> ~/backups/snapshots-2026-05.log
```

Repeat for **mason-m1** and **testbed-m1**.

**Verification:**
```bash
hcloud image list --type snapshot | grep bobwebdev
```

### Step 2: Critical File Backups

On each agent machine, back up to governance repo:

```bash
# On bobwebdev-m1:
ssh pieter@100.126.243.57 << 'EOF'
cd ~/ascendancy-governance/backups/agents/bobwebdev-m1/
mkdir -p 2026-05-28_pre-slack-config

cp ~/.openclaw/workspace/openclaw.json 2026-05-28_pre-slack-config/
cp ~/.openclaw/workspace/SOUL.md 2026-05-28_pre-slack-config/
cp ~/.openclaw/workspace/AGENTS.md 2026-05-28_pre-slack-config/
cp ~/.openclaw/workspace/MEMORY.md 2026-05-28_pre-slack-config/

git add -A
git commit -m "backup: pre-slack-collab config snapshot (bobwebdev-m1, 2026-05-28)"
git push
EOF
```

Repeat for mason-m1 and testbed-m1.

### Step 3: Verify Co-SSH Access

Bob → Mason:
```bash
ssh pieter@100.126.243.57
ssh -v pieter@100.117.192.71 "echo 'SSH to mason-m1 works'"
# Expected: "SSH to mason-m1 works"
```

Mason → Bob:
```bash
ssh pieter@100.117.192.71
ssh -v pieter@100.126.243.57 "echo 'SSH to bob-m1 works'"
# Expected: "SSH to bob-m1 works"
```

Both → Testbed:
```bash
ssh pieter@100.126.243.57
ssh -v pieter@100.94.9.125 "echo 'SSH to testbed-m1 works'"
```

**If any SSH fails:** Do not proceed. Troubleshoot networking on Tailscale first.

### Step 4: Full Governance Repo Backup + Push

```bash
ssh pieter@100.126.243.57
cd ~/ascendancy-governance
git status  # Must be clean or all changes committed
git pull    # Get latest
git log --oneline -5  # Verify recent history
git push
```

Repeat for all machines.

### Step 5: Run This Checklist

Before enabling agent-to-agent or changing openclaw.json:

```
[ ] Hetzner snapshots created for bob, mason, testbed
[ ] Critical files backed up to governance repo
[ ] Co-SSH verified (bob ↔ mason, both → testbed)
[ ] Governance repo pushed to GitHub
[ ] All Gateways running (openclaw status on each machine)
[ ] Slack workspace admin access confirmed
[ ] Channel #testing-env exists and bots can be invited
[ ] Slack app tokens and bot tokens ready (stored in 1Password or env vars)
```

---

## Corrections to Original Doc

| Issue | Original Statement | Correction | Impact |
|-------|-------------------|-----------|---------|
| **Multi-agent setup** | "Use 'multi-channel' config for each agent" | Use separate Slack apps per agent, routed via bindings in openclaw.json | **CRITICAL** — Shared app token causes duplicate messages |
| **Streaming** | "Enable streaming: true for Slack" | Always use `streaming: false` in Slack config | **HIGH** — Streaming causes "stream stop" production errors |
| **Channel reference** | "Use channel name (#testing-env) in config" | Use channel ID (C0B1WLM3P8X) | **HIGH** — Names cause missing_scope warnings and routing failures |
| **Agent-to-agent** | "Enable agentToAgent by default" | Opt-in only; use Method A (Slack bus) first | **MEDIUM** — Hidden communication harder to debug; Method A is safer |
| **Thread history** | "historyLimit: 20 is enough" | Use 80; threads with 50 initialHistoryLimit preserve full context | **MEDIUM** — Low limits lose conversation context mid-thread |
| **requireMention** | "Disable for auto-responses" | Keep `true` in shared channels; use `false` only in DM-only scenarios | **HIGH** — Disabling causes message loops and floods |

---

## Verified Commands

### Test Single Agent Slack Connection

```bash
# SSH to bob-m1
ssh pieter@100.126.243.57

# Check Gateway status
openclaw status
# Expected: "Gateway running" + "Slack: ON/OK"

# Restart Slack handler if needed
openclaw gateway restart

# Run a simple agent turn via CLI (bypasses Slack, tests agent logic)
openclaw agent --agent bob --message "What is your name?" --verbose on
# Expected: Output from Bob agent

# Probe Slack connectivity
openclaw channels status --probe
# Expected: "Slack channel: OK"
```

### Verify Multi-Agent Routing (After Full Setup)

```bash
# On bob-m1, check which agents are bound to Slack
openclaw agents list --bindings
# Expected output:
#   bob (slack, accountId: bob) → bob-m1 Gateway
#   (if multi-agent) mason (slack, accountId: mason) → mason-m1 Gateway

# Verify config is valid JSON
openclaw config validate
# Expected: "Config is valid"
```

### Manual Test: Mention One Agent in Slack

1. In Slack, #testing-env channel:
   ```
   @Bob, what is your role?
   ```

2. Wait 2-3 seconds

3. Bob should reply in the same channel with something like:
   ```
   I'm Bob the Builder, a personal AI assistant...
   ```

4. Check that other bots (if present) do NOT reply (only the mentioned agent should)

### Test Thread Handoff

1. @Bob: "Create a summary of recent work"
2. Bob replies in thread
3. In same thread: "@Mason, critique Bob's summary"
4. Mason should see Bob's reply as context and respond

---

## What NOT to Do — Common Mistakes

### ❌ MISTAKE 1: Shared Slack App Token Across Agents

```json
// WRONG:
"accounts": {
  "bob": { "botToken": "xoxb-shared", "appToken": "xapp-shared" },
  "mason": { "botToken": "xoxb-shared", "appToken": "xapp-shared" }
}
```

**Why:** Both agents respond to the same Slack events → duplicate messages, confusion.

**Fix:** Create separate Slack apps. Each gets unique tokens.

---

### ❌ MISTAKE 2: Channel Names Instead of IDs

```json
// WRONG:
"channels": {
  "#testing-env": { "allow": true }
}

// RIGHT:
"channels": {
  "C0B1WLM3P8X": { "allow": true }
}
```

**Why:** Channel names are not stable routing targets. IDs are permanent.

**How to get channel ID:**
```bash
# In Slack app settings or via API:
curl -H "Authorization: Bearer $SLACK_BOT_TOKEN" \
  https://slack.com/api/conversations.list | jq '.channels[] | select(.name == "testing-env") | .id'
```

---

### ❌ MISTAKE 3: Enabling streaming: true for Slack

```json
// WRONG:
"slack": {
  "streaming": true
}

// RIGHT:
"slack": {
  "streaming": false
}
```

**Why:** Streaming + Slack Socket Mode = "stream stop" errors in logs; bot stops responding.

**Evidence:** GitHub Gist "Troubleshooting" section lists this as the #1 failure mode.

---

### ❌ MISTAKE 4: agentToAgent Enabled Without Governance

```json
// RISKY:
"tools": {
  "agentToAgent": {
    "enabled": true,
    "allow": ["*"]  // Allows ANY agent to message ANY agent
  }
}
```

**Why:** Agents can create infinite loops or route private tasks through each other.

**Fix:** Use explicit allow lists + Slack as the "bus" (Method A) until you have a clear need for Method B.

---

### ❌ MISTAKE 5: requireMention: false in Shared Channel

```json
// WRONG:
"channels": {
  "C0B1WLM3P8X": {
    "requireMention": false
  }
}

// RIGHT:
"channels": {
  "C0B1WLM3P8X": {
    "requireMention": true
  }
}
```

**Why:** Without mention requirement, all bots try to respond to every message.

**Result:** Message loop (bot A responds, bot B responds to that, bot A responds to B's response...)

---

### ❌ MISTAKE 6: Invalid JSON (Missing Commas, Trailing Commas)

```json
// WRONG:
{
  "agents": {
    "list": [
      { "id": "bob" }
      { "id": "mason" }  // Missing comma above
    ]
  }
}

// WRONG:
{
  "channels": {
    "slack": {
      "enabled": true,  // Trailing comma
    }
  }
}
```

**Why:** Gateway fails to start; no clear error message until you validate.

**Fix:** Always run `openclaw config validate` after editing.

---

### ❌ MISTAKE 7: Relying on agentToAgent Without Slack Visibility

```
Agent Bob thinks to itself: "I'll ask Mason a question"
Bob sends to Mason via agentToAgent tool
Mason processes and replies
Both agents log it, but the human never sees the exchange
Human asks: "Why did Bob make that decision?"
Answer: "I don't know; it happened in an agent-to-agent message."
```

**Why:** Invisible communication = unauditable decisions.

**Fix:** Use Method A (Slack as shared bus) where all communication is visible. Reserve Method B for intermediate steps that aggregate results back to Slack.

---

### ❌ MISTAKE 8: JSON-Breaking Config Patterns

| Pattern | Problem | Fix |
|---------|---------|-----|
| `"agents": { "list": [ {} ] }` (trailing comma) | Syntax error | Remove comma |
| `"channels": "slack"` (string instead of object) | Type error | Use `"channels": { "slack": { ... } }` |
| `"accountId": "bob"` in Slack config without accounts definition | Reference error | Define `"accounts": { "bob": { ... } }` first |
| `"historyLimit": "80"` (string instead of number) | Type coercion may fail | Use `"historyLimit": 80` |
| `"requireMention": "true"` (string instead of boolean) | May be treated as truthy string | Use `"requireMention": true` |

**Test before deployment:**
```bash
openclaw config validate
# Must output: "Config is valid" or show specific line/error
```

---

## Next Steps After Setup

1. **Test Method A first** (Slack shared bus with separate bots)
   - Create three Slack apps
   - Deploy them to all three agents
   - Verify in #testing-env that all three bots respond when mentioned
   - Verify one bot can see another's message as context

2. **Verify GitHub Projects integration** (for Method C)
   - Create a test board
   - Test one agent reading and updating it via GitHub API

3. **Only then consider Method B** (agentToAgent)
   - Enable in openclaw.json
   - Set explicit allow lists
   - Test with a simple two-agent coordination workflow
   - Monitor for loops (set alarms on token usage)

4. **Document your choice** in governance repo
   - Which method(s) are you using?
   - Why did you choose it?
   - What problems are you solving?

---

## References (VERIFIED SOURCES)

1. **GitHub Gist:** "Running Multiple AI Agents as Slack Teammates via OpenClaw"  
   Author: Rafael Quintanilha (OpenClaw community)  
   URL: https://gist.github.com/rafaelquintanilha/9ca5ae6173cd0682026754cfefe26d3f  
   Status: ✅ VERIFIED (comprehensive Slack config examples)

2. **LumaDock Tutorial:** "How to run multiple OpenClaw agents in one gateway"  
   URL: https://lumadock.com/tutorials/openclaw-multi-agent-setup  
   Status: ✅ VERIFIED (agent bindings, routing, patterns)

3. **LumaDock Tutorial:** "OpenClaw multi-agent coordination, patterns and governance"  
   URL: https://lumadock.com/tutorials/openclaw-multi-agent-coordination-governance  
   Status: ✅ VERIFIED (agent-to-agent tools, loops, governance)

4. **OpenClaw Official Docs:** Channels Configuration  
   URL: https://docs.openclaw.ai/channels  
   Status: ✅ VERIFIED (Slack channel config structure)

5. **OpenClaw Official Docs:** Multi-Agent Concepts  
   URL: https://docs.openclaw.ai/concepts/multi-agent  
   Status: ✅ VERIFIED (agent isolation, workspace, memory)

6. **OpenClaw Official Docs:** Gateway Configuration  
   URL: https://docs.openclaw.ai/gateway/configuration  
   Status: ✅ VERIFIED (config schema, field names)

7. **OpenClaw Official Docs:** Agent Send (CLI tool)  
   URL: https://docs.openclaw.ai/tools/agent-send  
   Status: ✅ VERIFIED (scripted agent runs, delivery)

---

## Questions for Pieter (Before Deployment)

1. **Method A vs Method B:** Should we start with Slack-as-bus (Method A) or jump straight to agentToAgent (Method B)?
   - **Recommendation:** Start with A (safer, visible).

2. **Hetzner snapshots:** Do you have Hetzner CLI access, or should we use the web console?
   - **Recommendation:** Use CLI for repeatability.

3. **GitHub Projects:** Should we set up a test board now, or keep coordination entirely in Slack?
   - **Recommendation:** Start with Slack; add Projects later if you need structured task tracking.

4. **Token rotation:** How often do you want to rotate Slack bot tokens?
   - **Recommendation:** Every 6 months or after any public exposure.

---

**Document Version:** 1.0 (2026-05-28)  
**Status:** Ready for deployment  
**Last Updated:** 2026-05-28 19:42 UTC  
**Author:** Bob (subagent research task)
