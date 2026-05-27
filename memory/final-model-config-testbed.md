# Final Model Configuration for Testbed — Deployment Ready
**Agent:** Testbed  
**Date:** 2026-05-27  
**Hetzner Snapshot:** `Testbed-M1-PreJSON-ModelCahnges-CostReduction-05-27-2026`

---

## Confirmed Available Models in OpenRouter

From Pieter's final list (2026-05-27 16:30):

**Low-Cost:**
- `openrouter/anthropic/claude-haiku-4.5`
- `openrouter/anthropic/claude-sonnet-4.5` (current default)
- `openrouter/openai/gpt-5-mini`

**Free:**
- `openrouter/openai/gpt-oss-120b:free`
- `openrouter/google/gemma-4-31b-it:free`
- `openrouter/meta-llama/llama-3.3-70b-instruct:free` ✅ already working
- `openrouter/nvidia/nemotron-3-super:free`

---

## Selected Models for Testbed Deployment

### 3 Low-Cost Models
1. **`openrouter/anthropic/claude-haiku-4.5`**
   - Use: Summaries, structured Q&A, morning briefs
   - Cost: Low (~$0.25/1M tokens)

2. **`openrouter/anthropic/claude-sonnet-4.5`**
   - Use: Interactive work, code review (current default)
   - Cost: Moderate (stays as primary)

3. **`openrouter/openai/gpt-5-mini`**
   - Use: General fallback, sub-agents needing reasoning
   - Cost: Low

### 4 Free Models (all will be used)
1. **`openrouter/meta-llama/llama-3.3-70b-instruct:free`** ✅ proven
   - Use: Heartbeat, cron automation, backups, exports

2. **`openrouter/google/gemma-4-31b-it:free`**
   - Use: Sub-agents, parallel processing

3. **`openrouter/openai/gpt-oss-120b:free`**
   - Use: Backup free option, bulk processing

4. **`openrouter/nvidia/nemotron-3-super:free`**
   - Use: Technical tasks, code generation (free tier)

---

## JSON Configuration Changes

### Change 1: compaction.reserveTokensFloor (CRITICAL SAFETY)

**Location:** `agents.defaults.compaction`

**Current:**
```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard"
      }
    }
  }
}
```

**New:**
```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard",
        "reserveTokensFloor": 20000
      }
    }
  }
}
```

---

### Change 2: Heartbeat Model (FREE)

**Location:** `agents.defaults.heartbeat`

**Current:**
```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "1h"
      }
    }
  }
}
```

**New:**
```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "every": "1h",
        "model": "openrouter/meta-llama/llama-3.3-70b-instruct:free"
      }
    }
  }
}
```

---

### Change 3: Model Fallbacks (Updated)

**Location:** `agents.defaults.model`

**Current:**
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "openrouter/anthropic/claude-sonnet-4-5",
        "fallbacks": [
          "openrouter/meta-llama/llama-3.3-70b-instruct:free"
        ]
      }
    }
  }
}
```

**New:**
```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "openrouter/anthropic/claude-sonnet-4-5",
        "fallbacks": [
          "openrouter/anthropic/claude-haiku-4.5",
          "openrouter/openai/gpt-5-mini",
          "openrouter/meta-llama/llama-3.3-70b-instruct:free",
          "openrouter/google/gemma-4-31b-it:free"
        ]
      }
    }
  }
}
```

---

### Change 4: Cron Model Assignment (FREE for all automation)

**Current crons (need to check actual config):**
```bash
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
crons = d.get('crons', [])
if crons:
    print('Current crons:')
    for c in crons:
        print(f\"  {c.get('name', 'unnamed')}: model={c.get('model', 'MISSING')}\")
else:
    print('No crons found in config')
"
```

**Template for each cron entry:**
```json
{
  "name": "daily-start",
  "schedule": "0 9 * * *",
  "model": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
  "task": "Run daily start routine"
}
```

**All cron entries MUST have explicit `model` field set to FREE model.**

---

## Task → Model Assignment Reference

| Task Type | Model | Namespace | Cost |
|---|---|---|---|
| Heartbeat | `llama-3.3-70b:free` | OpenRouter | $0 |
| Daily exports | `llama-3.3-70b:free` | OpenRouter | $0 |
| Daily backups | `llama-3.3-70b:free` | OpenRouter | $0 |
| Morning briefs | `claude-haiku-4.5` | OpenRouter | Low |
| Simple Q&A | `claude-haiku-4.5` | OpenRouter | Low |
| Sub-agents (simple) | `gemma-4-31b:free` | OpenRouter | $0 |
| Sub-agents (reasoning) | `gpt-5-mini` | OpenRouter | Low |
| Interactive work | `claude-sonnet-4-5` | OpenRouter | Default |
| Code review | `claude-sonnet-4-5` | OpenRouter | Default |

---

## Deployment Procedure (Testbed Only, Today)

### Pre-Flight Checklist
- [x] Hetzner snapshot exists: `Testbed-M1-PreJSON-ModelCahnges-CostReduction-05-27-2026`
- [ ] Workspace backup to GitHub
- [ ] JSON backup (Two-Tier protocol)
- [ ] Critical files backup
- [ ] Current cron configuration documented
- [ ] Gateway model list refreshed
- [ ] JSON changes validated (syntax check)

### Step 1: Backup to GitHub Repo
```bash
cd ~/.openclaw/workspace
git add -A
git commit -m "Pre-cost-optimization backup 2026-05-27"
git push origin main
```

### Step 2: Critical Files Backup (Two-Tier Protocol)
```bash
# JSON backup
cp ~/.openclaw/openclaw.json \
   ~/.openclaw/openclaw.json.backup-cost-optimization-$(date +%Y%m%d-%H%M%S)

# Identity files backup
BACKUP_DIR=~/.openclaw/workspace/Backups-Granular/CRITICAL-FILES__$(date +%Y-%m-%d_%H-%M)
mkdir -p "$BACKUP_DIR"
for f in SOUL.md AGENTS.md MEMORY.md USER.md TOOLS.md IDENTITY.md HANDOFF.md HEARTBEAT.md; do
  [ -f ~/.openclaw/workspace/$f ] && cp ~/.openclaw/workspace/$f "$BACKUP_DIR/"
done
echo "Backup complete: $BACKUP_DIR"
```

### Step 3: Document Current State
```bash
# Record current config
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
print('=== Current Config ===')
print('Default model:', d.get('agents', {}).get('defaults', {}).get('model', {}))
print('Heartbeat:', d.get('agents', {}).get('defaults', {}).get('heartbeat', {}))
print('Compaction:', d.get('agents', {}).get('defaults', {}).get('compaction', {}))
print('Crons:', d.get('crons', []))
" > ~/.openclaw/workspace/memory/pre-optimization-config-$(date +%Y%m%d-%H%M).txt
```

### Step 4: Verify Gateway Model List
```bash
openclaw gateway restart
sleep 5
openclaw models list | grep -E "(haiku|gemma|llama|gpt-5-mini|gpt-oss|nemotron)"
```

**Expected output must include:**
- `openrouter/anthropic/claude-haiku-4.5`
- `openrouter/meta-llama/llama-3.3-70b-instruct:free`
- `openrouter/google/gemma-4-31b-it:free`
- `openrouter/openai/gpt-oss-120b:free`
- `openrouter/nvidia/nemotron-3-super:free`
- `openrouter/openai/gpt-5-mini`

If ANY are missing, STOP and report to Pieter.

### Step 5: Apply JSON Changes
```bash
python3 << 'PYEOF'
import json
from pathlib import Path

config_path = Path.home() / '.openclaw' / 'openclaw.json'
with open(config_path) as f:
    config = json.load(f)

# Change 1: compaction.reserveTokensFloor
if 'agents' not in config:
    config['agents'] = {}
if 'defaults' not in config['agents']:
    config['agents']['defaults'] = {}
if 'compaction' not in config['agents']['defaults']:
    config['agents']['defaults']['compaction'] = {}

config['agents']['defaults']['compaction']['mode'] = 'safeguard'
config['agents']['defaults']['compaction']['reserveTokensFloor'] = 20000

# Change 2: heartbeat.model
if 'heartbeat' not in config['agents']['defaults']:
    config['agents']['defaults']['heartbeat'] = {}

config['agents']['defaults']['heartbeat']['every'] = '1h'
config['agents']['defaults']['heartbeat']['model'] = 'openrouter/meta-llama/llama-3.3-70b-instruct:free'

# Change 3: model fallbacks
if 'model' not in config['agents']['defaults']:
    config['agents']['defaults']['model'] = {}

config['agents']['defaults']['model']['primary'] = 'openrouter/anthropic/claude-sonnet-4-5'
config['agents']['defaults']['model']['fallbacks'] = [
    'openrouter/anthropic/claude-haiku-4.5',
    'openrouter/openai/gpt-5-mini',
    'openrouter/meta-llama/llama-3.3-70b-instruct:free',
    'openrouter/google/gemma-4-31b-it:free'
]

# Change 4: cron models (add free model to all crons)
if 'crons' in config:
    for cron in config['crons']:
        if 'model' not in cron:
            cron['model'] = 'openrouter/meta-llama/llama-3.3-70b-instruct:free'
            print(f"Added free model to cron: {cron.get('name', 'unnamed')}")

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("✅ JSON changes applied")
PYEOF
```

### Step 6: Validate JSON Syntax
```bash
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    json.load(f)
print('✅ JSON syntax valid')
"
```

### Step 7: Restart Gateway
```bash
openclaw gateway restart
sleep 5
openclaw status
```

### Step 8: Validation Checks
```bash
# Check heartbeat is using free model
tail -f ~/.openclaw/logs/gateway.log | grep -i "heartbeat"
# Wait for next heartbeat cycle (up to 1 hour)

# Check crons have model set
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
print('=== Cron Models ===')
for c in d.get('crons', []):
    model = c.get('model', '⚠️ MISSING')
    print(f\"{c.get('name', 'unnamed'):20} → {model}\")
"

# Check compaction floor is set
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
floor = d.get('agents', {}).get('defaults', {}).get('compaction', {}).get('reserveTokensFloor', 'MISSING')
print(f'reserveTokensFloor: {floor}')
"
```

---

## Success Criteria (7-Day Validation)

| Metric | Baseline (Pre-Change) | Target (7 Days) | Measurement |
|---|---|---|---|
| Daily OR spend | TBD (record today) | -60% | OpenRouter dashboard |
| Heartbeat cost | TBD | $0 | Filter logs by heartbeat |
| Cron automation cost | TBD | $0 | Filter logs by cron names |
| Interactive work cost | TBD | Stable or -10% | Compare human-initiated sessions |
| Context crashes | TBD | 0 | Check for compaction errors |

---

## Rollback Plan

If issues occur:
```bash
# 1. Restore JSON from backup
cp ~/.openclaw/openclaw.json.backup-cost-optimization-TIMESTAMP \
   ~/.openclaw/openclaw.json

# 2. Restart gateway
openclaw gateway restart

# 3. Verify restoration
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
print('Restored config verified')
"
```

**Rollback time:** <5 minutes

---

## Post-Deployment Documentation

After successful deployment:
1. Update MEMORY.md with new model config
2. Commit changes to workspace repo
3. Document baseline costs for 7-day comparison
4. Create daily log entry in `memory/2026-05-27.md`

---

*Deployment-ready. Awaiting Pieter's go-ahead to execute.*

---

## Documentation & GitHub Task Model Assignment

**Documentation tasks use LOW-COST models, not free.**

### Model: `openrouter/anthropic/claude-haiku-4.5`

**Use for:**
- GitHub commit messages
- README updates
- Technical documentation (SOPs, HOW.md, implementation guides)
- Session notes (daily logs in `memory/YYYY-MM-DD.md`)
- MEMORY.md updates
- HANDOFF.md updates
- Test reports and validation summaries

**Why Haiku over free models:**
- Quality writing needed for long-term documentation
- Better structure and formatting
- Clear, professional commit messages
- 80-90% cheaper than Sonnet 4.5 while maintaining quality

### When to use FREE models for file operations:
- Simple file lists (backup manifests)
- Deterministic JSON generation
- Directory structures
- Basic logs without narrative

**Model:** `openrouter/meta-llama/llama-3.3-70b-instruct:free`

### When to escalate to PREMIUM (Sonnet 4.5):
- Code review documentation (needs reasoning)
- Complex architecture decisions
- When Pieter explicitly requests premium quality
- Critical implementation guides affecting production

---

## Implementation Note: Manual Model Selection

**Current limitation:** OpenClaw does not auto-detect "this is documentation work" vs. "this is a cron job."

**Options:**
1. **Manual awareness** — Agent chooses Haiku when writing docs (current approach)
2. **Task wrapper** — Script routes based on task type
3. **Future enhancement** — Request OpenClaw feature for task-based model routing

**For this deployment:** Testbed will manually use Haiku for documentation tasks until automated routing is implemented.

---

