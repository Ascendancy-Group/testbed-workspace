# BOOTSTRAP.md — Testbed Session Startup

**Run these checks at the start of every session.**

---

## 1. Identity Verification

```bash
# Confirm who you are
echo "I am Testbed, infrastructure tester on testbed-m1"
echo "Purpose: Test infrastructure changes before production"
```

**Expected:** Clear identity from SOUL.md loaded

---

## 2. Workspace State

```bash
cd ~/.openclaw/workspace

# Check git status
git status

# Pull latest
git pull

# Check for uncommitted changes
git diff --stat
```

**Expected:** Workspace clean or known pending changes

---

## 3. Gateway Health

```bash
# Gateway status
openclaw gateway status | head -15

# Check recent logs
tail -50 /tmp/openclaw/openclaw-$(date +%Y-%m-%d).log | grep -i error
```

**Expected:** Gateway running, no critical errors

---

## 4. Context Injection Checks

**Added:** 2026-05-26 (See SOP-15, HR-01)

### Bootstrap Size Measurement

```bash
cd ~/.openclaw/workspace

# Measure total bootstrap
TOTAL=0
for file in SOUL.md AGENTS.md MEMORY.md USER.md TOOLS.md HEARTBEAT.md IDENTITY.md HANDOFF.md; do
  if [ -f "$file" ]; then
    SIZE=$(wc -c < "$file")
    TOTAL=$((TOTAL + SIZE))
    echo "$file: $SIZE chars"
  fi
done
echo "Total bootstrap: $TOTAL chars (limit: 60,000)"
```

**Expected:** Total < 60,000 chars ✅

### Individual File Limits

```bash
# Check for oversized files
cd ~/.openclaw/workspace
for file in *.md; do
  SIZE=$(wc -c < "$file")
  if [ $SIZE -gt 15000 ]; then
    echo "⚠️ $file: $SIZE chars (exceeds 15k limit)"
  fi
done
```

**Expected:** No files > 15,000 chars

### MEMORY.md Line Count

```bash
wc -l MEMORY.md
```

**Expected:** < 100 lines (archive old content if over)

### Config Verification

```bash
# Verify bootstrap limits in openclaw.json
grep -A3 "bootstrapMaxChars" ~/.openclaw/openclaw.json
```

**Expected output:**
```json
"bootstrapMaxChars": 15000,
"bootstrapTotalMaxChars": 60000
```

### Personality Self-Test

**Ask yourself:** "Who are you? What is your purpose?"

**Expected answer should include:**
- Name: Testbed
- Machine: testbed-m1
- Role: Infrastructure tester
- Purpose: Test changes before production

**If answer is generic/vanilla:** Context injection problem - check logs and limits

---

## 5. Memory Sources

```bash
# Pull Honcho context
python3 ~/scripts/honcho-integration/honcho_client.py get-context

# Check today's log exists
ls -lh memory/$(date +%Y-%m-%d).md 2>/dev/null || echo "No log for today yet"

# Read HANDOFF.md for current state
head -20 HANDOFF.md
```

**Expected:** Honcho accessible, HANDOFF.md up to date

---

## 6. Governance Sync

```bash
cd ~/repos/ascendancy-governance
git pull
ls -lh playbook/sops/ | tail -5
```

**Expected:** Governance repo synced, SOPs accessible

---

## Weekly Maintenance (Every Monday)

### Context Injection Audit

```bash
# Run full baseline measurement (QW-01)
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
- Target: 50%+ reduction after QW-03 implementation (2026-05-26)

### Config Verification

```bash
# Ensure limits still present
grep "bootstrapMaxChars" ~/.openclaw/openclaw.json
```

**If missing:** Restore from backup, see SOP-14

---

## References

- **SOP-15:** Context Injection Management (full procedure)
- **HR-01:** AGENTS.md hard rule (context injection control)
- **QW-03:** Bootstrap limits implementation (2026-05-26)

---

*These bootstrap checks ensure agent health, context control, and cost management. Run them every session start.*
