# HOW — Step-by-Step Implementation Guide

**Target:** Any OpenClaw agent (Bob, Mason, Forge, Testbed)  
**Time:** ~30 minutes  
**Rollback:** <5 minutes if needed  
**Validated on:** Testbed-M1 (2026-05-27)

---

## Prerequisites

### Required Access
- [ ] SSH access to target machine (via Tailscale or direct IP)
- [ ] `sudo` privileges (if gateway runs as systemd service)
- [ ] GitHub SSH key configured (for workspace repo commits)
- [ ] 1Password CLI access (for OpenRouter API key verification)

### Required Tools
- [ ] OpenClaw CLI (`openclaw` command available)
- [ ] Python 3.8+ (for JSON validation scripts)
- [ ] `jq` (for JSON manipulation, optional but helpful)

### Before You Start
- [ ] Read `WHY.md` — understand the rationale
- [ ] Read `WHAT.md` — understand what's changing
- [ ] Verify current OpenRouter spend baseline (via dashboard)
- [ ] Ensure Hetzner/VPS snapshot capability available

---

## Phase 1: Pre-Flight Checks (15 minutes)

### Step 1.1: Document Current State
```bash
# Check gateway status
openclaw status

# Check current model config
openclaw models list

# Document current spend (OpenRouter dashboard)
# https://openrouter.ai/usage
# Take screenshot or note last 7-day total

# Check current heartbeat interval
grep -A5 '"heartbeat"' ~/.openclaw/openclaw.json || echo "No heartbeat config"
```

**Record these values:**
- Current model: `______________________`
- Heartbeat interval: `______________________`
- Last 7-day spend: `$______________________`

---

### Step 1.2: Create Hetzner Snapshot
**⚠️ CRITICAL — Do NOT skip this step**

```bash
# Via Hetzner Web UI:
# 1. Go to https://console.hetzner.cloud/
# 2. Select project > Select machine > Snapshots tab
# 3. Create snapshot: "PreCostOptimization-YYYY-MM-DD"
# 4. Wait for "Available" status (2-5 minutes)
```

**Snapshot name format:**
```
<machine>-PreCostOptimization-YYYY-MM-DD
Example: testbed-m1-PreCostOptimization-2026-05-27
```

**Verify snapshot exists:**
- [ ] Snapshot status: "Available"
- [ ] Snapshot size matches disk usage
- [ ] Snapshot timestamp is current

---

### Step 1.3: Backup openclaw.json (Two-Tier Protocol)
```bash
# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
cp ~/.openclaw/openclaw.json \
   ~/.openclaw/openclaw.json.backup-cost-optimization-${TIMESTAMP}

# Verify backup exists
ls -lh ~/.openclaw/openclaw.json.backup-*

# Output example:
# -rw-r--r-- 1 pieter pieter 8.2K May 27 16:39 openclaw.json.backup-cost-optimization-20260527-163944
```

**Record backup filename:**
```
openclaw.json.backup-cost-optimization-____________________
```

---

### Step 1.4: Backup Critical Identity Files
```bash
# Create granular backup directory
BACKUP_DIR=~/.openclaw/workspace/Backups-Granular/CRITICAL-FILES__$(date +%Y-%m-%d_%H-%M)
mkdir -p "$BACKUP_DIR"

# Backup all identity files
for f in SOUL.md AGENTS.md MEMORY.md USER.md TOOLS.md IDENTITY.md HANDOFF.md HEARTBEAT.md; do
  if [ -f ~/.openclaw/workspace/$f ]; then
    cp ~/.openclaw/workspace/$f "$BACKUP_DIR/"
    echo "✓ Backed up: $f"
  fi
done

# Verify
ls -lh "$BACKUP_DIR"
```

**Record backup directory:**
```
Backups-Granular/CRITICAL-FILES______________________
```

---

### Step 1.5: Commit Workspace to GitHub
```bash
cd ~/.openclaw/workspace
git add -A
git commit -m "Pre-cost-optimization backup $(date +%Y-%m-%d)"
git push origin main

# Verify commit
git log -1 --oneline
```

**Record commit hash:**
```
Pre-optimization commit: ____________________
```

---

## Phase 2: Apply Configuration Changes (10 minutes)

### Step 2.1: Verify Models Available
```bash
# Check current model list
openclaw models list

# Required models:
# - openrouter/anthropic/claude-sonnet-4-5 (should exist)
# - openrouter/meta-llama/llama-3.3-70b-instruct:free (should exist)
```

**If either model is missing:**
```bash
# Contact Bob to add to OpenRouter allowlist
# Do NOT proceed until both models are confirmed
```

---

### Step 2.2: Create JSON Patch Script
```bash
# Create Python script to apply changes
cat > /tmp/apply-cost-optimization.py << 'PYEOF'
import json
from pathlib import Path
import sys

config_path = Path.home() / '.openclaw' / 'openclaw.json'

print("=== Applying Cost Optimization Changes ===\n")

# Read current config
with open(config_path) as f:
    config = json.load(f)

# Ensure structure exists
if 'agents' not in config:
    config['agents'] = {}
if 'defaults' not in config['agents']:
    config['agents']['defaults'] = {}

# Change 1: compaction.reserveTokensFloor
if 'compaction' not in config['agents']['defaults']:
    config['agents']['defaults']['compaction'] = {}

config['agents']['defaults']['compaction']['mode'] = 'safeguard'
config['agents']['defaults']['compaction']['reserveTokensFloor'] = 20000
print("✓ Applied: compaction.reserveTokensFloor = 20000")

# Change 2: heartbeat.model
if 'heartbeat' not in config['agents']['defaults']:
    config['agents']['defaults']['heartbeat'] = {}

config['agents']['defaults']['heartbeat']['every'] = '1h'
config['agents']['defaults']['heartbeat']['model'] = 'openrouter/meta-llama/llama-3.3-70b-instruct:free'
print("✓ Applied: heartbeat.model = llama-3.3-70b:free")
print("✓ Applied: heartbeat.every = 1h")

# Change 3: model.fallbacks
if 'model' not in config['agents']['defaults']:
    config['agents']['defaults']['model'] = {}

config['agents']['defaults']['model']['primary'] = 'openrouter/anthropic/claude-sonnet-4-5'
config['agents']['defaults']['model']['fallbacks'] = [
    'openrouter/meta-llama/llama-3.3-70b-instruct:free'
]
print("✓ Applied: model fallbacks updated")

# Write back
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)

print("\n✅ All changes applied successfully")
print(f"Config written to: {config_path}")

# Verify JSON is valid
try:
    with open(config_path) as f:
        json.load(f)
    print("✅ JSON syntax validated")
except json.JSONDecodeError as e:
    print(f"❌ JSON validation failed: {e}")
    sys.exit(1)
PYEOF

# Run the script
python3 /tmp/apply-cost-optimization.py
```

**Expected output:**
```
=== Applying Cost Optimization Changes ===

✓ Applied: compaction.reserveTokensFloor = 20000
✓ Applied: heartbeat.model = llama-3.3-70b:free
✓ Applied: heartbeat.every = 1h
✓ Applied: model fallbacks updated

✅ All changes applied successfully
Config written to: /home/pieter/.openclaw/openclaw.json
✅ JSON syntax validated
```

**If errors occur:**
```bash
# Restore from backup immediately
LATEST_BACKUP=$(ls -t ~/.openclaw/openclaw.json.backup-* | head -1)
cp "$LATEST_BACKUP" ~/.openclaw/openclaw.json
echo "⚠️ Rolled back to: $LATEST_BACKUP"
```

---

### Step 2.3: Validate JSON Syntax
```bash
# Verify JSON is valid
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    config = json.load(f)
print('✅ JSON syntax valid')
print('\nVerified changes:')
print(f\"  reserveTokensFloor: {config['agents']['defaults']['compaction']['reserveTokensFloor']}\")
print(f\"  heartbeat.model: {config['agents']['defaults']['heartbeat']['model']}\")
print(f\"  heartbeat.every: {config['agents']['defaults']['heartbeat']['every']}\")
print(f\"  primary model: {config['agents']['defaults']['model']['primary']}\")
print(f\"  fallbacks: {config['agents']['defaults']['model']['fallbacks']}\")
"
```

**Expected output:**
```
✅ JSON syntax valid

Verified changes:
  reserveTokensFloor: 20000
  heartbeat.model: openrouter/meta-llama/llama-3.3-70b-instruct:free
  heartbeat.every: 1h
  primary model: openrouter/anthropic/claude-sonnet-4-5
  fallbacks: ['openrouter/meta-llama/llama-3.3-70b-instruct:free']
```

---

### Step 2.4: Restart Gateway
```bash
# Restart to load new config
openclaw gateway restart

# Wait for startup
sleep 5

# Verify gateway is running
openclaw status | head -20
```

**Check for:**
- [ ] Gateway status: "running"
- [ ] PID changed (new process)
- [ ] No error messages in status output

**If gateway fails to start:**
```bash
# Check logs
openclaw gateway logs --tail 50

# If config error, restore backup:
LATEST_BACKUP=$(ls -t ~/.openclaw/openclaw.json.backup-* | head -1)
cp "$LATEST_BACKUP" ~/.openclaw/openclaw.json
openclaw gateway restart
```

---

## Phase 3: Validation (5 minutes)

### Step 3.1: Verify Configuration Loaded
```bash
# Check that changes are active
openclaw status | grep -A5 "Heartbeat"

# Should show:
# Heartbeat: 1h interval
# Model: llama-3.3-70b:free
```

---

### Step 3.2: Test Heartbeat Cycle
```bash
# Wait for next heartbeat (max 1 hour)
# Or trigger manually if OpenClaw supports it

# Monitor logs for heartbeat
openclaw gateway logs --tail 100 | grep -i heartbeat

# Look for:
# - "Heartbeat poll" message
# - Model used: llama-3.3-70b:free
# - No errors
```

---

### Step 3.3: Verify Model Fallback
```bash
# Check model list shows both models
openclaw models list | grep -E "(sonnet-4-5|llama-3.3)"

# Expected:
# openrouter/anthropic/claude-sonnet-4-5     text       195k  ...
# openrouter/meta-llama/llama-3.3-70b-ins... text       195k  ...
```

---

### Step 3.4: Commit Changes
```bash
cd ~/.openclaw/workspace
git add -A
git commit -m "Cost optimization deployed: heartbeat free model, compaction floor set"
git push origin main

# Record commit hash
git log -1 --oneline
```

**Deployment commit:**
```
____________________
```

---

## Phase 4: Monitoring (7 days)

### Daily Checks (5 minutes/day)
```bash
# 1. Check OpenRouter spend
# Visit: https://openrouter.ai/usage
# Record daily spend

# 2. Check gateway logs for errors
openclaw gateway logs --tail 200 | grep -iE "(error|fail|crash)"

# 3. Check heartbeat success
openclaw gateway logs --tail 100 | grep -i heartbeat | tail -5

# 4. Monitor context compaction
openclaw gateway logs --tail 200 | grep -i compaction
```

### Monitoring Checklist
Create a table to track daily:

| Date | OpenRouter Spend | Heartbeat Status | Errors | Notes |
|------|------------------|------------------|--------|-------|
| Day 1 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |
| Day 2 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |
| Day 3 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |
| Day 4 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |
| Day 5 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |
| Day 6 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |
| Day 7 | $______ | ✓ / ✗ | ✓ / ✗ | ________________ |

### Success Criteria (Day 7)
- [ ] 7-day spend 60-70% below baseline
- [ ] No context crashes logged
- [ ] All heartbeat polls successful
- [ ] No gateway instability
- [ ] No user-facing issues reported

---

## Rollback Procedure (if needed)

### When to Rollback
Rollback immediately if:
- Gateway fails to start after restart
- Context crashes increase
- Heartbeat fails consistently
- User-facing errors occur
- Spend increases instead of decreases

### Rollback Steps (< 5 minutes)
```bash
# 1. Stop gateway
openclaw gateway stop

# 2. Restore JSON backup
LATEST_BACKUP=$(ls -t ~/.openclaw/openclaw.json.backup-cost-optimization-* | head -1)
cp "$LATEST_BACKUP" ~/.openclaw/openclaw.json
echo "Restored: $LATEST_BACKUP"

# 3. Restart gateway
openclaw gateway start

# 4. Verify status
openclaw status

# 5. Document rollback
cd ~/.openclaw/workspace
git add -A
git commit -m "ROLLBACK: Cost optimization reverted due to [REASON]"
git push origin main
```

### If Rollback Fails
```bash
# Nuclear option: Restore from Hetzner snapshot
# 1. Go to Hetzner Console
# 2. Select machine > Snapshots
# 3. Restore from "PreCostOptimization-YYYY-MM-DD"
# 4. Wait 5-10 minutes for restore
# 5. SSH back in and verify gateway running
```

---

## Post-Deployment Actions

### After 7-Day Validation Passes
```bash
# 1. Update MEMORY.md with validation results
# 2. Create detailed cost analysis report
# 3. Schedule rollout to next agent (Bob)
# 4. Document lessons learned
```

### Add Documentation Task Routing (when low-cost models available)
Once Bob confirms `claude-haiku-4.5` is in OpenRouter allowlist:

```json
{
  "agents": {
    "defaults": {
      "model": {
        "primary": "openrouter/anthropic/claude-sonnet-4-5",
        "fallbacks": [
          "openrouter/anthropic/claude-haiku-4.5",
          "openrouter/meta-llama/llama-3.3-70b-instruct:free"
        ]
      }
    }
  }
}
```

**Note:** This requires manual model selection for documentation tasks until OpenClaw supports task-based routing.

---

## Troubleshooting

### Issue: Models Not Available
**Symptom:** `openclaw models list` doesn't show required models

**Solution:**
```bash
# 1. Check OpenRouter account allowlist
# 2. Contact Bob to add models via management API
# 3. Wait 5-10 minutes for sync
# 4. Restart gateway: openclaw gateway restart
```

---

### Issue: JSON Validation Fails
**Symptom:** Python script reports JSON syntax error

**Solution:**
```bash
# 1. Restore backup immediately
LATEST_BACKUP=$(ls -t ~/.openclaw/openclaw.json.backup-* | head -1)
cp "$LATEST_BACKUP" ~/.openclaw/openclaw.json

# 2. Check what went wrong
python3 -m json.tool ~/.openclaw/openclaw.json

# 3. Fix syntax errors manually
# 4. Re-run validation script
```

---

### Issue: Gateway Won't Start
**Symptom:** `openclaw status` shows "not running"

**Solution:**
```bash
# 1. Check logs
openclaw gateway logs --tail 100

# 2. Look for config errors
# 3. Restore backup if config issue
# 4. Restart gateway
```

---

### Issue: Heartbeat Using Wrong Model
**Symptom:** Logs show Sonnet 4.5 for heartbeat instead of free model

**Solution:**
```bash
# 1. Verify config was applied
grep -A10 '"heartbeat"' ~/.openclaw/openclaw.json

# 2. If config correct but not loaded, restart gateway
openclaw gateway restart

# 3. If still wrong, check model string exactly matches
# Must be: openrouter/meta-llama/llama-3.3-70b-instruct:free
```

---

## Checklist Summary

**Pre-flight:**
- [ ] Hetzner snapshot created
- [ ] JSON backup created
- [ ] Identity files backed up
- [ ] Workspace committed to GitHub
- [ ] Current state documented

**Deployment:**
- [ ] Models verified available
- [ ] JSON patch script run successfully
- [ ] JSON syntax validated
- [ ] Gateway restarted successfully
- [ ] Changes committed to GitHub

**Validation:**
- [ ] Config loaded correctly
- [ ] Heartbeat using free model
- [ ] No errors in logs
- [ ] 7-day monitoring plan started

**Rollback ready:**
- [ ] JSON backup path recorded
- [ ] Hetzner snapshot name recorded
- [ ] Rollback procedure tested (optional but recommended)

---

**Time estimate:**
- Pre-flight: 15 minutes
- Deployment: 10 minutes
- Validation: 5 minutes
- **Total: 30 minutes**

**Rollback time: <5 minutes**

---

**Implementation guide complete. Follow step-by-step for safe deployment.**
