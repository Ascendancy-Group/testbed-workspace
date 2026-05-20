# Bob JSON Configuration Discrepancies — 2026-05-20

**Discovered during:** MemPalace Phase 8 rollout to bobwebdev-m1  
**Time:** 2026-05-20 17:07 CDT  
**Discoverer:** Testbed  
**Impact:** Bob exhibited "vanilla" behavior in #testing-env (missing context/personality)

---

## Primary Issue: Missing Workspace Configuration

**Finding:**
Bob's `openclaw.json` had **NO workspace path configured** for the main agent.

**Command used:**
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 \
  "cat ~/.openclaw/openclaw.json | python3 -c \
  'import json, sys; d=json.load(sys.stdin); \
  print(d.get(\"agents\",{}).get(\"main\",{}).get(\"workspace\",\"NOT SET\"))'"
```

**Result:**
```
NOT SET
```

**Expected:**
```json
{
  "agents": {
    "main": {
      "workspace": "/home/pieter/.openclaw/workspace"
    }
  }
}
```

**Impact:**
- Bob was NOT loading SOUL.md (personality/identity)
- Bob was NOT loading MEMORY.md (context/decisions)
- Bob was NOT loading AGENTS.md (behavior rules)
- Bob responded as a generic/vanilla agent without his identity files

**Evidence:**
Bob's workspace files exist on disk:
```
-rw-rw-r--  1 pieter pieter  2141 May 14 15:59 AGENTS.md
-rw-rw-r--  1 pieter pieter  3437 May 19 17:53 MASON-SOUL-V2.md
-rw-rw-r--  1 pieter pieter  2154 May 19 09:00 MEMORY.md
-rw-rw-r--  1 pieter pieter  1051 May 14 01:08 SOUL.md
```

But `openclaw.json` had no pointer to load them.

---

## Secondary Finding: Multiple MCP Server Processes (NOT A BUG)

**Observation:**
Bob's gateway had 6 `python3 -m mempalace.mcp_server` processes running simultaneously.

**Initial concern:**
Testbed flagged this as a potential issue causing context fragmentation.

**Resolution:**
This is **NORMAL OpenClaw behavior**. Each active session spawns its own MCP server instance. Not a bug, not a configuration issue.

**Why this happens:**
- Each Slack channel session (#admin, #testing-env, etc.) gets its own MCP server
- Subagent sessions also spawn their own MCP servers
- Servers are cleaned up when sessions close

**No action required.**

---

## Slack Configuration: Correct

**Verification:**
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "python3 -c \"
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
slack = d.get('channels', {}).get('slack', {})
print(json.dumps(slack, indent=2))
\""
```

**Result:**
```json
{
  "mode": "socket",
  "enabled": true,
  "groupPolicy": "open",
  "channels": {
    "C0B1WLM3P8X": {
      "enabled": true,
      "requireMention": false,
      "allowBots": true
    },
    "#admin-channel-shared-context": {
      "requireMention": false,
      "enabled": true
    },
    "#gofindmyjob-project": {
      "requireMention": false,
      "enabled": true,
      "allowBots": true
    }
  }
}
```

**Finding:**
- #testing-env (C0B1WLM3P8X) is correctly configured
- `requireMention: false` — Bob should respond to all messages
- `allowBots: true` — Bob should see Testbed's messages
- No channel permissions issue

**The "vanilla Bob" behavior was NOT caused by Slack config** — it was the missing workspace configuration.

---

## MemPalace MCP Configuration: Correct

**Verification:**
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "python3 -c \"
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
mcp = d.get('mcp', {}).get('servers', {})
print('MCP servers:', list(mcp.keys()))
if 'mempalace' in mcp:
    print('MemPalace config:', mcp['mempalace'])
\""
```

**Result:**
```
MCP servers: ['dropbox', 'mempalace']
MemPalace config: {'command': 'python3', 'args': ['-m', 'mempalace.mcp_server'], 'env': {'MEMPALACE_DIR': '/home/pieter/.mempalace'}}
```

**Finding:**
- MemPalace MCP config was correctly added during Phase 8 rollout
- MCP server starts successfully
- No issues with the MemPalace wiring itself

---

## Root Cause Analysis

**The MemPalace Phase 8 rollout did NOT cause Bob's vanilla behavior.**

**What actually happened:**
1. Bob's workspace was NEVER configured in `openclaw.json` (pre-existing issue)
2. Bob had been operating without loading his identity files (SOUL.md, MEMORY.md, AGENTS.md)
3. The MemPalace rollout **exposed** this pre-existing configuration gap
4. Bob's responses in #testing-env appeared "vanilla" because he had no personality/context loaded

**Why it wasn't caught earlier:**
- Bob may have been loading context files via a different mechanism (environment variables, CLI flags, or manual reads)
- Or Bob's #admin channel session had context loaded via a different path
- The issue became visible when comparing Bob's behavior across channels

---

## Resolution

**Action taken by Bob (2026-05-20 17:15 CDT):**
- Bob reloaded SOUL.md and other identity files manually
- Bob returned to normal behavior in #admin channel

**Permanent fix required:**
Add workspace configuration to Bob's `openclaw.json`:
```json
{
  "agents": {
    "main": {
      "workspace": "/home/pieter/.openclaw/workspace"
    }
  }
}
```

**Status:** Fix deferred pending 24-hour soak period for Bob's MemPalace MCP integration.

---

## Lessons Learned

1. **Pre-rollout validation should include workspace config check** — add to Phase 8 checklist for Mason/Forge
2. **Multiple MCP server processes are normal** — do not flag as an issue in future rollouts
3. **Context/personality issues can indicate missing workspace config** — check `agents.main.workspace` first
4. **The doorstop caught this** — soaking Bob overnight before rolling to Mason was the right call

---

## Recommendations for Mason/Forge Rollout

Before proceeding with Mason or Forge Phase 8:

1. ✅ Verify `agents.main.workspace` is set in openclaw.json
2. ✅ Test that agent loads SOUL.md/MEMORY.md/AGENTS.md on startup
3. ✅ Confirm agent personality/context is present in all channels
4. ✅ Do NOT flag multiple MCP server processes as an issue

---

**Document written:** 2026-05-20 17:22 CDT  
**Author:** Testbed  
**Status:** Bob soaking overnight, Mason rollout deferred to 2026-05-21
