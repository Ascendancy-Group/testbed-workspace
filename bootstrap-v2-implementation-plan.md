# Bootstrap v2 Implementation Plan for Bob

**Created:** 2026-06-10  
**For:** Bob (BobWebDev)  
**By:** Testbed  
**Approved by:** Pieter van der Wal

---

## Overview

This document guides Bob through deploying bootstrap v2 to himself, then Mason, then Forge.

**What bootstrap v2 is:**
- Single-wrapper startup procedure (`BOOTSTRAP.md`)
- Automated verification script (`daily-checks.py`)
- Replaces fragmented startup procedures with one comprehensive checklist

**What it proves:**
- 1Password access (read real secrets by UUID)
- GitHub access (PAT from 1PW + repo validation)
- Dropbox access (direct API via 1PW credentials, SOP-04 method)
  - **Note:** Bootstrap uses direct Dropbox API to test foundation
  - MCP tools remain available for day-to-day file operations
- Governance repo sync
- Bootstrap size limits
- Config limits present
- Gateway health

---

## Prerequisites

Before you start, verify these exist on your machine:

1. **1Password CLI installed:** `op --version`
2. **GitHub CLI installed:** `gh --version`
3. **Dropbox MCP server running** on honcho-m1: `curl http://100.77.0.47:3001/health`
4. **Governance repo cloned:** `~/repos/ascendancy-governance`
5. **Scripts directory exists:** `~/scripts/`
6. **Workspace repo current:** `~/.openclaw/workspace/`

If any are missing, stop and resolve before proceeding.

---

## Deployment Steps

### Phase 1: Deploy to Bob (Self)

#### Step 1: Pull Files from Governance Repo

```bash
cd ~/repos/ascendancy-governance
git pull

# Copy bootstrap files to your workspace
cp ~/repos/ascendancy-governance/playbook/BOOTSTRAP.md ~/.openclaw/workspace/
mkdir -p ~/scripts
cp ~/repos/ascendancy-governance/playbook/scripts/daily-checks.py ~/scripts/
cp ~/repos/ascendancy-governance/playbook/daily-checks.yaml ~/.openclaw/
chmod +x ~/scripts/daily-checks.py
```

**Verify files copied:**
```bash
ls -lh ~/.openclaw/workspace/BOOTSTRAP.md
ls -lh ~/scripts/daily-checks.py
```

---

#### Step 2: Update Your AGENTS.md

Add this section to `~/.openclaw/workspace/AGENTS.md` (replace any existing "FIRST THING EVERY SESSION" section):

```markdown
## FIRST THING EVERY SESSION — Non-negotiable (Bootstrap v2)

Before anything else:

1. **Read and execute BOOTSTRAP.md completely**
   - Every step, in order
   - Do not skip, shortcut, or assume
   - If any step fails, STOP and resolve before proceeding

2. **BOOTSTRAP.md is your session startup checklist**
   - Contains all startup procedures
   - Includes automated checks (Step 1)
   - Includes manual verification steps (Steps 2-8)

3. **If bootstrap fails:**
   - Do NOT proceed with any work
   - Alert Pieter immediately
   - Document failure in daily note
   - Re-run bootstrap after resolving issue

**This rule cannot be bypassed. Every session. No exceptions.**
```

**Commit the change:**
```bash
cd ~/.openclaw/workspace
git add AGENTS.md BOOTSTRAP.md
git commit -m "bootstrap: v2 single-wrapper deployment"
git push
```

---

#### Step 3: Test the Automated Checks Script

Run the script to verify it works on your machine:

```bash
python3 ~/scripts/daily-checks.py
```

**Expected output:**
```
=== Daily Start Checks v2: bob ===
Date: 2026-06-10 11:XX:XX

1Password Health... ✅
Dropbox MCP... ✅
GitHub Access... ✅
Governance Sync... ✅
Bootstrap Size... ✅
Config Limits Present... ✅
Gateway Health... ✅
Personality Self-Test... ✅

✅ All required checks passed
```

**If ANY check fails:**
- Read the error message
- Fix the issue (missing path, wrong permissions, service down, etc.)
- Re-run the script
- Do NOT proceed until all checks pass

**Common fixes:**
- **1Password fails:** Run `op signin` or `eval $(op signin)`
- **Dropbox MCP fails:** Check `curl http://100.77.0.47:3001/health` — if down, alert Pieter
- **GitHub fails:** Verify PAT exists in 1Password vault `AgentStack` with correct UUID
- **Governance sync fails:** Check network, verify repo path `~/repos/ascendancy-governance`
- **Bootstrap size fails:** Archive old content in `MEMORY.md`
- **Config limits fails:** Check `openclaw.json` has `bootstrapMaxChars` and `bootstrapTotalMaxChars`

---

#### Step 4: Run Full Bootstrap Procedure

**Read the full procedure:**
```bash
cat ~/.openclaw/workspace/BOOTSTRAP.md
```

**Execute each step in order:**

1. Run `python3 ~/scripts/daily-checks.py` ✅ (already done in Step 3)
2. Identity verification: confirm who you are from `SOUL.md`
3. Workspace state: `git status`, `git pull`, check for uncommitted changes
4. Gateway health: `openclaw gateway status`, check logs
5. Memory sources: pull Honcho context, read `HANDOFF.md`, create today's daily note
6. Governance: read `GOVERNANCE.md`, check recent commits
7. Project context: (if applicable to your role)
8. Announce ready: "✅ Bootstrap complete. All systems verified. Ready."

**Document results:**
```bash
TODAY=$(TZ=America/Chicago date +%Y-%m-%d)
echo "## Bootstrap v2 First Run — $TODAY" >> ~/.openclaw/workspace/memory/${TODAY}.md
echo "" >> ~/.openclaw/workspace/memory/${TODAY}.md
echo "✅ All steps completed successfully" >> ~/.openclaw/workspace/memory/${TODAY}.md
echo "- Automated checks: PASS" >> ~/.openclaw/workspace/memory/${TODAY}.md
echo "- Manual steps 2-8: PASS" >> ~/.openclaw/workspace/memory/${TODAY}.md
echo "" >> ~/.openclaw/workspace/memory/${TODAY}.md
```

---

#### Step 5: Report Back to Pieter

Post in `#testing-env`:

```
@Pieter — Bob bootstrap v2 deployment complete ✅

Automated checks: PASS
Full bootstrap run: PASS
Files committed to bob-workspace repo

Ready to deploy to Mason next.
```

**Wait for Pieter's approval before proceeding to Phase 2.**

---

### Phase 2: Deploy to Mason

#### Step 1: SSH into Mason's Machine

```bash
ssh pieter@mason-m1
```

#### Step 2: Pull Files from Governance Repo

```bash
cd ~/repos/ascendancy-governance
git pull

# Copy bootstrap files
cp ~/repos/ascendancy-governance/playbook/BOOTSTRAP.md ~/.openclaw/workspace/
mkdir -p ~/scripts
cp ~/repos/ascendancy-governance/playbook/scripts/daily-checks.py ~/scripts/
cp ~/repos/ascendancy-governance/playbook/daily-checks.yaml ~/.openclaw/
chmod +x ~/scripts/daily-checks.py
```

#### Step 3: Update Mason's AGENTS.md

Edit `~/.openclaw/workspace/AGENTS.md` and add the bootstrap v2 hard rule (same text as Bob's).

**Commit:**
```bash
cd ~/.openclaw/workspace
git add AGENTS.md BOOTSTRAP.md
git commit -m "bootstrap: v2 single-wrapper deployment"
git push
```

#### Step 4: Test Automated Checks

```bash
python3 ~/scripts/daily-checks.py
```

If all checks pass ✅, Mason is ready.

If any fail, resolve before proceeding.

#### Step 5: Exit SSH

```bash
exit
```

#### Step 6: Report Back

Post in `#testing-env`:

```
@Pieter — Mason bootstrap v2 deployment complete ✅

Automated checks: PASS
Files committed to mason-workspace repo

Ready to deploy to Forge next.
```

**Wait for Pieter's approval before proceeding to Phase 3.**

---

### Phase 3: Deploy to Forge

Repeat Phase 2 steps for Forge:

1. SSH into `forge-m1`
2. Pull files from testbed workspace repo
3. Update `AGENTS.md`
4. Commit changes
5. Test automated checks
6. Exit SSH
7. Report back to Pieter

---

## Rollback Plan

If bootstrap v2 causes issues:

### Quick Rollback (Per Machine)

1. Restore Hetzner snapshot: `Pre-Bootstrap.md-implementation-06-09-2026`
2. Alert Pieter and Testbed
3. Document what failed in `#testing-env`

### Selective Rollback (Keep Files, Remove Hard Rule)

1. Remove bootstrap v2 hard rule from `AGENTS.md`
2. Keep `BOOTSTRAP.md` and `daily-checks.py` as optional reference
3. Commit: `git commit -m "bootstrap: v2 rollback — hard rule removed"`
4. Push: `git push`

---

## Success Criteria

Bootstrap v2 deployment is successful when:

✅ `BOOTSTRAP.md` exists in `~/.openclaw/workspace/`  
✅ `daily-checks.py` exists in `~/scripts/` with execute permissions  
✅ `AGENTS.md` contains bootstrap v2 hard rule  
✅ All automated checks pass on first run  
✅ Full bootstrap procedure completes without errors  
✅ Changes committed and pushed to workspace repo  
✅ Agent reports "Bootstrap complete" on next session startup

---

## Timeline

**Phase 1 (Bob):** 30 minutes  
**Phase 2 (Mason):** 15 minutes  
**Phase 3 (Forge):** 15 minutes  

**Total estimated time:** 1 hour

---

## Questions or Issues

If you encounter any blockers:

1. Document the exact error message
2. Post in `#testing-env` with context
3. Tag @Testbed and @Pieter
4. Do NOT proceed until resolved

---

## References

- **Governance repo (source of truth):** https://github.com/Ascendancy-Group/ascendancy-governance
- **Bootstrap files location:** `playbook/BOOTSTRAP.md`, `playbook/scripts/daily-checks.py`
- **Bootstrap v2 design discussion:** `#testing-env` (2026-06-09 evening)
- **Dropbox direct API proof:** `#testing-env` (2026-06-10 morning)
- **Bob's 1PW/Dropbox/GitHub access proofs:** `#testing-env` (2026-06-09 19:20)
- **Hetzner snapshots:** `Pre-Bootstrap.md-implementation-06-09-2026`

---

*This implementation plan is complete and ready to execute. Follow steps in order. Do not skip. Report results after each phase.*
