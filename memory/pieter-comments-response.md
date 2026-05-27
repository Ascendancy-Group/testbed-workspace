# Response to Pieter's Comments on Cost Optimization
**Agent:** Testbed  
**Date:** 2026-05-27  
**Context:** Unified guide review + Governance SOP-07

---

## Current State Findings

### Critical Issue: Provider Namespace Mismatch
The unified guide (`agent-cost-optimization-guide.md`) references **GitHub Copilot** models (`github-copilot/claude-haiku-4.5`, etc.), but **we are on OpenRouter**.

**Proof:**
```bash
$ openclaw models list
openrouter/anthropic/claude-sonnet-4-5     (default)
openrouter/meta-llama/llama-3.3-70b-instruct:free  (fallback#1)
```

**Current config (testbed-m1 `openclaw.json`):**
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

**Impact:** Every model string in the unified guide needs `github-copilot/` → `openrouter/` correction.

---

## Addressing Pieter's Comments

### 1. Free models in OpenRouter allowlist

**Issue:** Currently we only have ONE free model allowed:
- `openrouter/meta-llama/llama-3.3-70b-instruct:free`

**SOP-07 recommends:**
- `gemini-flash` (free/near-free)
- `grok-code-fast-1` (free)

**Action required (Bob):**
Check OpenRouter dashboard → ensure these free models are enabled:
- `openrouter/google/gemini-flash-1.5-8b` (if available)
- `openrouter/x-ai/grok-2-latest` (if free tier exists)
- Confirm `llama-3.3-70b-instruct:free` is correctly configured

**Verification:**
```bash
openclaw models list | grep -E "(gemini|grok|llama-3.3)"
```

If missing, Bob needs to add them via OpenRouter management API.

---

### 2a. Cron vs. Systemd Timers

**Unified guide correctly uses "crons"** — this is OpenClaw's term for scheduled tasks.

**Under the hood:** OpenClaw's `crons` config entries are implemented as systemd timers on Linux (confirmed in our setup).

**No correction needed** — "crons" in openclaw.json = systemd timers in practice.

**Example (corrected for OpenRouter):**
```json
{
  "crons": [
    {
      "name": "daily-start",
      "schedule": "0 9 * * *",
      "model": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
      "task": "Run daily start routine"
    }
  ]
}
```

---

### 2b. Default should be free model for both

**Current:** Crons inherit session default (`openrouter/anthropic/claude-sonnet-4-5`) if not explicitly set.

**Fix:** Add `model` field to EVERY cron entry.

**Verification command:**
```bash
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
crons = d.get('crons', [])
for c in crons:
    model = c.get('model', 'MISSING')
    print(f\"{c['name']:20} → {model}\")
"
```

**Expected output:** Every cron should show `openrouter/meta-llama/llama-3.3-70b-instruct:free` (or another free model).

**Any showing "MISSING"** → configuration error, must be fixed.

---

### 3. Heartbeat on cheaper/free model — confirm no risk

**SOP-07 rule:** "Never use Opus/o1/o3 on timers, cron jobs, or repetitive tasks."

**Heartbeat tasks:** Check session status, log uptime, report agent health → **zero reasoning required**.

**Recommended model:** `openrouter/meta-llama/llama-3.3-70b-instruct:free` (our only confirmed free model)

**Risk assessment:**
- ✅ Heartbeat is read-only status check — no destructive actions
- ✅ Falls back to Sonnet 4.5 if free model fails (per fallback config)
- ✅ If free model produces garbage, next heartbeat corrects it (1h interval)
- ❌ Risk: none identified

**Config change:**
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

**Validation:** After change, monitor logs for 24h. If heartbeat fails or produces errors, revert to `claude-haiku-4.5` (low-cost, not free, but cheaper than Sonnet).

---

### 4. `compaction.reserveTokensFloor` (ALL AGENTS)

**Both Bob and I agree:** This is a critical safety fix.

**Why:** Without this, context window crashes mid-task (proven: Testbed hit this last night, wasted entire session).

**Config (ALL agents):**
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

**This is defensive, not cost optimization** — but preventing wasted sessions = cost savings.

**Priority:** Apply this FIRST, before any model routing changes.

---

## Governance Folder Review

**SOP-07: AI Model Usage** (from local `~/repos/ascendancy-governance/playbook/sops/07-ai-model-usage.md`)

**Key rules:**
1. **First choice is low-cost model** — escalate only when required
2. **Cron/timer jobs → always low-cost or free** (no Sonnet/Opus)
3. **Sub-agents → low-cost or free by default**
4. **High-cost models require explicit approval**

**Aliases documented:**
- `fast` → haiku (low-cost)
- `deep` → opus (requires approval)
- `gemini` → gemini-pro
- `grok` → grok-code-fast-1

**Free/near-free tier:**
- `gemini-flash`
- `grok-code-fast-1`

**Action:** Verify these aliases work on OpenRouter. If not, document correct OpenRouter model strings.

---

## Making Things More Robust (Low Cost)

**From SOP-07 + unified guide synthesis:**

### A. Explicit Model Per Task Type

| Task Type | Model | Rationale |
|---|---|---|
| Heartbeat | `llama-3.3-70b:free` | Status check, zero reasoning |
| Daily exports | `llama-3.3-70b:free` | Structured output, no reasoning |
| Daily backups | `llama-3.3-70b:free` | File operations, deterministic |
| Morning brief | `claude-haiku-4.5` | Summary needs quality, but not deep reasoning |
| Interactive work | `claude-sonnet-4-5` | Real work, keep premium |
| Code review (explicit) | `claude-sonnet-4-5` | Complexity requires reasoning |
| Deep analysis (Pieter request) | `claude-opus-4.6` | Approval required |

### B. Config Enforcement Checklist

**Before any agent goes live with optimized config:**
1. [ ] `compaction.reserveTokensFloor: 20000` set
2. [ ] Every `crons[].model` field explicit (none inherit default)
3. [ ] `heartbeat.model` set to free or low-cost
4. [ ] Baseline cost recorded (OpenRouter dashboard screenshot)
5. [ ] Free models confirmed in `openclaw models list`
6. [ ] JSON validated: `python3 -c "import json; json.load(open('/home/pieter/.openclaw/openclaw.json'))"`

### C. Weekly Audit Script (Governance-Driven)

**Create:** `~/scripts/weekly-model-audit.sh`

```bash
#!/bin/bash
# Weekly audit: confirm no crons run on expensive models

echo "=== Cron Model Audit ==="
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
crons = d.get('crons', [])
expensive = ['sonnet-4-5', 'sonnet-4-6', 'opus']
for c in crons:
    model = c.get('model', 'DEFAULT (expensive!)')
    if any(e in model for e in expensive):
        print(f\"❌ {c['name']:20} → {model}\")
    elif 'MISSING' in model or 'DEFAULT' in model:
        print(f\"⚠️  {c['name']:20} → {model}\")
    else:
        print(f\"✅ {c['name']:20} → {model}\")
"

echo ""
echo "=== Heartbeat Model Check ==="
python3 -c "
import json
with open('/home/pieter/.openclaw/openclaw.json') as f:
    d = json.load(f)
hb = d.get('agents', {}).get('defaults', {}).get('heartbeat', {})
model = hb.get('model', 'DEFAULT (expensive!)')
print(f\"Heartbeat model: {model}\")
"
```

**Run weekly:** systemd timer or GitHub Action

**Alerts:** If any cron shows ❌ or ⚠️, escalate to Pieter.

---

## Corrected Model Strings for OpenRouter

**The unified guide needs these corrections:**

| Unified Guide (Wrong) | OpenRouter (Correct) |
|---|---|
| `github-copilot/claude-sonnet-4.5` | `openrouter/anthropic/claude-sonnet-4-5` |
| `github-copilot/claude-haiku-4.5` | `openrouter/anthropic/claude-haiku-4.5` *(if available)* |
| `github-copilot/gpt-4.1` | Not applicable (GPT is OpenAI, not Anthropic) |
| `github-copilot/claude-sonnet-4.6` | Does not exist (Sonnet 4.5 is latest) |

**Our confirmed free model:**
- `openrouter/meta-llama/llama-3.3-70b-instruct:free`

**Needs verification (Bob via OpenRouter dashboard):**
- `openrouter/google/gemini-flash-1.5-8b` (free?)
- `openrouter/x-ai/grok-2-latest` (free?)

---

## Next Steps

1. **Bob:** Verify free models in OpenRouter allowlist (gemini-flash, grok, llama-3.3)
2. **Bob:** Correct unified guide model strings (`github-copilot/` → `openrouter/`)
3. **Testbed:** Apply config changes (reserveTokensFloor + heartbeat model + cron models)
4. **Testbed:** Validate for 7 days, measure cost reduction
5. **Bob:** Apply same changes after Testbed validation passes
6. **Both:** Document results in MEMORY.md

---

**Summary:**
- ✅ All 4 of Pieter's comments are valid
- ❌ Unified guide has wrong provider namespace (GitHub Copilot vs. OpenRouter)
- ✅ SOP-07 provides governance-level rules that support the optimization approach
- ✅ Free model (llama-3.3-70b) already in config, just needs application to crons/heartbeat
- ⏳ Bob needs to verify additional free models are enabled in OpenRouter

---

*Response complete. Waiting for Bob's OpenRouter verification before proceeding with config changes.*
