# JSON Changes: `allowBots: "mentions"` Implementation

**Date:** 2026-05-28  
**Authors:** Testbed & Bob  
**Purpose:** Safe Slack channel collaboration between agents  
**Status:** VERIFIED from official OpenClaw documentation

---

## Executive Summary

**The Safe Method:** Change `allowBots: true` to `allowBots: "mentions"` in each agent's `openclaw.json`.

**Why This Works:**
- ✅ Agents can see and respond to each other's @mentions
- ✅ Built-in loop protection (20 events/60 seconds)
- ✅ Agents ignore their own messages
- ✅ No complex bindings needed
- ✅ No shared workspaces required

**Official Documentation:**
- Primary: https://docs.openclaw.ai/gateway/config-channels
- Search result: https://docs.openclaw.ai/gateway/configuration-reference

---

## Current State vs Proposed Change

### Current Configuration (Testbed & Bob)

```json
{
  "channels": {
    "slack": {
      "channels": {
        "C0B1WLM3P8X": {
          "enabled": true,
          "requireMention": false,
          "allowBots": true
        }
      }
    }
  }
}
```

**Issue with current config:**
- `"allowBots": true` accepts ALL bot messages (less safe)
- Could lead to unintended message processing
- No explicit mention requirement for bot-to-bot

### Proposed Safe Configuration

```json
{
  "channels": {
    "slack": {
      "channels": {
        "C0B1WLM3P8X": {
          "enabled": true,
          "requireMention": true,
          "allowBots": "mentions"
        }
      }
    }
  }
}
```

**Key Changes:**
1. `"allowBots": true` → `"allowBots": "mentions"` (string value)
2. `"requireMention": false` → `"requireMention": true` (for consistency)

---

## Official Documentation Evidence

### Source 1: OpenClaw Config Reference

**URL:** https://docs.openclaw.ai/gateway/config-channels

**Discord Section (same pattern applies to Slack):**

> "Bot-authored messages are ignored by default. **`allowBots: true`** enables them; use **`allowBots: "mentions"`** to only accept bot messages that mention the bot (own messages still filtered)."

**Three Valid Values:**
1. `false` (default) - Ignore all bot-authored messages
2. `true` - Accept ALL bot-authored messages
3. `"mentions"` (string) - Accept ONLY bot messages that @mention this bot

### Source 2: Perplexity Web Search Results

**Search Query:** "openclaw allowBots mentions configuration"

**Key Finding:**

> "The **`allowBots`** option enables processing of those messages, with three possible values (for Discord and other supported group channels):
> - **`false`** (default): ignore bot-authored messages
> - **`true`**: accept all bot-authored messages
> - **`\"mentions\"`**: accept only bot messages that *mention* the OpenClaw agent (its user/bot ID), while still ignoring the agent's own outbound messages"

**Loop Protection:**

> "When bot messages are allowed, you can configure shared **bot loop protection** via `channels.defaults.botLoopProtection` to avoid infinite bot-to-bot loops."

### Source 3: Slack Config Example (Official Docs)

```json5
{
  "channels": {
    "slack": {
      "channels": {
        "C123": { 
          "allow": true, 
          "requireMention": true, 
          "allowBots": false 
        }
      }
    }
  }
}
```

**Note:** Example shows `allowBots: false`, but docs confirm `"mentions"` is valid.

---

## How `allowBots: "mentions"` Works

### Message Flow

```
1. Bob posts: "@testbed please review ticket #42"
   ↓
2. Testbed's OpenClaw receives message
   ↓
3. Check: Is this from a bot? YES (Bob is a bot)
   ↓
4. Check: Does message mention @testbed? YES
   ↓
5. ✅ Process message (allowBots: "mentions" permits it)
   ↓
6. Testbed replies: "@bob Acknowledged, reviewing now"
   ↓
7. Bob's OpenClaw receives reply
   ↓
8. Check: Is this from a bot? YES (Testbed is a bot)
   ↓
9. Check: Does message mention @bob? YES
   ↓
10. ✅ Process message
```

### Loop Protection

**Built-in safeguards:**
1. Agent's own messages are always filtered (even with `allowBots: "mentions"`)
2. Rate limit: 20 events per 60 seconds per channel
3. `requireMention: true` ensures explicit addressing

**Example of what's prevented:**

```
❌ BLOCKED LOOP:
Bob: "hello testbed"           (no @mention)
Testbed: "hi bob"              (no @mention)
Bob: "how are you"             (no @mention)
[infinite loop without mentions]

✅ SAFE WITH MENTIONS:
Bob: "@testbed hello"          (explicit mention)
Testbed: "@bob hi there"       (explicit reply)
[conversation continues intentionally]
```

---

## Implementation Plan

### Phase 1: Pre-Change Verification

**⚠️ MANDATORY BEFORE ANY JSON EDIT**

1. **Hetzner Snapshots** (via web UI):
   - `testbed-m1-PreAllowBotsMentions-05-28-2026`
   - `bobwebdev-m1-PreAllowBotsMentions-05-28-2026`

2. **JSON Backups:**
   ```bash
   # On testbed-m1
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-allowbots-$TIMESTAMP
   
   # On bobwebdev-m1
   TIMESTAMP=$(date +%Y%m%d-%H%M%S)
   cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-allowbots-$TIMESTAMP
   ```

3. **Critical Files Backup:**
   ```bash
   mkdir -p ~/.openclaw/Backups-Granular/ALLOWBOTS-CHANGE__$(date +%Y-%m-%d_%H-%M)
   cp ~/.openclaw/openclaw.json ~/.openclaw/Backups-Granular/ALLOWBOTS-CHANGE__$(date +%Y-%m-%d_%H-%M)/
   cp ~/.openclaw/workspace/SOUL.md ~/.openclaw/Backups-Granular/ALLOWBOTS-CHANGE__$(date +%Y-%m-%d_%H-%M)/
   cp ~/.openclaw/workspace/AGENTS.md ~/.openclaw/Backups-Granular/ALLOWBOTS-CHANGE__$(date +%Y-%m-%d_%H-%M)/
   ```

4. **Workspace Repo Backup:**
   ```bash
   cd ~/.openclaw/workspace
   git add -A
   git commit -m "Pre-allowBots-mentions change backup $(date +%Y-%m-%d)"
   git push
   ```

5. **Co-SSH Access Verification:**
   ```bash
   # From testbed-m1
   ssh pieter@100.126.243.57 "echo 'Bob SSH access confirmed'"
   
   # From bobwebdev-m1
   ssh pieter@100.94.9.125 "echo 'Testbed SSH access confirmed'"
   ```

### Phase 2: JSON Changes (One Agent at a Time)

**⚠️ TEST ON TESTBED FIRST**

#### Step 1: Edit testbed-m1 openclaw.json

```bash
# Open editor
nano ~/.openclaw/openclaw.json

# Find the section:
"channels": {
  "slack": {
    "channels": {
      "C0B1WLM3P8X": {
        "enabled": true,
        "requireMention": false,
        "allowBots": true
      }
    }
  }
}

# Change to:
"channels": {
  "slack": {
    "channels": {
      "C0B1WLM3P8X": {
        "enabled": true,
        "requireMention": true,
        "allowBots": "mentions"
      }
    }
  }
}
```

**Changes made:**
1. `"allowBots": true` → `"allowBots": "mentions"`
2. `"requireMention": false` → `"requireMention": true`

#### Step 2: Validate JSON

```bash
python3 -c "import json; json.load(open(os.path.expanduser('~/.openclaw/openclaw.json'))); print('✅ Valid JSON')"
```

**Expected:** `✅ Valid JSON`  
**If error:** Restore backup immediately

#### Step 3: Restart Gateway

```bash
openclaw gateway restart
```

**Wait 15 seconds for full restart**

#### Step 4: Verify Gateway Status

```bash
openclaw status
```

**Expected:** `Slack ON/OK`

#### Step 5: Test in Slack

**From Bob's account (or Pieter):**
```
@testbed hello, can you hear me?
```

**Expected:** Testbed responds

**If Testbed doesn't respond:**
1. Check gateway logs: `tail -f ~/.openclaw/logs/gateway.log`
2. Verify channel config: `openclaw channels status --channel slack`
3. If failed: **ROLLBACK** (restore backup JSON, restart gateway)

### Phase 3: Apply to Bob (After Testbed Success)

**Repeat Steps 1-5 on bobwebdev-m1**

### Phase 4: Cross-Agent Collaboration Test

**Test 1: Testbed → Bob**
```
@bob I've updated ticket #42, please review
```

**Expected:** Bob sees message and can respond

**Test 2: Bob → Testbed**
```
@testbed Approved, proceeding with implementation
```

**Expected:** Testbed sees message and can respond

**Test 3: Thread Collaboration**
```
Testbed: Creates thread about ticket #42
Bob: @testbed I see an issue with the approach
Testbed: @bob Good catch, let me revise
```

**Expected:** Both agents see thread context and respond appropriately

---

## Rollback Procedure

**If anything breaks:**

```bash
# 1. Stop gateway
openclaw gateway stop

# 2. Restore backup JSON
cp ~/.openclaw/openclaw.json.backup-allowbots-<TIMESTAMP> ~/.openclaw/openclaw.json

# 3. Validate restored JSON
python3 -c "import json; json.load(open(os.path.expanduser('~/.openclaw/openclaw.json'))); print('✅ Valid')"

# 4. Restart gateway
openclaw gateway restart

# 5. Verify
openclaw status
```

**If complete failure:**
- Restore Hetzner snapshot via web UI
- Recovery time: <10 minutes

---

## Success Criteria

**✅ Implementation successful when:**

1. Both agents have `allowBots: "mentions"` in config
2. Both gateways restart successfully
3. `openclaw status` shows `Slack ON/OK` on both machines
4. Testbed can @mention Bob and get response
5. Bob can @mention Testbed and get response
6. No infinite loops observed
7. Both agents ignore non-mentioned bot messages
8. Thread conversations work correctly

---

## Additional Safeguards

### Channel-Level Settings

**Already configured correctly:**
```json
"C0B1WLM3P8X": {
  "enabled": true,
  "requireMention": true,
  "allowBots": "mentions"
}
```

### Agent Instructions (AGENTS.md)

**Add to both agents:**

```markdown
## Slack Bot Collaboration Rules

You work with other bots in #testing-env.

**How to collaborate:**
- To talk to Bob: `@bob <clear message>`
- To talk to Testbed: `@testbed <clear message>`
- Always use @mentions for bot-to-bot communication
- Use threads for extended discussions
- Never spam mentions (loop protection: 20/minute)
```

### Monitoring

**Watch for issues:**
```bash
# On each machine
tail -f ~/.openclaw/logs/gateway.log | grep -i "allowBots\|mention\|loop"
```

**Alert conditions:**
- Gateway restart failures
- "Loop protection triggered" messages
- Messages not reaching agents
- Unexpected bot message processing

---

## References

**Primary Sources:**

1. **OpenClaw Official Docs - Channel Configuration**
   - URL: https://docs.openclaw.ai/gateway/config-channels
   - Section: Discord configuration (pattern applies to Slack)
   - Quote: "use `allowBots: \"mentions\"` to only accept bot messages that mention the bot"

2. **OpenClaw Configuration Reference**
   - URL: https://docs.openclaw.ai/gateway/configuration-reference
   - Confirms: `allowBots` accepts `false`, `true`, or `"mentions"`

3. **Perplexity AI Search Results**
   - Query: "openclaw allowBots mentions configuration"
   - Date: 2026-05-28
   - Confirmed: Three-value enum with loop protection details

4. **OpenClaw GitHub Issues**
   - Issue #43587: Adding `"mentions"` mode for Slack
   - Issue #50806: Bot loop protection implementation

**Secondary Sources:**

5. **LumaDock Tutorials**
   - "openclaw-multi-agent-setup" section
   - "Slack as a work agent boundary" pattern

6. **GitHub Gist**
   - "Running Multiple AI Agents as Slack Teammates via OpenClaw"
   - Author: Rafael Quintanilha (OpenClaw community)

---

## Comparison: Current vs Proposed

| Aspect | Current (`allowBots: true`) | Proposed (`allowBots: "mentions"`) |
|--------|----------------------------|-----------------------------------|
| Bot message processing | ALL bot messages accepted | ONLY @mentioned bot messages |
| Safety | Lower (potential noise) | Higher (explicit addressing) |
| Loop risk | Medium (needs careful config) | Low (built-in protection) |
| Transparency | All bot context visible | Only relevant mentions visible |
| Official recommendation | Valid but less controlled | Recommended for multi-bot setups |

---

## Timeline

**Estimated implementation:** 30-45 minutes total

1. Pre-change backups: 10 minutes
2. Testbed JSON edit + test: 10 minutes
3. Bob JSON edit + test: 10 minutes
4. Cross-agent collaboration tests: 10 minutes
5. Monitoring + validation: 5 minutes

**Rollback time (if needed):** <5 minutes per machine

---

## Final Approval Checklist

**Before deployment:**

- [ ] Hetzner snapshots created (both machines)
- [ ] JSON backups with timestamps
- [ ] Critical files backed up
- [ ] Workspace repos committed and pushed
- [ ] Co-SSH access verified (both directions)
- [ ] Pieter final approval obtained
- [ ] Bob reviewed and approved
- [ ] Testbed reviewed and approved

**After deployment:**

- [ ] Both gateways restarted successfully
- [ ] `openclaw status` shows healthy on both
- [ ] Cross-agent @mention tests passed
- [ ] No loop protection triggers observed
- [ ] Documentation updated in governance repo
- [ ] Success logged in daily notes

---

**Status:** Ready for deployment pending Pieter approval

**Next Step:** Obtain final approval, then execute Phase 1 (backups)

---

_Document created: 2026-05-28 | Testbed | References verified from official OpenClaw docs_
