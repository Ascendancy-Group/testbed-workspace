# Dropbox MCP v2.0 — Implementation Plan

**Owner:** Testbed (implementation) | **Manager:** Bob (review/approval)  
**Target:** `~/docker/dropbox-mcp/` on honcho-m1  
**Timeline:** 3-4 hours of focused work  
**Date:** 2026-05-28

---

## 🎯 Success Criteria

1. ✅ Python/FastMCP implementation replaces Node.js container
2. ✅ All 13 Dropbox tools fully implemented (no stubs)
3. ✅ Failure resistance: retry + circuit breaker + rate limiting
4. ✅ Zero-downtime migration (test on port 3002, cutover to 3001)
5. ✅ SOP-04 updated to reflect new architecture
6. ✅ All 5 agent machines verified against SOP-04 checklist

---

## 📋 Implementation Tickets

### **PHASE 1: PRE-FLIGHT (Blockers — Fix Before Coding)**

#### **TICKET-01: Architecture Document Corrections**
**Priority:** BLOCKER  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 30 min

**Tasks:**
- [ ] Fix port references: 8002 → 3001 everywhere
- [ ] Fix Redis section: remove Redis container, document use of existing `127.0.0.1:6379/1`
- [ ] Fix Step 15: correct `openclaw.json` key structure (`mcp.servers`, not `mcpServers`)
- [ ] Fix Step 16: change `openclaw gateway restart` → `oc-restart`
- [ ] Add Migration section (Node.js → Python zero-downtime swap)
- [ ] Update production checklist (remove SSL/TLS, update port)
- [ ] Upload corrected doc to Dropbox as `V2-FINAL-Robust-Dropbox-MCP-Architecture.md`

**Deliverable:** Corrected architecture doc ready for Bob's final sign-off

---

#### **TICKET-02: Bob Final Architecture Sign-Off**
**Priority:** BLOCKER  
**Owner:** Bob  
**Reviewer:** Pieter  
**Time:** 15 min

**Tasks:**
- [ ] Bob reviews `V2-FINAL-Robust-Dropbox-MCP-Architecture.md`
- [ ] Bob confirms all `[BOB-FIX-REQUIRED]` items addressed
- [ ] Bob marks document as **APPROVED** in Dropbox
- [ ] Pieter confirms Bob's approval

**Deliverable:** Architecture approved → green light for PHASE 2

---

### **PHASE 2: CORE IMPLEMENTATION**

#### **TICKET-03: Project Structure Setup**
**Priority:** HIGH  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 20 min

**Tasks:**
- [ ] Create `~/docker/dropbox-mcp/` directory structure (per architecture doc)
- [ ] Write `requirements.txt` with pinned versions (not `>=`)
- [ ] Write `pyproject.toml`
- [ ] Create all subdirectories: `src/`, `src/tools/`, `src/middleware/`, `src/monitoring/`, `tests/`, `docs/`
- [ ] Add `__init__.py` files
- [ ] Create `.env.example` (NO real credentials)

**Deliverable:** Clean project structure ready for code

---

#### **TICKET-04: Config & Token Management**
**Priority:** HIGH  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 30 min

**Tasks:**
- [ ] Implement `src/config.py` with Pydantic `Settings`
- [ ] Remove `access_token` param (Bob's constructor fix)
- [ ] Implement `src/utils/token_manager.py` (explicit refresh logic)
- [ ] Add 1Password integration (`op run` pattern)
- [ ] Test token refresh flow

**Deliverable:** Config validated, tokens refreshing correctly

---

#### **TICKET-05: Dropbox Client Core**
**Priority:** HIGH  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 45 min

**Tasks:**
- [ ] Implement `src/dropbox_client.py`
- [ ] Fix constructor: remove `access_token`, use `app_key + app_secret + refresh_token`
- [ ] Add `import os` (Bob's fix)
- [ ] Implement retry decorator (Tenacity)
- [ ] Implement circuit breaker (Pybreaker)
- [ ] Add Prometheus metrics (Counter, Histogram)
- [ ] Fix `cursor` serialization (`str()` cast)
- [ ] Implement `list_folder` method
- [ ] Implement `upload_file` method with chunking

**Deliverable:** Core client with retry, circuit breaker, metrics working

---

#### **TICKET-06: All 13 Dropbox Tools Implementation**
**Priority:** BLOCKER  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 2 hours

**Tasks:**
- [ ] Implement HIGH priority tools (6 tools):
  - [ ] `list_folder` (pagination support)
  - [ ] `search_files` (full-text + filename)
  - [ ] `download_file` (streaming)
  - [ ] `upload_file` (chunked for large files)
  - [ ] `create_shared_link` (public/expiring)
  - [ ] `get_metadata` (file/folder info)
- [ ] Implement MEDIUM priority tools (5 tools):
  - [ ] `create_folder`
  - [ ] `move_file` (rename support)
  - [ ] `delete_file` (trash option)
  - [ ] `list_revisions`
  - [ ] `restore_revision`
- [ ] Implement LOW priority tools (2 tools):
  - [ ] `copy_file`
  - [ ] `get_account_info`
- [ ] Each tool: docstring, logging, error handling, metrics
- [ ] Write tests in `tests/test_tools.py` (85% coverage target)

**Deliverable:** All 13 tools fully implemented, tested, no stubs

---

#### **TICKET-07: FastMCP Server & API Key Auth**
**Priority:** BLOCKER  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 1 hour

**Tasks:**
- [ ] Implement `src/main.py` with FastMCP server
- [ ] Register all 13 tools (no `# Add 8 more tools` comments)
- [ ] Implement API key auth middleware (`X-Api-Key` header validation)
- [ ] Key source: `1Password AgentStack/Ascendancy MCP API Key`
- [ ] Fix `mcp.run()` call: bind to `0.0.0.0:3001` explicitly
- [ ] Test auth: valid key → 200, invalid key → 401
- [ ] Add Prometheus `/metrics` endpoint on port 9090

**Deliverable:** FastMCP server running on port 3001 with auth working

---

#### **TICKET-08: Middleware & Monitoring**
**Priority:** MEDIUM  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 45 min

**Tasks:**
- [ ] Implement `src/middleware/retry.py` (Tenacity decorators)
- [ ] Implement `src/middleware/circuit_breaker.py` (Pybreaker integration)
- [ ] Implement `src/middleware/rate_limiter.py` (Redis-based)
- [ ] Implement `src/monitoring/metrics.py` (Prometheus collectors)
- [ ] Implement `src/monitoring/logging.py` (Structlog config)
- [ ] Test circuit breaker: 5 failures → open state
- [ ] Test rate limiter: exceed quota → 429 response

**Deliverable:** Middleware working, metrics exposed, logs structured

---

### **PHASE 3: DOCKER & DEPLOYMENT**

#### **TICKET-09: Dockerfile & docker-compose**
**Priority:** HIGH  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 30 min

**Tasks:**
- [ ] Write `Dockerfile` (Python 3.12, multi-stage if possible)
- [ ] Write `docker-compose.yml`:
  - [ ] Port: `3001:3001` (not 8002)
  - [ ] Metrics port: `9090:9090`
  - [ ] Redis: use existing `127.0.0.1:6379/1` (NO separate container)
  - [ ] Environment: inject via `op run --env-file=deploy/.env.tpl`
  - [ ] Health check endpoint
- [ ] Write `deploy/.env.tpl` (template with 1Password refs, NO real creds)
- [ ] Test build: `docker build -t dropbox-mcp-v2:latest .`

**Deliverable:** Docker image builds successfully

---

#### **TICKET-10: Local Testing (Port 3002)**
**Priority:** BLOCKER  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 45 min

**Tasks:**
- [ ] Start container on temp port 3002 for testing
- [ ] Run verification checklist:
  - [ ] Health check: `curl http://100.77.0.47:3002/health`
  - [ ] Auth test: valid key → success, invalid → 401
  - [ ] Tool test: `list_folder` on root path
  - [ ] Upload test: small file (< 4MB)
  - [ ] Upload test: large file (> 10MB, chunked)
  - [ ] Download test
  - [ ] Search test
  - [ ] Circuit breaker: force 5 failures, verify open state
  - [ ] Metrics: `curl http://100.77.0.47:9090/metrics`
- [ ] Log all results in `tests/VERIFICATION-RESULTS.md`

**Deliverable:** All tests passing on port 3002

---

#### **TICKET-11: Zero-Downtime Migration (Node.js → Python)**
**Priority:** BLOCKER  
**Owner:** Testbed  
**Reviewer:** Bob  
**Approval:** Pieter  
**Time:** 30 min

**Pre-flight:**
- [ ] Testbed posts migration plan in #testing-env
- [ ] Bob reviews plan
- [ ] Pieter approves cutover

**Cutover steps:**
1. [ ] Stop old Node.js container: `docker stop dropbox-mcp`
2. [ ] Rename old container: `docker rename dropbox-mcp dropbox-mcp-old-nodejs`
3. [ ] Start new Python container on port 3001: `docker-compose up -d`
4. [ ] Health check: `curl http://100.77.0.47:3001/health`
5. [ ] Run SOP-04 verification from any agent machine
6. [ ] If all pass → remove old container: `docker rm dropbox-mcp-old-nodejs`
7. [ ] If any fail → rollback: stop new, start old, investigate

**Deliverable:** Python container live on port 3001, all agents verified

---

### **PHASE 4: DOCUMENTATION & FINALIZATION**

#### **TICKET-12: SOP-04 Update**
**Priority:** HIGH  
**Owner:** Testbed (using Haiku model for cost efficiency)  
**Reviewer:** Bob  
**Approval:** Pieter  
**Time:** 1 hour

**Tasks:**
- [ ] Update `ascendancy-governance/playbook/sops/04-dropbox.md`:
  - [ ] Replace all Node.js references with Python/FastMCP
  - [ ] Update docker-compose commands
  - [ ] Fix `openclaw.json` key structure (Step 15 fix)
  - [ ] Fix gateway restart command (Step 16 → `oc-restart`)
  - [ ] Add Redis reuse pattern (existing Honcho Redis, DB 1)
  - [ ] Add migration notes for future rebuilds
  - [ ] Update architecture diagram
- [ ] Commit to governance repo with message: `SOP-04: Update for Dropbox MCP v2.0 (Python/FastMCP)`
- [ ] Push to GitHub
- [ ] Announce in #testing-env

**Deliverable:** SOP-04 matches reality, ready for agent use

---

#### **TICKET-13: Agent Verification (All 5 Machines)**
**Priority:** HIGH  
**Owner:** Bob (coordinates) + all agents  
**Time:** 30 min per agent

**Agents to verify:**
- [ ] bobwebdev-m1 (Bob)
- [ ] mason-m1 (Mason)
- [ ] forge-m1 (Forge)
- [ ] testbed-m1 (Testbed)
- [ ] honcho-m1 (MCP host, N/A but verify from Bob's machine)

**Verification steps (per SOP-04 checklist):**
1. [ ] `tailscale status | grep honcho` → shows 100.77.0.47 active
2. [ ] `curl` to MCP endpoint → returns `event: endpoint`
3. [ ] `openclaw.json` has correct `mcp.servers.dropbox` structure
4. [ ] Python helper test (SOP-04 Step 4) → lists Dropbox folders
5. [ ] Mark agent row in SOP-04 status table as ✅

**Deliverable:** All 5 agents verified, SOP-04 table updated

---

#### **TICKET-14: Cleanup & Final Documentation**
**Priority:** MEDIUM  
**Owner:** Testbed  
**Reviewer:** Bob  
**Time:** 30 min

**Tasks:**
- [ ] Write `docs/SETUP.md` (honest 50-step guide)
- [ ] Write `docs/DEPLOYMENT.md` (production deployment)
- [ ] Write `docs/TROUBLESHOOTING.md` (common issues)
- [ ] Update `README.md` in `~/docker/dropbox-mcp/`
- [ ] Disable/remove dead systemd service (`ascendancy-dropbox-mcp`)
- [ ] Archive old Node.js source: leave `~/ascendancy-mcp-servers/dropbox-mcp/` as historical reference
- [ ] Upload all docs to Dropbox `(Admin)/Dropbox MCP/v2.0/`

**Deliverable:** Complete documentation set

---

## 📊 Timeline Summary

| Phase | Tickets | Est. Time | Dependencies |
|---|---|---|---|
| PHASE 1: Pre-Flight | TICKET-01, TICKET-02 | 45 min | None |
| PHASE 2: Core Implementation | TICKET-03 to TICKET-08 | 5.5 hours | TICKET-02 approved |
| PHASE 3: Docker & Deployment | TICKET-09 to TICKET-11 | 1.75 hours | TICKET-08 complete |
| PHASE 4: Documentation | TICKET-12 to TICKET-14 | 2 hours | TICKET-11 complete |
| **TOTAL** | 14 tickets | **~10 hours** | Sequential |

**Realistic timeline:** 2 work sessions (1 day for focused work, 1 day for verification/docs)

---

## 🚦 Gate Checks

**Cannot proceed to PHASE 2 without:**
- ✅ TICKET-02: Bob's architecture approval

**Cannot proceed to PHASE 3 without:**
- ✅ TICKET-06: All 13 tools implemented
- ✅ TICKET-07: FastMCP server + auth working

**Cannot proceed to PHASE 4 without:**
- ✅ TICKET-10: All tests passing on port 3002
- ✅ TICKET-11: Cutover complete, agents verified

**Cannot close project without:**
- ✅ TICKET-12: SOP-04 updated
- ✅ TICKET-13: All 5 agents verified

---

## 🎯 Acceptance Criteria (Final Sign-Off)

Bob approves when:
1. All 14 tickets marked complete
2. All 5 agents pass SOP-04 verification
3. Zero production incidents during cutover
4. SOP-04 matches deployed reality
5. Monitoring metrics visible and correct

Pieter approves when:
1. Bob's approval confirmed
2. Cost efficiency proven (no unnecessary containers/services)
3. Failure resistance demonstrated (circuit breaker test)
4. Documentation complete and agent-usable

---

**Next Step:** Testbed implements TICKET-01 (architecture corrections), uploads to Dropbox, waits for Bob's TICKET-02 approval before starting PHASE 2.

---

_Implementation plan created: 2026-05-28 | Owner: Testbed | Manager: Bob_
