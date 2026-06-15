# Learnings

Corrections, insights, and knowledge gaps captured during development.

**Categories**: correction | insight | knowledge_gap | best_practice

---

## [LRN-20260615-001] correction

**Logged**: 2026-06-15T18:34:00Z
**Priority**: critical
**Status**: pending
**Area**: infra

### Summary
Never trust automated checks alone — always verify API access independently

### Details
**What happened:**
- Bootstrap Step 1 (`daily-checks.py`) reported "Dropbox Write Test... ✅"
- User (Pieter) asked me to upload files to Dropbox
- Dropbox MCP circuit breaker tripped immediately — upload failed
- I claimed bootstrap "passed" but never verified Dropbox access independently

**What was wrong:**
- Trusted script output without manual verification
- `daily-checks.py` likely tests a different path than OpenClaw MCP client
- False positive: automated check passed, but actual API usage failed

**What's correct:**
- Automated checks are a first pass, not final verification
- Critical APIs (1Password, Dropbox) must be tested manually via direct calls
- Bootstrap should STOP if manual verification fails

**User correction:**
Pieter: "keep me honest, you could or could not upload to Dropbox"
Pieter: "that is the intent of bootstrap- yes there should be a hard rule to that and the access via API"

### Suggested Action
1. ✅ Add Step 1.5 to BOOTSTRAP.md: "Independent API Verification"
   - 1Password: `op vault list`
   - Dropbox: `curl http://100.77.0.47:3001/health` or direct MCP test
2. ✅ Hard rule: If either fails → STOP, document, alert Pieter
3. ⚠️ Current issue: Dropbox MCP health endpoint returns "Not Found"
4. ⚠️ Cannot SSH to honcho-m1 to diagnose (publickey auth required)

### Metadata
- Source: user_feedback
- Related Files: BOOTSTRAP.md, daily-checks.py
- Tags: bootstrap, api-verification, dropbox, false-positive
- See Also: (future entries on API testing)
- Pattern-Key: testing.false_positive

---
