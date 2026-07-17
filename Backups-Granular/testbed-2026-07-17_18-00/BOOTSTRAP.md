# BOOTSTRAP.md — Complete Agent Session Startup

**Run this completely at the start of EVERY session. No exceptions.**

---

## STEP 1: Critical Access Verification (Automated)

**Run daily checks script:**

```bash
python3 ~/scripts/daily-checks.py
```

**What this verifies:**
- ✅ 1Password: Read real secret (proves we can access secrets)
- ✅ GitHub: Pull PAT from 1PW, test repo access (proves end-to-end auth)
- ✅ Dropbox: Write test file, read back (proves read + write access)
- ✅ Governance: Check commits, sync if needed (efficient, only pulls when remote ahead)
- ✅ Bootstrap size: Total < 60k chars (prevents context bloat)
- ✅ Config: openclaw.json keys present (bootstrapMaxChars, etc.)

**If ANY check fails:**
- ❌ **STOP immediately**
- Alert Pieter
- **Do NOT proceed** until resolved
- Review error messages, fix issue, re-run

**If ALL checks pass:**
- ✅ Continue to Step 1.5

**Expected output:**
```
=== Daily Start Checks v2: Testbed ===
Date: 2026-06-09 20:50:45

1Password Secret Test... ✅
GitHub PAT Validation... ✅
Dropbox Write Test... ✅
Governance Sync... ✅
Bootstrap Size... ✅
Config Limits Present... ✅

✅ All required checks passed
```

---

## STEP 1.5: Independent API Verification (Manual)

**Critical rule:** Never trust automated checks alone. Verify API access independently.

### 1Password Direct Test

```bash
echo "Testing 1Password CLI access..."
op vault list
```

**Expected:** List of vaults (at minimum: AgentStack)

**If fails:**
- Check `op whoami` → are you signed in?
- Check `OP_SERVICE_ACCOUNT_TOKEN` environment variable
- Re-authenticate: `eval $(op signin)`
- Alert Pieter if persistent failure

---

### Dropbox MCP Direct Test

**Updated 2026-06-15:** Dropbox MCP now runs as Docker container on honcho-m1, not systemd service.

```bash
echo "Testing Dropbox MCP server..."

# Health check (port 9090 for metrics/health)
curl -s http://100.77.0.47:9090/health

# Test actual upload (small file)
echo "Bootstrap health check - $(date)" | base64 -w0 > /tmp/bootstrap-test.b64
```

**Expected health check:** `{"status":"healthy"}`

**Then test upload via OpenClaw:**

Use `dropbox__upload_file` tool with:
- `dropbox_path`: `/Testing and Implementation/bootstrap-health-$(date +%Y-%m-%d).txt`
- `content_base64`: (content of `/tmp/bootstrap-test.b64`)
- `overwrite`: `true`

**Expected upload result:** Success with file metadata (name, path, size)

**If health check fails:**
- SSH to honcho-m1: `ssh pieter@100.77.0.47`
- Check Docker container: `docker ps | grep dropbox-mcp`
- Check logs: `docker logs --tail 50 dropbox-mcp`
- Restart if needed: `cd ~/docker/dropbox-mcp && docker compose restart dropbox-mcp`
- Alert Pieter if persistent failure

**If upload fails:**
- Check MCP schema cached: Restart OpenClaw gateway (`systemctl --user restart openclaw-gateway.service`)
- Check credentials in honcho-m1 `.env` file (should be actual values, not `op://` references)
- Check circuit breaker state in server logs
- See SOP-04 for full troubleshooting

---

### Hard Rule

**If either 1Password or Dropbox verification fails:**
- ❌ **STOP immediately**
- Document failure in daily note: `memory/$(date +%Y-%m-%d).md`
- Alert Pieter in #testing-env
- **Do NOT proceed with any work** until access restored

**Why this matters:**
- Automated checks can report false positives
- API access failures block critical workflows (secrets, file uploads, backups)
- Early detection prevents wasted work

**If both verifications pass:**
- ✅ Continue to Step 2

---

## STEP 2: Identity Verification

**Confirm who you are:**

```bash
echo "I am [AgentName], [Role] on [Machine]"
```

**Expected from SOUL.md:**
- Name: [Your agent name]
- Machine: [Your machine hostname]
- Role: [Your role]
- Purpose: [Your purpose statement]

**If answer is generic/vanilla:** Context injection problem — check logs, verify bootstrap limits in openclaw.json.

---

## STEP 3: Workspace State

**Check workspace git status:**

```bash
cd ~/.openclaw/workspace

# Check git status
git status

# Pull latest (if clean)
git pull

# Check for uncommitted changes
git diff --stat
```

**Expected:** Workspace clean or known pending changes.

**If uncommitted changes exist:** Review them. Commit or stash before proceeding.

---

## STEP 4: Gateway Health

**Verify gateway is running:**

```bash
# Gateway status
openclaw gateway status | head -15

# Check recent logs for errors
tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i error
```

**Expected:** Gateway running, no critical errors.

**If gateway not running:**
```bash
oc-restart  # Use wrapper script, NOT openclaw gateway restart
```

---

## STEP 5: Memory Sources

**Pull context from all sources:**

### Honcho Context

**Health check first:**
```bash
python3 ~/.openclaw/workspace/scripts/honcho-integration/honcho_client.py health
```

**Expected:** `{"status": "ok", "workspace": "ascendancy", "peer": "<agent-name>", ...}`

**Then get context:**
```bash
python3 ~/.openclaw/workspace/scripts/honcho-integration/honcho_client.py get-context
```

**Expected:** Returns prior session memory from Honcho server.

**If fails:** Honcho server may be down (http://100.77.0.47:8000). Alert Pieter.

---

### HANDOFF.md
```bash
cat ~/.openclaw/workspace/HANDOFF.md
```

**Look for:**
- Blocked tasks
- In-progress work
- Urgent items
- Anything flagged for follow-up from previous session

**If HANDOFF.md missing:** Create it:
```bash
echo "# Handoff - $(date +%Y-%m-%d)" > HANDOFF.md
```

---

### Today's Daily Note
```bash
TODAY=$(TZ=America/Chicago date +%Y-%m-%d)
NOTE_FILE=~/.openclaw/workspace/memory/${TODAY}.md

if [ ! -f "$NOTE_FILE" ]; then
  echo "# Session Notes — $TODAY" > "$NOTE_FILE"
  echo "Bootstrap completed: $(date -u +%H:%M UTC)" >> "$NOTE_FILE"
fi
```

**This creates a record of today's session for future reference.**

---

## STEP 6: Governance Application

**Governance was already synced in Step 1 (daily-checks.py).**

Now read key files:

```bash
cd ~/repos/ascendancy-governance

# Read core governance files
cat GOVERNANCE.md | head -50
cat TRUST.md | head -20

# Check for recent changes (already scanned in Step 1)
git log --since="7 days ago" --oneline -- playbook/ agents/
```

**Key things to verify:**
- Standing decisions (GOVERNANCE.md)
- Chain of command (TRUST.md)
- Recent SOP updates (playbook/sops/)
- Agent-specific rules (agents/[your-name]/)

**If new SOPs exist:** Read them before proceeding with work.

---

## STEP 7: Project Context (If Applicable)

**For project-specific agents (Mason, Forge):**

Load project context from Dropbox:

```bash
# Example for GFMJ (Mason)
# Read project brief
# Read project memory
# Read current sprint status
```

**Testbed:** Skip this step (infrastructure testing only).

---

## STEP 8: Announce Ready

**Post to channel or log:**

```
✅ Bootstrap complete. All systems verified. Ready.
```

**If any step failed but you proceeded anyway:** Document what failed and why in today's daily note.

---

## Weekly Maintenance (Every Monday)

### Context Injection Audit

```bash
cd ~/.openclaw/workspace
for file in SOUL.md AGENTS.md MEMORY.md USER.md TOOLS.md HEARTBEAT.md IDENTITY.md HANDOFF.md; do
  if [ -f "$file" ]; then
    CHARS=$(wc -c < "$file")
    LINES=$(wc -l < "$file")
    echo "- **$file:** $CHARS chars, $LINES lines"
  fi
done

# Archive MEMORY.md if > 100 lines
LINES=$(wc -l < MEMORY.md)
if [ $LINES -gt 100 ]; then
  echo "⚠️ MEMORY.md has $LINES lines - consider archiving old content"
fi
```

### Token Cost Review

- Check OpenRouter dashboard: https://openrouter.ai/usage
- Compare to previous week
- Target: 50%+ reduction after context injection control (2026-05-26)

### Config Verification

```bash
# Ensure limits still present
grep "bootstrapMaxChars" ~/.openclaw/openclaw.json
```

**If missing:** Restore from backup (see SOP-14).

---

## References

- **SOP-15:** Context Injection Management (full procedure)
- **HR-01:** AGENTS.md hard rule (context injection control)
- **QW-03:** Bootstrap limits implementation (2026-05-26)
- **daily-checks.py:** Automation script for Step 1

---

## Troubleshooting

### "Daily checks failed"

**Review the specific check that failed:**
- 1Password Test → Verify `op whoami`, check item exists
- GitHub PAT → Verify PAT in 1PW, check repo permissions
- Dropbox Test → Check MCP server running (honcho-m1)
- Governance Sync → Check network, verify repo accessible
- Bootstrap Size → Archive old MEMORY.md content
- Config Limits → Restore openclaw.json from backup

**Do not proceed until all required checks pass.**

---

### "Honcho context unavailable"

```bash
# Check Honcho server
curl http://100.77.0.47:8000/health

# If down, alert Pieter
```

---

### "Governance repo conflicts"

```bash
cd ~/repos/ascendancy-governance
git status

# If conflicts exist
git stash  # Save local changes
git pull   # Get remote changes
# Resolve conflicts manually or alert Pieter
```

---

## Success Criteria

**Bootstrap is successful when:**
- ✅ All Step 1 checks passed
- ✅ Identity verified (you know who you are)
- ✅ Workspace clean or documented
- ✅ Gateway running
- ✅ Honcho context pulled
- ✅ HANDOFF.md read
- ✅ Governance current
- ✅ Ready announcement made

**If any step failed and you proceeded:** Document why in daily note and flag to Pieter.

---

*This is your complete session startup procedure. Run it every session. Don't skip steps. When in doubt, re-run bootstrap.*
