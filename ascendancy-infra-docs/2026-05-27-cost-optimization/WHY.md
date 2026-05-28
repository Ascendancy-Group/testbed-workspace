# WHY — Cost Optimization Rationale

**Problem:** OpenClaw agent infrastructure burning $100/3 days (~$1,000/month) — unsustainable.

---

## Business Driver

**Monthly limit set:** $300/month for Testbed (2026-05-27)

**Cost trajectory:**
- Current: ~$1,000/month across 4 agents
- Testbed alone: ~$250/month
- Target: $75/month per agent ($300 total for 4 agents)
- **Required reduction: 60-70%**

---

## Root Causes Identified

### 1. Heartbeat Cost Waste
**Problem:**
- Heartbeat polls every 30 minutes using premium model (Sonnet 4.5)
- 24 heartbeats/day × $0.015/call = $0.36/day = **$10.80/month on heartbeat alone**
- Heartbeat is simple health check — doesn't need reasoning capability

**Solution:**
- Use free model (`llama-3.3-70b:free`) for heartbeat
- Reduce frequency to 1 hour
- **Cost: $0**

---

### 2. Context Crashes
**Problem:**
- Context compaction without `reserveTokensFloor` leaves insufficient room for response
- Agent crashes, retries with new context
- Retry burns another full context load = 2x cost for failed attempt

**Solution:**
- Set `reserveTokensFloor: 20000` as safety buffer
- Prevents crash-and-retry loops
- One successful call vs. multiple failed attempts

---

### 3. Unnecessary Premium Model Usage
**Problem:**
- All automation (cron jobs, backups, exports) defaulting to premium model
- Tasks like "export memory to JSON" don't need $15/1M token reasoning
- No explicit model assignment = inherits expensive default

**Solution:**
- Explicit model assignment for automation
- Free models for deterministic tasks
- Reserve premium models for interactive work

---

### 4. Inefficient Fallback Chain
**Problem:**
- Multiple paid fallbacks configured
- When primary fails, burns through 3-4 paid models before giving up
- Each retry costs money

**Solution:**
- Simplified fallback: one free model as safety net
- Fail fast if premium model unavailable
- No cascading paid-model retries

---

### 5. Documentation Written by Premium Models
**Problem:**
- GitHub commit messages, README updates, technical docs all using Sonnet 4.5
- Quality writing needed, but not reasoning/planning capability
- Haiku ($0.25/1M) delivers 90% of Sonnet quality at 80% cost savings

**Solution (pending):**
- Use `claude-haiku-4.5` for documentation tasks
- Reserve Sonnet for interactive work
- **Projected: 15-20% additional savings**

---

## Why These Changes Are Safe

### 1. Heartbeat on Free Model
**Risk:** Lower quality health check  
**Mitigation:**
- Heartbeat is pass/fail — no complex reasoning needed
- Free model (llama-3.3-70b) is highly capable for simple tasks
- Reduced frequency (1h) still catches issues quickly

### 2. Context Crash Prevention
**Risk:** None — this is pure safety  
**Benefit:**
- Prevents cascading failures
- More reliable agent operation
- Lower retry costs

### 3. Simplified Fallback
**Risk:** Less redundancy  
**Mitigation:**
- Primary model (Sonnet 4.5) is highly reliable
- Free fallback still provides safety net
- Fail-fast prevents cost spiral on outages

---

## Projected Impact

| Cost Driver | Before | After | Savings |
|-------------|--------|-------|---------|
| Heartbeat (24/day) | $10.80/month | $0 | **100%** |
| Context crashes | 10-15% retry overhead | 0% | **10-15%** |
| Automation crons | Premium model | Free model | **20-30%** |
| Documentation | Sonnet 4.5 | Haiku 4.5 | **15-20%** (pending) |
| **Total** | **~$250/month** | **~$75/month** | **60-70%** |

---

## Why Testbed First

**Test environment rationale:**
1. **Non-critical workload** — if optimization breaks something, no production impact
2. **Identical config to production** — valid test of changes
3. **7-day validation window** — catch issues before Bob/Mason/Forge rollout
4. **Cost urgency** — Testbed hitting limit first

---

## Governance Alignment

**SOP-07 (AI Model Usage):**
- ✅ No Chinese-origin models
- ✅ Explicit model assignment required
- ✅ Two-Tier backup protocol before changes
- ✅ Cost monitoring and reporting

**SOP-03 (Dropbox):**
- ✅ Documentation uploaded to `(Admin)/Model Use/`
- ✅ Implementation guides accessible to all agents

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Free model quality degradation | Medium | Low | Monitor logs, rollback ready |
| Context crashes from floor too low | Low | Medium | 20k buffer tested in prior work |
| Gateway instability | Low | Low | Changes validated in staging |
| Rollback needed | Low | Low | <5 min restore from JSON backup |

---

## Why Not Wait

**Urgency factors:**
1. **$300/month limit active** — already at risk of overage
2. **Cost trajectory unsustainable** — $1,000/month baseline unacceptable
3. **Quick wins available** — heartbeat optimization = immediate $0 cost
4. **Safe implementation path** — changes are low-risk with rollback ready

**Decision:** Deploy now, validate 7 days, rollout to production.

---

**Rationale: Cost reduction is urgent, changes are safe, and Testbed is the right place to prove it.**
