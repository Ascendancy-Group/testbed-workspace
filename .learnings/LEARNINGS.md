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

## [LRN-20260615-002] best_practice

**Logged**: 2026-06-15T18:56:00Z
**Priority**: high
**Status**: resolved
**Area**: infra

### Summary
1Password access = gateway to all other systems

### Details
**What I learned:**
When bootstrap Step 1 validates 1Password access (`op vault list` succeeds), that means:
1. ✅ All secrets in AgentStack vault are accessible
2. ✅ SSH keys can be retrieved (if stored in vault)
3. ✅ API keys (Dropbox MCP, OpenRouter, etc.) can be retrieved
4. ✅ Can diagnose other systems by pulling credentials

**Key insight from Pieter:**
"if you have validated you have 1PW access.........then you also have access to the SSH keys Inclusive to Honcho-M1"

**What I did wrong initially:**
- 1Password validated → stopped at "SSH permission denied"
- Didn't realize 1PW access = can retrieve SSH keys
- Should have continued: pull SSH key from 1PW → test honcho-m1 access

**What I did right after correction:**
1. Read SOP-04 (Dropbox) from governance repo
2. Found correct health endpoint: port 9090 (not 3001)
3. Verified Dropbox MCP health: ✅ healthy
4. Verified MCP config in openclaw.json: ✅ correct
5. Tested MCP endpoint directly: ✅ responding

**Root cause of circuit breaker:**
- Not server failure
- Not config issue
- MCP client circuit breaker tripped after rapid retries (expected behavior)

### Suggested Action
1. ✅ Update BOOTSTRAP.md Step 1.5 to test correct Dropbox health port (9090)
2. ✅ Document: 1Password access = foundation for all other troubleshooting
3. ✅ Promote to AGENTS.md: "1PW validated → you have access to everything else"

### Metadata
- Source: user_feedback + governance_docs
- Related Files: BOOTSTRAP.md, SOP-04 (~/repos/ascendancy-governance/playbook/sops/04-dropbox.md)
- Tags: bootstrap, 1password, troubleshooting, dropbox, foundation
- See Also: LRN-20260615-001
- Pattern-Key: troubleshooting.foundation_access

---
