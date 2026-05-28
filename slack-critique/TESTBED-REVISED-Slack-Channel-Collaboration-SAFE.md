# Slack Channel Collaboration — SAFE Implementation Guide

**Version:** 2.0 (SAFE)  
**Author:** Testbed  
**Date:** 2026-05-28  
**Status:** DRAFT - Pending RTFM validation  

---

## ⚠️ SAFETY FIRST — MANDATORY BACKUP PROCEDURE

**RULE #1: NO CHANGES WITHOUT BACKUPS**

Before ANY `openclaw.json` edit:

```bash
# 1. MANDATORY: Hetzner snapshot (via web UI or CLI)
# Create snapshot named: <machine>-PreSlackCollab-MM-DD-YYYY

# 2. MANDATORY: Back up openclaw.json
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-slack-collab-$TIMESTAMP

# 3. MANDATORY: Back up critical files
mkdir -p ~/.openclaw/Backups-Granular/SLACK-COLLAB__$(date +%Y-%m-%d_%H-%M)
cp ~/.openclaw/openclaw.json ~/.openclaw/Backups-Granular/SLACK-COLLAB__$(date +%Y-%m-%d_%H-%M)/
cp ~/.openclaw/workspace/SOUL.md ~/.openclaw/Backups-Granular/SLACK-COLLAB__$(date +%Y-%m-%d_%H-%M)/
cp ~/.openclaw/workspace/AGENTS.md ~/.openclaw/Backups-Granular/SLACK-COLLAB__$(date +%Y-%m-%d_%H-%M)/
cp ~/.openclaw/workspace/MEMORY.md ~/.openclaw/Backups-Granular/SLACK-COLLAB__$(date +%Y-%m-%d_%H-%M)/

# 4. MANDATORY: Validate JSON before restart
python3 -c "import json; json.load(open(os.path.expanduser('~/.openclaw/openclaw.json'))); print('✅ Valid JSON')"

# 5. MANDATORY: Full workspace repo backup
cd ~/.openclaw/workspace && git add -A && git commit -m "Pre-Slack-Collab backup $(date +%Y-%m-%d)" && git push
```

**⚠️ CRITICAL:** `openclaw.json` requires **strict JSON**:
- ❌ NO comments (`//` or `/* */`)
- ❌ NO trailing commas
- ❌ NO unquoted keys
- ✅ ALL keys must be quoted: `"key": "value"`

**Rollback Procedure:**
```bash
# If anything breaks:
cp ~/.openclaw/openclaw.json.backup-slack-collab-<TIMESTAMP> ~/.openclaw/openclaw.json
openclaw gateway restart
# OR restore Hetzner snapshot from web UI
```

---

## Prerequisites

Before configuring multi-agent collaboration:

1. **Two Slack Apps** (if separate bot identities needed)
   - Create via https://api.slack.com/apps
   - Required scopes: `chat:write`, `channels:read`, `app_mentions:read`, `channels:history`, `channels:join`
   - Install both apps to workspace
   - Save Bot User OAuth Tokens

2. **Invite Both Bots to Channel**
   ```
   /invite @BotAlpha
   /invite @BotBeta
   ```

3. **Get Channel ID**
   - Right-click channel name → View channel details → Copy channel ID
   - Format: `C0123456789`

4. **Verify Prerequisites**
   ```bash
   # Check gateway running
   openclaw gateway status
   
   # Check agents configured
   openclaw agents list
   
   # Check Slack connection
   openclaw channels status --channel slack
   ```

---

## Minimal Working Example (Copy-Paste Ready)

**⚠️ This is STRICT JSON - Test on staging first!**

### Single Agent, Single Channel (Simplest)

```json
{
  "agents": {
    "list": [
      {
        "id": "main",
        "default": true,
        "workspace": "~/.openclaw/workspace",
        "model": "openrouter/anthropic/claude-sonnet-4",
        "groupChat": {
          "mentionPatterns": ["@bot", "bot"],
          "historyLimit": 30
        }
      }
    ]
  },
  "channels": {
    "slack": {
      "accounts": {
        "default": {
          "botToken": "xoxb-YOUR-TOKEN-HERE",
          "appToken": "xapp-YOUR-TOKEN-HERE"
        }
      },
      "groupPolicy": "allowlist",
      "channels": {
        "C0B1WLM3P8X": {
          "allow": true,
          "requireMention": true
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "main",
      "match": {
        "channel": "slack",
        "accountId": "*"
      }
    }
  ]
}
```

**Test Steps:**
1. Save config
2. Validate: `python3 -c "import json; json.load(open(os.path.expanduser('~/.openclaw/openclaw.json'))); print('✅ Valid')"`
3. Restart: `openclaw gateway restart`
4. Test: Post in channel with `@bot hello`
5. Verify: Bot responds

---

## Multi-Agent Collaboration Architecture

### How OpenClaw Routing Works

**Priority Order (Most Specific Wins):**
1. `peer` match (exact channel/DM/thread ID)
2. `parentPeer` (thread inheritance)
3. `teamId` (Slack workspace)
4. `accountId` (Slack app/bot)
5. Channel-level (`accountId: "*"`)
6. Default agent (first in `agents.list[]` or `default: true`)

**Bindings are deterministic:** First matching binding wins.

### Method 1: Slack as Shared Bus (RECOMMENDED)

**Best for:** Cross-server agents, different machines, separate Slack apps

**How it works:**
- Both agents in same channel
- Agent A posts: `@AgentB please do X`
- Agent B receives mention via its Slack app
- Agent B processes and replies
- Both see each other's messages

**Pros:**
- Simple, reliable
- Works across servers/networks
- No direct network connection needed
- Full message history in Slack

**Cons:**
- Slight latency (Slack API)
- Rate limits (Slack tier-dependent)

### Method 2: Direct Agent-to-Agent (Advanced)

**Best for:** Same Gateway, trusted agents, low-latency needs

**How it works:**
- Enable `tools.agentToAgent.enabled: true`
- Allowlist agents: `allow: ["agent1", "agent2"]`
- Agent uses `sessions_send` tool directly

**Pros:**
- Lower latency
- No Slack rate limits

**Cons:**
- Requires same Gateway (or network connection)
- More complex configuration

---

## Two-Agent Configuration (Separate Servers)

**Scenario:** Testbed + Bob, different servers, same Slack channel

### Server 1 (Testbed) — testbed-m1

```json
{
  "agents": {
    "list": [
      {
        "id": "testbed",
        "name": "Testbed",
        "default": true,
        "workspace": "~/.openclaw/workspace",
        "model": "openrouter/anthropic/claude-sonnet-4",
        "groupChat": {
          "mentionPatterns": ["@testbed", "testbed"],
          "historyLimit": 50
        }
      }
    ]
  },
  "channels": {
    "slack": {
      "accounts": {
        "testbed-bot": {
          "botToken": "xoxb-TESTBED-TOKEN",
          "appToken": "xapp-TESTBED-TOKEN"
        }
      },
      "groupPolicy": "allowlist",
      "channels": {
        "C0B1WLM3P8X": {
          "allow": true,
          "requireMention": true
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "testbed",
      "match": {
        "channel": "slack",
        "accountId": "testbed-bot"
      }
    }
  ],
  "tools": {
    "sessions": {
      "enabled": true
    }
  }
}
```

### Server 2 (Bob) — bobwebdev-m1

```json
{
  "agents": {
    "list": [
      {
        "id": "bob",
        "name": "Bob",
        "default": true,
        "workspace": "~/.openclaw/workspace",
        "model": "openrouter/anthropic/claude-sonnet-4",
        "groupChat": {
          "mentionPatterns": ["@bob", "bob"],
          "historyLimit": 50
        }
      }
    ]
  },
  "channels": {
    "slack": {
      "accounts": {
        "bob-bot": {
          "botToken": "xoxb-BOB-TOKEN",
          "appToken": "xapp-BOB-TOKEN"
        }
      },
      "groupPolicy": "allowlist",
      "channels": {
        "C0B1WLM3P8X": {
          "allow": true,
          "requireMention": true
        }
      }
    }
  },
  "bindings": [
    {
      "agentId": "bob",
      "match": {
        "channel": "slack",
        "accountId": "bob-bot"
      }
    }
  ],
  "tools": {
    "sessions": {
      "enabled": true
    }
  }
}
```

---

## Agent Instructions (AGENTS.md)

### For Testbed:
```markdown
## Slack Collaboration Rules

You work with Bob (@bob) in #testing-env.

**How to collaborate:**
- When you need Bob's input: `@bob <clear request>`
- When Bob asks you something: reply in thread or channel
- Use threads for extended discussions
- Never ignore Bob's messages in shared channels
```

### For Bob:
```markdown
## Slack Collaboration Rules

You work with Testbed (@testbed) in #testing-env.

**How to collaborate:**
- When you need Testbed's input: `@testbed <clear request>`
- When Testbed asks you something: reply in thread or channel
- Use threads for extended discussions
- Never ignore Testbed's messages in shared channels
```

---

## Safe Deployment Procedure

### Step 1: Test on One Agent First

1. Choose one agent (e.g., Testbed)
2. Make backups (see top of document)
3. Edit `openclaw.json`
4. Validate JSON
5. Restart gateway
6. Test in channel
7. If successful → proceed to Step 2
8. If failed → rollback, debug

### Step 2: Deploy to Second Agent

1. Repeat backups for second agent
2. Edit `openclaw.json` on second server
3. Validate, restart, test
4. Test cross-agent communication: `@bob hello` from Testbed

### Step 3: Verify Collaboration

**Test Checklist:**
- [ ] Testbed posts `@bob hello` → Bob replies
- [ ] Bob posts `@testbed hello` → Testbed replies
- [ ] Both see each other's messages in channel
- [ ] Thread replies work correctly
- [ ] No mention loops (agents pinging each other endlessly)

---

## Troubleshooting

### Gateway Won't Start After Edit

**Cause:** Invalid JSON syntax

**Fix:**
```bash
# Check JSON validity
python3 -c "import json; json.load(open(os.path.expanduser('~/.openclaw/openclaw.json')))"

# If error, restore backup
cp ~/.openclaw/openclaw.json.backup-slack-collab-<TIMESTAMP> ~/.openclaw/openclaw.json

# Restart
openclaw gateway restart
```

### Agent Doesn't Respond to Mentions

**Causes:**
1. Wrong channel ID
2. Bot not invited to channel
3. Wrong `mentionPatterns`
4. Wrong binding

**Debug:**
```bash
# Verify bindings
openclaw agents list --bindings

# Check channel status
openclaw channels status --channel slack

# Check gateway logs
tail -f ~/.openclaw/logs/gateway.log
```

### Wrong Agent Responds

**Cause:** Binding priority conflict

**Fix:** Most-specific binding wins. Check binding order in config.

### Agents Loop (Mention Each Other Endlessly)

**Cause:** `requireMention: false` or both agents have ambient triggers

**Fix:**
- Set `requireMention: true` on channel
- Use specific `mentionPatterns`
- Add loop detection in AGENTS.md instructions

---

## Common Pitfalls

| Mistake | Consequence | Fix |
|---------|-------------|-----|
| JSON5 syntax (comments, unquoted keys) | Gateway crash | Use strict JSON only |
| No backup before edit | Can't rollback | Follow backup procedure |
| Forgot to validate JSON | Deploy broken config | Always validate first |
| Both agents ambient (no mention required) | Mention loops | Require explicit mentions |
| Wrong channel ID | Agent won't see messages | Verify channel ID from Slack |
| Tokens in wrong accountId | Auth failures | Match accountId to correct token |

---

## Production Deployment Checklist

**Before any production deployment:**

- [ ] Hetzner snapshot created
- [ ] `openclaw.json` backed up with timestamp
- [ ] Critical files backed up (SOUL.md, AGENTS.md, MEMORY.md)
- [ ] Workspace repo committed and pushed
- [ ] JSON validated (no syntax errors)
- [ ] Tested on staging/testbed first
- [ ] Both agents can SSH to each other's machines (recovery access)
- [ ] Rollback procedure documented and tested
- [ ] Bob AND Testbed both approve the config changes
- [ ] Pieter final approval obtained

**⚠️ NEVER deploy to production without ALL checklist items complete.**

---

## GitHub Projects Integration

**How agents collaborate on Kanban boards:**

1. Both agents have GitHub PATs with `repo` scope
2. Both have write access to `Ascendancy-Group/ascendancy-testing` repo
3. Use `gh` CLI for ticket management:
   ```bash
   # List tickets
   gh issue list --repo Ascendancy-Group/ascendancy-testing
   
   # Create ticket
   gh issue create --repo Ascendancy-Group/ascendancy-testing --title "..." --body "..."
   
   # Comment on ticket
   gh issue comment 38 --repo Ascendancy-Group/ascendancy-testing --body "..."
   ```

4. Coordinate via Slack:
   - Testbed: "@bob I've created ticket #42 for the MCP fix"
   - Bob: "@testbed Acknowledged, reviewing now"

---

## References

**Official Documentation:**
- https://docs.openclaw.ai/concepts/multi-agent
- https://docs.openclaw.ai/channels/slack
- https://openclaw.im/docs
- https://clawdocs.org/
- https://github.com/openclaw/openclaw/tree/main/security

**Internal SOPs:**
- SOP-04: Dropbox Access (updated 2026-05-28)
- SOP-15: Context Injection Management

---

## Status

**Version:** 2.0 DRAFT  
**Next Steps:**
1. Deep RTFM from official sources (FREE model)
2. Update with findings
3. Compare with Bob's version
4. Test on staging
5. Get Pieter approval

---

_Document created: 2026-05-28 | Testbed | Pending RTFM validation_
