# WHAT — Cost Optimization Implementation

**Implementation Date:** 2026-05-27  
**Agent:** Testbed  
**Machine:** testbed-m1 (Hetzner VPS, Ubuntu 24.04)  
**Status:** ✅ Deployed and operational

---

## What Was Implemented

Deployed AI model cost optimization to reduce OpenClaw agent infrastructure spend from ~$100/3 days (~$1,000/month) to sustainable levels ($300/month limit for Testbed).

### Three Core Changes

#### 1. Context Crash Prevention
**Change:** Set `compaction.reserveTokensFloor: 20000`

**What it does:**
- Reserves 20,000 tokens as safety buffer during context compaction
- Prevents context crashes when compaction leaves insufficient room for response
- Applies to all model fallback attempts

**Config location:**
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

#### 2. Free-Tier Heartbeat
**Change:** Set `heartbeat.model: openrouter/meta-llama/llama-3.3-70b-instruct:free`

**What it does:**
- Heartbeat polls now use $0-cost free model instead of premium Sonnet 4.5
- 24 heartbeats/day × $0 = **100% cost reduction on heartbeat**
- Heartbeat interval increased from 30m to 1h (reduced frequency)

**Config location:**
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

#### 3. Updated Fallback Chain
**Change:** Simplified fallback to only available free model

**What it does:**
- Primary: `openrouter/anthropic/claude-sonnet-4-5` (unchanged for interactive work)
- Fallback: `openrouter/meta-llama/llama-3.3-70b-instruct:free` (cost-free safety net)
- Removes unreliable paid fallbacks

**Config location:**
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

---

## Immediate Impact

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| Heartbeat cost | Premium (Sonnet 4.5) | $0 (free model) | **100% reduction** |
| Heartbeat frequency | 30 minutes | 60 minutes | 50% reduction |
| Context crash risk | High (no floor) | Protected (20k buffer) | **Safety enabled** |
| Fallback reliability | Multiple paid models | One free model | Simplified |

---

## Models Used

### Available Models (2)
1. **`openrouter/anthropic/claude-sonnet-4-5`** — Premium, interactive work
2. **`openrouter/meta-llama/llama-3.3-70b-instruct:free`** — Free, automation/heartbeat

### Pending Models (5)
Once Bob confirms OpenRouter allowlist updated:
- **Low-cost:** `claude-haiku-4.5`, `gpt-5-mini`
- **Free:** `gemma-4-31b-it:free`, `gpt-oss-120b:free`, `nemotron-3-super:free`

These will enable documentation task routing (Haiku for quality writing at low cost).

---

## Scope

**Deployed to:** Testbed-M1 only  
**Not yet deployed:** Bob, Mason, Forge (pending 7-day validation)

---

## Governance Compliance

**SOP-07 (AI Model Usage):**
- ✅ No Chinese-origin models (Qwen removed from proposals)
- ✅ Explicit model assignment (no default inheritance for automation)
- ✅ Two-Tier backup protocol followed

---

## Validation Window

**Start:** 2026-05-27  
**End:** 2026-06-03 (7 days)

**Monitoring:**
- Daily OpenRouter spend tracking
- Heartbeat cycle logs
- Context compaction behavior
- Gateway stability

**Success criteria:**
- 60-70% cost reduction vs. baseline
- No context crashes
- No gateway instability
- Heartbeat successful on free model

---

## Next Steps

1. **Monitor 7 days** — track OpenRouter daily spend
2. **Bob verification** — confirm low-cost models added to OpenRouter
3. **Documentation routing** — add Haiku for quality writing tasks
4. **Rollout to Bob** — after validation passes
5. **Rollout to Mason/Forge** — parallel deployment after Bob

---

**Implementation complete. System operational.**
