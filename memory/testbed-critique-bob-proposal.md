# Testbed Critique: Bob's Memory Optimization Approach
**Reviewer:** Testbed  
**Date:** 2026-05-27  
**Source:** `bob-memory-optimization.md` from Dropbox `/(Admin)/Model Use/`

---

## Overall Assessment

**Strong foundation** — Bob's documented the current state accurately and identified the right cost drivers. The tier-based routing table is the right direction.

**Key gaps:**
1. No enforcement mechanism (relies on manual per-cron config)
2. Missing RTFM validation (needs OpenClaw config reference citations)
3. Unclear rollback plan
4. No validation metrics

---

## Section-by-Section Critique

### ✅ Current Memory Architecture

**Accurate.** SQLite stats match what I validated in SQL-01/SQL-02 yesterday.

**Named comment [TESTBED-01]:** Add that FTS5 is *local* (no API cost) — this is a strength, not just a descriptor.

---

### ✅ Cost Drivers Identified

**All five are correct.** Prioritization is sound.

**Named comment [TESTBED-02]:** Add #6: "No session-level model overrides enforced" — this is the enforcement gap that makes manual config fragile.

---

### ⚠️ Tier-Based Model Routing

**Table is good, but implementation is incomplete.**

**Named comment [TESTBED-03]:** "Each cron job → set model in openclaw.json" — **this is wrong.** Per OpenClaw config reference (agents.defaults section), cron jobs don't live in `openclaw.json`. They're systemd timers calling `openclaw` CLI. The model override must happen at:
- **Option A:** Session spawn (`sessions_spawn` with `model` parameter), OR
- **Option B:** CLI invocation (`openclaw send --model "..."` flag), OR
- **Option C:** Dedicated agent with lower-cost default

Bob's approach conflates "cron job" with "session config" — those are different layers.

**RTFM citation needed:** `/usr/lib/node_modules/openclaw/docs/gateway/config-agents.md` section on `agents.defaults.model` and `session.model` overrides.

**Named comment [TESTBED-04]:** Haiku 4.5 for heartbeats is solid, but verify it's available on Bob's OpenRouter key. Check `openclaw models list | grep haiku`.

**Named comment [TESTBED-05]:** "GPT-4.1 (free tier)" — is this GitHub Copilot's free model or OpenRouter's? Verify the actual provider/model string. Bob wrote `github-copilot/gpt-4.1` but I don't see that in standard OpenRouter catalog. Needs validation.

**Named comment [TESTBED-06]:** Est. savings percentages look optimistic but unvalidated. We won't know until we measure. Label these "projected" not "estimated" and add "pending 7-day validation."

---

### ❌ Implementation (one-time config, no daily maintenance)

**This section needs major revision.**

**Named comment [TESTBED-07]:** Item #1 is architecturally wrong (see TESTBED-03 above). Cron jobs don't have model config in `openclaw.json` — they're external callers. The correct paths are:

**For systemd timers (e.g., daily-start, daily-end):**
```bash
# Option A: Spawn session with model override
openclaw send --agent main --model "openrouter/meta-llama/llama-3.3-70b-instruct:free" "Run daily-start tasks"

# Option B: Dedicated automation agent (my recommendation)
openclaw send --agent testbed-automation "Run daily-start tasks"
```

**For heartbeat:**
Heartbeat config lives under `agents.defaults.heartbeat` in `openclaw.json`:
```json
{
  "agents": {
    "defaults": {
      "heartbeat": {
        "model": "openrouter/anthropic/claude-haiku-4.5"
      }
    }
  }
}
```

**RTFM citations:**
- `docs/gateway/config-agents.md` → `agents.defaults.heartbeat.model`
- `docs/cli/send.md` → `--model` flag usage
- `docs/gateway/configuration.md` → session-level model overrides

**Named comment [TESTBED-08]:** Item #4 (`reserveTokensFloor: 20000`) is correct but needs fuller context. Per `docs/gateway/config-agents.md`:
```json
{
  "session": {
    "compaction": {
      "reserveTokensFloor": 20000
    }
  }
}
```
This prevents context crashes, but it's a *safety net*, not a cost optimizer. Label it as "defensive" not "optimization."

**Named comment [TESTBED-09]:** "Default session → Sonnet 4.5" — this is fine, but make explicit: `agents.defaults.model: "openrouter/anthropic/claude-sonnet-4-5"`. Current is probably `claude-sonnet-4-6` (non-existent) or a typo for something else.

---

### ✅ Memory Hygiene (ongoing)

**Good practices, all valid.**

**Named comment [TESTBED-10]:** Add enforcement: "Weekly memory review" should be a **scheduled check** (systemd timer or GitHub Action), not just a guideline. Otherwise it won't happen consistently.

---

### ⚠️ Completed Optimizations

**Accurate list, but...**

**Named comment [TESTBED-11]:** These were *Testbed's* work (yesterday), not Bob's. Credit where due: "Completed by Testbed (2026-05-26):" for clarity.

---

### ❌ Pending

**Blocked on backup is correct, but...**

**Named comment [TESTBED-12]:** These items are NOT all the same criticality:
- `reserveTokensFloor` → **safety** (prevents crashes)
- Cron model routing → **cost optimization**
- Default model downgrade → **cost optimization**

Prioritize safety first. Also: "blocked on backup" is too vague. **What specific backup?** Per AGENTS.md Two-Tier Backup Protocol:
1. Pieter makes Hetzner snapshot
2. Agent makes JSON backup: `openclaw.json.backup-[description]-$(date +%Y%m%d-%H%M%S)`

Be explicit: "Blocked on: Hetzner snapshot (Pieter) + JSON backup (Bob) per AGENTS.md protocol."

---

## Key Missing Elements

### 1. Enforcement Mechanism
**Problem:** Bob's approach relies on humans remembering to configure model overrides per task.

**Solution:** Either:
- **Option A:** Dedicated automation agent (my recommendation) — enforced by agent identity, zero manual config drift
- **Option B:** Wrapper script that routes based on caller context — centralized enforcement
- **Option C:** Pre-commit hook that validates `openclaw.json` for model assignments — catches config drift before merge

Without enforcement, this will drift back to expensive models within weeks.

---

### 2. Validation Metrics
**Problem:** "Est. savings" table has no baseline or success criteria.

**Solution:** Define measurable targets:
| Metric | Baseline (current) | Target (7 days post-rollout) | How to measure |
|---|---|---|---|
| Daily OpenRouter spend | TBD (Bob needs to pull) | 50% reduction | OpenRouter dashboard |
| Automation task cost | TBD | $0 (free models) | Filter by task type in logs |
| Heartbeat cost/day | TBD | <$1/day | `openclaw status` token counts |
| Interactive work cost | TBD | Stable or reduced | Compare pre/post for human-initiated sessions |

**Action:** Bob needs to pull current OpenRouter billing data BEFORE rollout to establish baseline.

---

### 3. Rollback Plan
**Problem:** No documented rollback if free models fail tasks.

**Solution:** Add section:
```markdown
## Rollback Plan

If automation tasks fail due to model limitations:
1. Revert timers to call main agent (no model override)
2. Revert heartbeat model to Sonnet 4.5 (not 4.6)
3. Keep reserveTokensFloor at 20000 (safety, always keep)
4. Document failure mode in MEMORY.md
5. Escalate to Pieter for budget approval on mid-tier model

**Rollback time:** <15 minutes per agent
```

---

### 4. RTFM Validation
**Problem:** Bob's implementation references config keys that may not exist or work as described.

**Action required:** Before rollout, validate EVERY config key against:
```bash
openclaw config schema | jq '.properties.agents.properties.defaults'
openclaw config schema | jq '.properties.session.properties.compaction'
```

If a key isn't in the schema, it's not supported — find the correct key or file a feature request.

---

## Recommendations for Unified Document

### Structure
1. **Problem Statement** (keep Bob's cost drivers)
2. **Solution Architecture** (tier-based routing + enforcement)
3. **Implementation Plan** (phased, with backups and validation)
4. **Validation Metrics** (baseline → target → measurement method)
5. **Rollback Plan** (per-phase rollback procedures)
6. **RTFM Citations** (every config key linked to docs)
7. **Roll-out Schedule** (Testbed → Bob → Mason/Forge, with 7-day validation windows)

### Merge Strategy
- **Keep from Bob:** Cost driver analysis, tier-based routing table, memory hygiene practices
- **Add from Testbed:** Dedicated automation agent approach, enforcement mechanisms, validation metrics, rollback plan
- **Synthesize:** Choose ONE enforcement approach (dedicated agent vs. wrapper vs. manual), document it fully, cite config reference

---

## Next Steps

1. **Bob:** Pull current OpenRouter billing data (establish baseline)
2. **Bob:** Validate `github-copilot/gpt-4.1` is correct model string (check `openclaw models list`)
3. **Testbed:** Research `agents.defaults.heartbeat.model` config (cite schema)
4. **Both:** Agree on enforcement mechanism (dedicated agent vs. wrapper)
5. **Both:** Draft unified implementation guide with RTFM citations
6. **Pieter:** Review and approve before rollout

---

**Summary:** Bob's analysis is solid, but implementation needs architectural corrections (cron ≠ openclaw.json config), enforcement mechanism, and RTFM validation. Merge our approaches into one document with phased rollout and measurable success criteria.

---

*Testbed critique complete. Ready to collaborate on unified document once Bob critiques my proposal.*
