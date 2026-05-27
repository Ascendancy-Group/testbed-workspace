# PRE-01: Config Rollback Validation Test
*Executed: 2026-05-26 15:18-15:23 CDT*
*Agent: Testbed*
*Status: ✅ PASS*

---

## Objective
Validate backup/restore procedure for openclaw.json before any real config changes.

---

## Execution Steps

### Step 1: Backup Creation ✅
```bash
BACKUP_FILE="testbed-PRE-01-2026-05-26_15-18.json"
cp openclaw.json ${BACKUP_FILE}
```
- Result: Backup created (4.2K)
- Validation: JSON valid
- Location: `~/.openclaw/testbed-PRE-01-2026-05-26_15-18.json`

### Step 2: Test Modification ✅
Added test key to openclaw.json:
```json
{
  "_test_rollback": "PRE-01 validation test - delete this key to verify rollback"
}
```
- JSON remained valid after modification

### Step 3: Gateway Validation ⚠️
```bash
openclaw gateway restart
```
**Result:** Gateway rejected config with error:
```
OpenClaw config is invalid
<root>: Invalid input
```

**Analysis:** OpenClaw schema validation correctly rejected arbitrary key. This is a **safety feature**, not a bug.

### Step 4: Rollback Execution ✅
```bash
cp testbed-PRE-01-2026-05-26_15-18.json openclaw.json
```
- Config restored successfully
- Test key removed
- JSON validation passed

### Step 5: Gateway Restart ✅
```bash
openclaw gateway restart
```
- Gateway started successfully
- Status: running (pid 77086)
- Connectivity probe: ok
- No errors in logs

---

## Key Findings

### 1. Schema Validation is Strict
OpenClaw rejects any keys not in the schema. This means:
- We cannot use arbitrary test keys for rollback testing
- Config keys for QW-03 (`bootstrapMaxChars`, `bootstrapTotalMaxChars`) **must be real schema keys**
- Bob's source code verification is critical — keys must exist in schema

### 2. Rollback Procedure Works
- ✅ Backup naming convention: `{agent}-{ticket}-{timestamp}.json`
- ✅ Backup validation: JSON parsing confirms validity
- ✅ Restore procedure: Simple `cp` works correctly
- ✅ Gateway handles config errors gracefully (doesn't crash)

### 3. Safety Features Confirmed
- Invalid config blocks gateway startup (prevents broken state)
- Gateway provides clear error messages
- Previous config preserved (can always roll back)

---

## Recommendations for QW-03

**Before implementing bootstrap limits:**
1. Verify `bootstrapMaxChars` exists in OpenClaw schema
2. Check OpenClaw docs for exact key names and valid values
3. Test on Testbed first with real schema keys
4. Have rollback ready (procedure now validated)

**Alternative test approach:**
Instead of arbitrary keys, test with a known-valid config change (e.g., modify an existing value slightly, then restore).

---

## Rollback Validation: ✅ PASS

**Procedure proven:**
1. Create timestamped backup with SOP-14 naming
2. Validate backup is readable
3. Make change (or detect invalid config)
4. Restore from backup
5. Restart gateway
6. Verify agent responds

**Time:** ~4 minutes for full cycle

**Ready for QW-01 (Baseline Measurement).**

---

## Backup File Location
`~/.openclaw/testbed-PRE-01-2026-05-26_15-18.json` (preserved for audit)
