# Work Tickets — Cost Optimization

**Implementation tracking for 2026-05-27 cost optimization deployment.**

---

## Epic: Cost Optimization

**Goal:** Reduce OpenClaw infrastructure spend from $1,000/month to $300/month (60-70% reduction)

**Owner:** Testbed  
**Reviewer:** Bob the Builder  
**Approver:** Pieter van der Wal

---

## ✅ TICKET-01: Model Selection & Governance Review

**Status:** Complete  
**Assignee:** Testbed  
**Completed:** 2026-05-27

### Scope
- Research available low-cost and free models on OpenRouter
- Verify governance compliance (SOP-07: no Chinese models)
- Propose 6 models (3 low-cost, 3 free)
- Document rationale

### Deliverables
- ✅ `proposed-models-testbed-bob.md` (8,887 bytes)
- ✅ Qwen (Chinese) removed, replaced with Mistral (France)
- ✅ Governance review passed

### Models Approved
**Low-cost:**
1. `openrouter/anthropic/claude-haiku-4.5`
2. `openrouter/anthropic/claude-sonnet-4-5`
3. `openrouter/openai/gpt-5-mini`

**Free:**
1. `openrouter/meta-llama/llama-3.3-70b-instruct:free` ✅
2. `openrouter/google/gemma-4-31b-it:free`
3. `openrouter/openai/gpt-oss-120b:free`
4. `openrouter/nvidia/nemotron-3-super:free`

---

## ✅ TICKET-02: Critique Bob's Proposal

**Status:** Complete  
**Assignee:** Testbed  
**Completed:** 2026-05-27

### Scope
- Review Bob's memory optimization approach
- Identify architectural conflicts (cron vs openclaw.json)
- Propose enforcement mechanisms
- Document gaps

### Deliverables
- ✅ `testbed-critique-bob-proposal.md` (9,352 bytes)
- ✅ 12 named comments (TESTBED-01 through TESTBED-12)
- ✅ Key issues identified: cron/JSON confusion, enforcement needed

### Key Findings
- Bob conflated cron job config with openclaw.json
- Need explicit model assignment for automation
- Validation metrics required
- Rollback plan missing

---

## ✅ TICKET-03: Unified Cost Analysis

**Status:** Complete  
**Assignee:** Testbed  
**Completed:** 2026-05-27

### Scope
- Address Pieter's 4 comments
- Create unified cost optimization response
- Document provider namespace differences (GitHub Copilot vs OpenRouter)
- Propose 3-option implementation approach

### Deliverables
- ✅ `testbed-pieter-comments-response.md` (9,220 bytes)
- ✅ Addressed all 4 Pieter comments
- ✅ Identified GitHub Copilot vs OpenRouter mismatch
- ✅ Recommended Option 1 (dedicated automation agent)

---

## ✅ TICKET-04: Pre-Deployment Backups

**Status:** Complete  
**Assignee:** Testbed  
**Completed:** 2026-05-27 16:39 CDT

### Scope
- Create Hetzner snapshot
- Backup openclaw.json (Two-Tier protocol)
- Backup critical identity files
- Commit workspace to GitHub

### Deliverables
- ✅ Hetzner snapshot: `Testbed-M1-PreJSON-ModelCahnges-CostReduction-05-27-2026`
- ✅ JSON backup: `openclaw.json.backup-cost-optimization-20260527-163944`
- ✅ Identity files: `Backups-Granular/CRITICAL-FILES__2026-05-27_16-39/`
- ✅ Git commit: `7ce4d54`

---

## ✅ TICKET-05: Apply Configuration Changes

**Status:** Complete  
**Assignee:** Testbed  
**Completed:** 2026-05-27 17:30 CDT

### Scope
- Apply `compaction.reserveTokensFloor: 20000`
- Set `heartbeat.model: llama-3.3-70b:free`
- Update fallback chain
- Validate JSON syntax
- Restart gateway

### Deliverables
- ✅ JSON changes applied via Python script
- ✅ JSON validated (no syntax errors)
- ✅ Gateway restarted successfully (pid 95686)
- ✅ Config loaded and active

### Changes Applied
```json
{
  "agents": {
    "defaults": {
      "compaction": {
        "mode": "safeguard",
        "reserveTokensFloor": 20000
      },
      "heartbeat": {
        "every": "1h",
        "model": "openrouter/meta-llama/llama-3.3-70b-instruct:free"
      },
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

## ✅ TICKET-06: Post-Deployment Validation

**Status:** Complete  
**Assignee:** Testbed  
**Completed:** 2026-05-27 17:45 CDT

### Scope
- Verify config loaded correctly
- Commit changes to GitHub
- Update MEMORY.md
- Create daily log entry
- Upload documentation to Dropbox

### Deliverables
- ✅ Config verification passed
- ✅ Git commit: `14eb7ec`
- ✅ MEMORY.md updated
- ✅ Daily log: `memory/2026-05-27.md`
- ✅ Dropbox: `final-model-config-testbed.md` uploaded

---

## 🕐 TICKET-07: 7-Day Monitoring

**Status:** In Progress  
**Assignee:** Testbed  
**Started:** 2026-05-27  
**Due:** 2026-06-03

### Scope
- Monitor OpenRouter daily spend
- Track heartbeat success rate
- Check for context crashes
- Verify gateway stability
- Document any issues

### Daily Checklist
- [ ] Day 1 (2026-05-27): OpenRouter spend recorded
- [ ] Day 2 (2026-05-28): OpenRouter spend recorded
- [ ] Day 3 (2026-05-29): OpenRouter spend recorded
- [ ] Day 4 (2026-05-30): OpenRouter spend recorded
- [ ] Day 5 (2026-05-31): OpenRouter spend recorded
- [ ] Day 6 (2026-06-01): OpenRouter spend recorded
- [ ] Day 7 (2026-06-02): OpenRouter spend recorded
- [ ] Day 7 (2026-06-03): Final validation report

### Success Criteria
- [ ] 60-70% cost reduction vs. baseline
- [ ] Zero context crashes
- [ ] 100% heartbeat success rate
- [ ] No gateway instability

---

## ⏳ TICKET-08: Documentation Task Routing (Pending)

**Status:** Blocked  
**Assignee:** Testbed  
**Blocked by:** Bob model verification

### Scope
- Add `claude-haiku-4.5` to fallback chain
- Document manual model selection for docs/GitHub tasks
- Update HOW.md with documentation routing

### Blockers
- Bob needs to confirm `claude-haiku-4.5` is in OpenRouter allowlist
- Gateway model list not showing new models yet

### When Unblocked
```json
{
  "agents": {
    "defaults": {
      "model": {
        "fallbacks": [
          "openrouter/anthropic/claude-haiku-4.5",
          "openrouter/meta-llama/llama-3.3-70b-instruct:free"
        ]
      }
    }
  }
}
```

---

## ⏳ TICKET-09: Bob Deployment (Pending)

**Status:** Not Started  
**Assignee:** Bob the Builder  
**Dependencies:** TICKET-07 (7-day validation)

### Scope
- Wait for Testbed 7-day validation to pass
- Apply same changes to Bob's machine
- Validate GitHub Copilot model routing
- Monitor 7 days

### Prerequisites
- [ ] Testbed validation report shows success
- [ ] GitHub Copilot model strings verified
- [ ] Bob's baseline spend documented

---

## ⏳ TICKET-10: Mason/Forge Deployment (Pending)

**Status:** Not Started  
**Assignee:** TBD  
**Dependencies:** TICKET-09 (Bob validation)

### Scope
- Wait for Bob 7-day validation to pass
- Apply changes to Mason and Forge in parallel
- Monitor 7 days each
- Document final results

---

## 🚫 TICKET-11: OpenRouter Model List Update (Issue)

**Status:** Open Issue  
**Assignee:** Bob the Builder  
**Opened:** 2026-05-27

### Issue
Gateway not showing new models added to OpenRouter allowlist:
- Missing: `haiku-4.5`, `gpt-5-mini`, `gemma`, `gpt-oss`, `nemotron`
- Only visible: `sonnet-4-5`, `llama-3.3-70b:free`

### Action Needed
1. Bob verify models were added via OpenRouter management API
2. Check OpenRouter account settings
3. Wait for API sync (5-10 minutes)
4. Restart gateway: `openclaw gateway restart`

### Impact
Blocks TICKET-08 (documentation task routing)

---

## Decisions Log

| Decision | Date | Who | Rationale |
|----------|------|-----|-----------|
| Use free models for automation | 2026-05-27 | Pieter | Immediate cost reduction |
| Proceed with 2 models only | 2026-05-27 | Pieter | Don't wait for OpenRouter sync |
| Testbed deployment first | 2026-05-27 | Pieter | Cost urgency + safe test environment |
| 7-day validation required | 2026-05-27 | Testbed | Catch issues before production rollout |
| Documentation uses Haiku | 2026-05-27 | Testbed | Quality writing at low cost (pending) |

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| Free model quality degradation | Medium | Low | Monitor logs, rollback ready | 🕐 Monitoring |
| Context crashes from low floor | Low | Medium | 20k buffer tested previously | ✅ Mitigated |
| Gateway instability | Low | Low | Config validated, backups ready | ✅ Mitigated |
| OpenRouter model sync delay | High | Low | Proceed with available models | ✅ Accepted |
| Cost increase instead of decrease | Low | High | Daily monitoring, rollback ready | 🕐 Monitoring |

---

## Timeline Summary

```
2026-05-27 (Day 0)
├── 10:00 - Model selection (TICKET-01)
├── 12:00 - Bob critique (TICKET-02)
├── 14:00 - Unified analysis (TICKET-03)
├── 16:39 - Pre-flight backups (TICKET-04)
├── 17:30 - Config changes applied (TICKET-05)
├── 17:45 - Validation complete (TICKET-06)
└── 19:45 - Documentation created (current)

2026-05-28 to 2026-06-02
└── Daily monitoring (TICKET-07)

2026-06-03 (Day 7)
└── Validation report + Bob deployment decision

TBD
├── Bob deployment (TICKET-09)
└── Mason/Forge deployment (TICKET-10)
```

---

**Total tickets:** 11 (6 complete, 1 in progress, 3 pending, 1 blocked/issue)
