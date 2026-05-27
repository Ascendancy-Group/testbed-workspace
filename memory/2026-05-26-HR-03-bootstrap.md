# HR-03: BOOTSTRAP.md Enhancement — Testbed + Bob
*Date: 2026-05-26 17:09 CDT*
*Ticket: https://github.com/Ascendancy-Group/ascendancy-testing/issues/35*

## Summary

Enhanced BOOTSTRAP.md with context injection checks to ensure agents monitor bootstrap size and context health at every session start.

## Changes

**Added new section: "Context Injection Checks"**

### Bootstrap Size Measurement
```bash
# Measure total bootstrap
TOTAL=0
for file in *.md; do
  SIZE=$(wc -c < "$file")
  TOTAL=$((TOTAL + SIZE))
done
echo "Total: $TOTAL chars (limit: 60,000)"
```

### Individual File Limits
- Check for files > 15k chars
- Alert if any exceed limit

### MEMORY.md Line Count
- Target: < 100 lines
- Archive old content if over

### Config Verification
- Verify `bootstrapMaxChars: 15000` in openclaw.json
- Verify `bootstrapTotalMaxChars: 60000`

### Personality Self-Test
- Ask: "Who are you? What is your purpose?"
- Expected: Identity from SOUL.md
- If vanilla/generic: Context injection problem

### Weekly Maintenance
- Full baseline measurement every Monday
- Token cost review (OpenRouter dashboard)
- Config verification

## Implementation

**Testbed (testbed-m1):**
- Created new BOOTSTRAP.md
- Commit: d50076f
- Size: 4 KB

**Bob (bobwebdev-m1):**
- Enhanced existing BOOTSTRAP.md
- Commit: 961d6f4
- Added context checks section
- Includes Bob's proven baseline: 33,777 chars

## Purpose

**Session startup discipline:**
- Agents check their own context health every session
- Early warning if files grow too large
- Catch missing config before problems occur
- Verify personality intact

**Weekly maintenance:**
- Proactive monitoring
- Cost tracking
- Config drift detection

## References

- **SOP-15:** Full context injection management procedure
- **HR-01:** AGENTS.md hard rule
- **QW-03:** Bootstrap limits implementation

---

## ✅ EPIC 3 Complete

All three HR tickets complete:
- ✅ HR-02: SOP-15 creation (governance repo)
- ✅ HR-01: AGENTS.md hard rule (both machines)
- ✅ HR-03: BOOTSTRAP.md enhancement (both machines)

**Context injection control now embedded in:**
1. Governance (SOP-15 - reference documentation)
2. Identity (AGENTS.md - hard rule)
3. Bootstrap (BOOTSTRAP.md - session checks)

---

*Both agents now have complete context injection management infrastructure.*
