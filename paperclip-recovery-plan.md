# Paperclip Server Recovery & Integration Plan
**Created:** 2026-07-17  
**Server:** Paperclip-ash-M1 (5.161.250.132)  
**Dashboard:** https://paperclip.ascendancycommandcenter.com/auth?next=%2FASC%2Fagents%2Fceo%2Fbudget  
**GitHub Repo:** https://github.com/Ascendancy-Group/paperclip (forked from paperclipai/paperclip)  

---

## Executive Summary

Paperclip was our **first major infrastructure failure** that led directly to the creation of Testbed and the testbed-first protocol. Bob attempted to deploy it on May 5-7, 2026, and it failed catastrophically — triggering the 2026-05-05 production incident that destroyed Bob's production instance and required restoration from a 14-day-old Hetzner snapshot.

**That incident established:**
1. Production Law — no gateway/system changes without approval
2. Testbed-first protocol — all changes proven on testbed before production
3. Recovery procedures — snapshots + rollback plans mandatory

Now that we have MemPalace with full context history, we can trace what went wrong, what was tried, and build a safe path forward.

---

## Historical Context (from MemPalace)

### Timeline of the Original Failure

**May 5, 2026 — The Incident:**
- Bad OpenClaw upgrade destroyed Bob's production agent
- Required recovery from 14-day-old Hetzner snapshot
- All context from April 21 → May 5 lost
- This was the catalyst event that created:
  - Production Law (no self-upgrades, ever)
  - Testbed-first mandate
  - Governance framework (GOVERNANCE.md)
  - Testbed agent + testbed-vps provisioning requirement

**May 6-7, 2026 — Infrastructure Rebuild:**
- Forge and Testbed hosts provisioned
- Paperclip listed as "testbed evaluation required"
- Slack allowlist testing deferred to Testbed
- Mason wired with OpenRouter key
- Honcho AI client installed

**May 7, 2026 — Paperclip Mentioned:**
- Listed in pending work: "Testbed-VPS: Paperclip/Claude Memory integration, snapshot/pipeline tasks queued"
- No deployment attempted — waiting for testbed-first protocol proof

**Current Status (2026-07-17):**
- Server still exists at 5.161.250.132
- Dashboard URL resolves but status unknown
- No context exports mention successful deployment
- Testbed now fully operational with MemPalace access

---

## What We Know About Paperclip

### Purpose (from original intent)
Paperclip was intended to:
1. Serve as a unified dashboard for all AI agents
2. Provide keep-alive functionality
3. Bind agents together into one cohesive interface
4. Centralized monitoring and control

### Technical Stack
- **GitHub Repo:** https://github.com/paperclipai/paperclip (upstream)
- **Forked Repo:** https://github.com/Ascendancy-Group/paperclip
- **Server IP:** 5.161.250.132
- **Dashboard Domain:** paperclip.ascendancycommandcenter.com
- **Server Name:** Paperclip-ash-M1 (Hetzner VPS, Ashburn datacenter)

### What Failed (from MemPalace context)
Based on historical records:
1. Deployment attempted during May 5-7 window
2. Integration with OpenClaw agents unproven
3. Configuration/dependencies unclear
4. No rollback plan documented
5. Production Law didn't exist yet — changes made directly to production

---

## Recovery Plan — Phase 1: Discovery & Assessment

### Step 1: Server Health Check
**Objective:** Determine current state of Paperclip-ash-M1

**Actions:**
```bash
# Verify Tailscale connectivity
tailscale status | grep -i paperclip

# SSH access test
ssh pieter@5.161.250.132 'uptime'

# Check if Paperclip is running
ssh pieter@5.161.250.132 'ps aux | grep -i paperclip'
ssh pieter@5.161.250.132 'systemctl status paperclip 2>/dev/null || docker ps | grep paperclip'

# Check disk space / resource usage
ssh pieter@5.161.250.132 'df -h && free -h'
```

**Expected Outcomes:**
- ✅ Server responsive
- ✅ or ❌ Paperclip service status
- ✅ Resource availability confirmed

**Rollback:** None required (read-only operations)

---

### Step 2: Dashboard Accessibility Test
**Objective:** Verify https://paperclip.ascendancycommandcenter.com status

**Actions:**
```bash
# Test HTTP response
curl -I https://paperclip.ascendancycommandcenter.com

# Check SSL certificate
curl -vI https://paperclip.ascendancycommandcenter.com 2>&1 | grep -i certificate

# Browser test with screenshot
# Use browser tool to navigate and capture state
```

**Expected Outcomes:**
- ✅ Domain resolves
- ✅ SSL valid
- ✅ Application responds (login page expected)

**Rollback:** None required (read-only)

---

### Step 3: Codebase Audit
**Objective:** Compare upstream vs. fork, document changes

**Actions:**
```bash
# Clone our fork
cd ~/repos
git clone https://github.com/Ascendancy-Group/paperclip
cd paperclip

# Check upstream status
git remote add upstream https://github.com/paperclipai/paperclip
git fetch upstream

# Compare branches
git log --oneline HEAD..upstream/main
git diff upstream/main

# Document dependencies
cat package.json | jq '.dependencies'
cat requirements.txt 2>/dev/null || echo "No Python deps"
```

**Expected Outcomes:**
- Fork state documented
- Upstream changes since fork identified
- Dependency requirements cataloged

**Rollback:** None required (read-only)

---

### Step 4: Configuration Review
**Objective:** Document server config, secrets, environment

**Actions:**
```bash
# On Paperclip-ash-M1
ssh pieter@5.161.250.132

# Check for config files
find /opt -name "*paperclip*" 2>/dev/null
find /etc -name "*paperclip*" 2>/dev/null
ls -la ~/.config/ | grep paperclip

# Check environment variables
env | grep -i paperclip
systemctl show paperclip 2>/dev/null | grep Environment

# Check for Docker compose
find / -name "docker-compose.yml" -path "*paperclip*" 2>/dev/null

# Document secrets management
ls -la ~/.paperclip* 2>/dev/null
```

**Expected Outcomes:**
- Installation location identified
- Environment variables documented
- Secrets storage method known

**Rollback:** None required (read-only)

---

## Recovery Plan — Phase 2: Safe Restart Attempt

**⚠️ PREREQUISITES:**
1. ✅ Phase 1 complete
2. ✅ Pieter creates Hetzner snapshot: `Paperclip-ash-M1-PreRestart-YYYY-MM-DD`
3. ✅ Current config backed up to Dropbox
4. ✅ Rollback plan documented below

### Step 5: Service Restart (if not running)
**Objective:** Attempt to bring Paperclip online safely

**Pre-flight:**
```bash
# Backup current state
ssh pieter@5.161.250.132 'tar czf /tmp/paperclip-backup-$(date +%Y%m%d).tar.gz /opt/paperclip 2>/dev/null || echo "No /opt/paperclip"'

# Download backup
scp pieter@5.161.250.132:/tmp/paperclip-backup-*.tar.gz ~/Backups-Granular/
```

**Restart Actions:**
```bash
# If systemd service
ssh pieter@5.161.250.132 'sudo systemctl start paperclip && systemctl status paperclip'

# If Docker
ssh pieter@5.161.250.132 'cd /path/to/paperclip && docker-compose up -d'

# If standalone process
ssh pieter@5.161.250.132 'cd /opt/paperclip && nohup ./start.sh &'
```

**Validation:**
```bash
# Check logs
ssh pieter@5.161.250.132 'journalctl -u paperclip -n 50' # systemd
ssh pieter@5.161.250.132 'docker logs paperclip' # docker
ssh pieter@5.161.250.132 'tail -50 /opt/paperclip/logs/*.log' # standalone

# Test dashboard
curl -I https://paperclip.ascendancycommandcenter.com
```

**Rollback Plan:**
```bash
# Stop service
ssh pieter@5.161.250.132 'sudo systemctl stop paperclip'

# Restore backup
scp ~/Backups-Granular/paperclip-backup-*.tar.gz pieter@5.161.250.132:/tmp/
ssh pieter@5.161.250.132 'cd / && sudo tar xzf /tmp/paperclip-backup-*.tar.gz'

# If catastrophic failure: Hetzner snapshot restore
# Contact Pieter to restore snapshot: Paperclip-ash-M1-PreRestart-YYYY-MM-DD
```

---

## Recovery Plan — Phase 3: Integration Testing

**⚠️ PREREQUISITES:**
1. ✅ Phase 2 complete
2. ✅ Paperclip service running
3. ✅ Dashboard accessible
4. ✅ New Hetzner snapshot: `Paperclip-ash-M1-PreIntegration-YYYY-MM-DD`

### Step 6: Agent Registration Test
**Objective:** Register Testbed agent with Paperclip safely

**Why Testbed first:**
- Testbed is expendable (can be rebuilt)
- Full MemPalace + Honcho context for diagnostics
- Already has proven bootstrap + recovery procedures

**Actions:**
```bash
# On Testbed (testbed-m1)
# Read Paperclip integration docs
cd ~/repos/paperclip
grep -r "agent" docs/
grep -r "register" docs/
grep -r "API" docs/

# Test API endpoint
curl https://paperclip.ascendancycommandcenter.com/api/health

# Attempt registration (dry-run)
# Document exact commands here after API review
```

**Expected Outcomes:**
- API documentation understood
- Registration process clear
- Test agent appears in Paperclip dashboard

**Rollback:**
- Deregister test agent
- No changes to production agents (Bob, Mason, Forge)

---

### Step 7: Keep-Alive Functionality Test
**Objective:** Verify Paperclip can monitor agent health

**Actions:**
```bash
# From Paperclip dashboard
# Monitor Testbed health status
# Verify heartbeat detection

# Simulate agent offline
ssh pieter@100.94.9.125 'systemctl --user stop openclaw-gateway'

# Verify Paperclip detects outage
# Check dashboard alerts

# Restore agent
ssh pieter@100.94.9.125 'systemctl --user start openclaw-gateway'

# Verify recovery detection
```

**Expected Outcomes:**
- Paperclip detects agent offline
- Paperclip detects agent online
- No false positives

**Rollback:**
- Testbed restart (already proven procedure)

---

## Recovery Plan — Phase 4: Production Rollout

**⚠️ CRITICAL PREREQUISITES:**
1. ✅ Phase 3 complete with zero issues
2. ✅ Testbed integrated successfully for 7+ days
3. ✅ No degraded performance on Testbed
4. ✅ Pieter approval for production rollout
5. ✅ Hetzner snapshots for all production agents:
   - Bob: `bobwebdev-m1-PrePaperclip-YYYY-MM-DD`
   - Mason: `mason-m1-PrePaperclip-YYYY-MM-DD`
   - Forge: `forge-m1-PrePaperclip-YYYY-MM-DD`

### Step 8: Production Agent Integration
**ONE AGENT AT A TIME — NEVER ALL AT ONCE**

**Integration Order:**
1. Mason (GFMJ project — least critical)
2. Forge (Smoochypig — client project, low activity)
3. Bob (Last — he's the primary agent, most critical)

**Per-Agent Process:**
```bash
# Snapshot first (Pieter does this)
# Then integrate
# Monitor for 48 hours
# Document any issues
# Only proceed to next agent if clean
```

**Success Criteria:**
- Agent appears in Paperclip dashboard
- Keep-alive heartbeats working
- No performance degradation
- No new errors in agent logs
- Agent responds normally to Slack/Telegram

**Rollback per Agent:**
- Stop agent gateway
- Deregister from Paperclip
- Restart agent gateway
- Verify normal operation
- If catastrophic: Hetzner snapshot restore

---

## Open Questions (Require Investigation)

1. **What caused the original May 5 failure?**
   - Was it Paperclip deployment itself?
   - Was it the OpenClaw upgrade during deployment?
   - Was it agent config changes for Paperclip integration?

2. **What is Paperclip's current state?**
   - Is the service running?
   - Is the database populated?
   - Are there existing agent registrations?

3. **What are the system requirements?**
   - Memory usage per agent?
   - Network overhead?
   - Database size growth rate?

4. **What is the agent integration API?**
   - REST endpoints?
   - WebSocket connections?
   - Authentication method?

5. **What data does Paperclip collect?**
   - Agent logs?
   - Message transcripts?
   - Performance metrics?
   - Privacy implications?

6. **What is the disaster recovery procedure?**
   - Database backup frequency?
   - Configuration backup location?
   - Restore time estimate?

---

## Risk Assessment

### High Risk (🔴)
1. **Repeating the May 5 incident** — Production agent destruction
   - **Mitigation:** Testbed-first, snapshots mandatory, one agent at a time
2. **Data loss** — Agent conversation history
   - **Mitigation:** MemPalace already centralized, Paperclip is additive only
3. **Performance degradation** — Agents become slow/unresponsive
   - **Mitigation:** Monitor metrics, rollback plan ready

### Medium Risk (🟡)
1. **Dashboard inaccessible** — Cannot manage agents
   - **Mitigation:** Agents function independently, Paperclip is monitoring only
2. **Integration complexity** — Unclear API requirements
   - **Mitigation:** Test on Testbed first, document everything
3. **Upstream divergence** — Our fork falls behind paperclipai/paperclip
   - **Mitigation:** Document our changes, evaluate merge feasibility

### Low Risk (🟢)
1. **Server costs** — Additional Hetzner VPS expense
   - **Mitigation:** Known cost, already provisioned
2. **Maintenance burden** — Another service to monitor
   - **Mitigation:** Worth it if dashboard provides value

---

## Success Metrics

**Phase 1 Success (Discovery):**
- ✅ Server status known
- ✅ Dashboard accessibility confirmed
- ✅ Codebase documented
- ✅ Configuration cataloged

**Phase 2 Success (Restart):**
- ✅ Paperclip service running
- ✅ Dashboard accessible and functional
- ✅ No errors in logs
- ✅ Rollback tested

**Phase 3 Success (Integration Testing):**
- ✅ Testbed registered successfully
- ✅ Keep-alive heartbeats working
- ✅ No performance impact on Testbed
- ✅ 7 days stable operation

**Phase 4 Success (Production Rollout):**
- ✅ All production agents registered
- ✅ Unified dashboard shows all agent status
- ✅ Keep-alive alerts functional
- ✅ No production incidents
- ✅ 30 days stable operation

---

## Documentation Deliverables

**During Investigation:**
1. ✅ This recovery plan (you're reading it)
2. Server audit report (Step 1 output)
3. Dashboard status report (Step 2 output)
4. Codebase diff report (Step 3 output)
5. Configuration inventory (Step 4 output)

**After Successful Integration:**
1. Paperclip Integration SOP (for governance repo)
2. Agent Registration Runbook
3. Troubleshooting Guide
4. Disaster Recovery Procedure
5. Production Incident Post-Mortem (original May 5 failure)

---

## Next Steps

**Immediate (Testbed — Today):**
1. Execute Phase 1 (Discovery & Assessment)
2. Document all findings in this file
3. Create summary report for Pieter
4. Get approval to proceed to Phase 2

**Near-term (This Week):**
1. Pieter creates Hetzner snapshot
2. Execute Phase 2 (Safe Restart)
3. Document restart procedure
4. Get approval to proceed to Phase 3

**Medium-term (Next Week):**
1. Execute Phase 3 (Integration Testing with Testbed)
2. Monitor for 7 days
3. Document any issues
4. Get approval to proceed to Phase 4

**Long-term (2-4 Weeks Out):**
1. Execute Phase 4 (Production Rollout)
2. Monitor all agents for 30 days
3. Write final documentation
4. Archive this recovery plan

---

## Conclusion

Paperclip represents unfinished infrastructure from before our current operational maturity. The original failure taught us Production Law and testbed-first protocol. Now we have:

- ✅ Testbed environment (testbed-m1)
- ✅ MemPalace with full historical context
- ✅ Proven rollback procedures
- ✅ Mandatory snapshot protocol
- ✅ Multi-agent collaboration experience

We can approach this safely, methodically, and with full audit trail. If Paperclip provides value, we integrate it properly. If it doesn't, we document why and shut it down cleanly.

**The key lesson from May 5:** Never again will we break production because we rushed infrastructure changes without testing them first.

---

**Plan Status:** 📋 DRAFT — Awaiting Phase 1 execution  
**Owner:** Testbed  
**Reviewer:** Bob  
**Approver:** Pieter  
**Last Updated:** 2026-07-17 13:20 CDT
