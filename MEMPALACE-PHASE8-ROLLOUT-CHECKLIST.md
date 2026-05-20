# MemPalace Phase 8 Rollout Checklist
**Version:** 3.3.0 (N-4 non-compliant — 3.3.5 upgrade planned separately)  
**Rollout Date:** 2026-05-20  
**Order:** Bob → Mason → Forge  
**Executor:** Testbed

---

## Pre-Rollout Validation ✅

- [x] Testbed Phases 1-7 complete
- [x] Evidence report written: `memory/2026-05-19-mempalace-phase1-7-evidence.md`
- [x] Testbed snapshot: `Testbed-M1-MemPalaceImplement-05-19-2026`
- [x] Testbed JSON backup: `testbed-mempalace-addition-2026-05-19_11-50.json`
- [x] Fresh session tool validation passed
- [x] Pieter approval received (2026-05-19 11:59 CDT)

---

## Agent 1: Bob (bobwebdev-m1) 🏗️

**Status:** Has MemPalace 3.3.0 + 10,774 drawers  
**IP:** 100.126.243.57  
**SSH Key:** `~/.ssh/bob_key`

### Pre-flight Checks
- [ ] Verify Bob's gateway is running: `ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "systemctl --user is-active openclaw-gateway.service"`
- [ ] Verify existing palace: `ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "python3 -m mempalace status | head -5"`
- [ ] Confirm MemPalace version: `ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "pip3 show mempalace | grep Version"`

### Backup Protocol
- [ ] **Pieter:** Create Hetzner snapshot `bobwebdev-m1-mempalace-mcp-wiring-2026-05-20`
- [ ] **Pieter:** Confirm snapshot created
- [ ] **Testbed:** Create JSON backup:
```bash
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "cp ~/.openclaw/openclaw.json ~/.openclaw/bob-mempalace-mcp-addition-${TIMESTAMP}.json"
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "python3 -c \"import json; json.load(open('/home/pieter/.openclaw/bob-mempalace-mcp-addition-${TIMESTAMP}.json')); print('✅ Backup valid')\""
```
- [ ] **Testbed:** Verify backup size/location

### MCP Wiring
- [ ] **Testbed:** Wire MCP config into Bob's `openclaw.json`:
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "python3 << 'PYEOF'
import json
path = '/home/pieter/.openclaw/openclaw.json'
with open(path) as f:
    d = json.load(f)
d.setdefault('mcp', {}).setdefault('servers', {})
d['mcp']['servers']['mempalace'] = {
    'command': 'python3',
    'args': ['-m', 'mempalace.mcp_server'],
    'env': {'MEMPALACE_DIR': '/home/pieter/.mempalace'}
}
with open(path, 'w') as f:
    json.dump(d, f, indent=2)
print('✅ MCP config added')
PYEOF
"
```
- [ ] **Testbed:** Validate JSON:
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "python3 -c 'import json; json.load(open(\"/home/pieter/.openclaw/openclaw.json\")); print(\"✅ JSON valid\")'"
```

### Gateway Restart
- [ ] **Testbed:** Restart Bob's gateway:
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "systemctl --user restart openclaw-gateway.service"
```
- [ ] **Testbed:** Wait 10 seconds
- [ ] **Testbed:** Verify gateway active:
```bash
ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "systemctl --user is-active openclaw-gateway.service"
```

### Validation Test
- [ ] **Testbed:** Send test message to Bob via `sessions_send`:
```
Task: Test if mempalace_search tool is available. Search your palace for "GFMJ". Report back if the tool works and what you found.
```
- [ ] **Testbed:** Receive Bob's response confirming tool availability
- [ ] **Testbed:** Verify Bob can search his 10,774-drawer palace

### Rollback (if needed)
- [ ] Restore JSON: `ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "cp ~/.openclaw/bob-mempalace-mcp-addition-2026-05-20_[TIME].json ~/.openclaw/openclaw.json"`
- [ ] Restart gateway: `ssh -i ~/.ssh/bob_key pieter@100.126.243.57 "systemctl --user restart openclaw-gateway.service"`
- [ ] If gateway won't start: Pieter restores Hetzner snapshot

### Sign-off
- [ ] **Testbed:** ✅ Bob MemPalace MCP operational
- [ ] **Pieter:** Approval to proceed to Mason

---

## Agent 2: Mason (mason-m1) 🔨

**Status:** Clean slate (no MemPalace)  
**IP:** 100.116.59.116  
**SSH Key:** `~/.ssh/bob_key`

### Pre-flight Checks
- [ ] Verify Mason's gateway is running
- [ ] Verify no existing MemPalace: `ssh -i ~/.ssh/bob_key pieter@100.116.59.116 "pip3 show mempalace || echo 'Not installed'"`

### Backup Protocol
- [ ] **Pieter:** Create Hetzner snapshot `mason-m1-mempalace-install-2026-05-20`
- [ ] **Pieter:** Confirm snapshot created
- [ ] **Testbed:** Create JSON backup:
```bash
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
ssh -i ~/.ssh/bob_key pieter@100.116.59.116 "cp ~/.openclaw/openclaw.json ~/.openclaw/mason-mempalace-addition-${TIMESTAMP}.json"
```

### Installation
- [ ] **Testbed:** Install MemPalace 3.3.0 on Mason:
```bash
ssh -i ~/.ssh/bob_key pieter@100.116.59.116 "pip3 install mempalace==3.3.0 --user --break-system-packages"
```
- [ ] **Testbed:** Verify install:
```bash
ssh -i ~/.ssh/bob_key pieter@100.116.59.116 "pip3 show mempalace | grep Version"
```

### MCP Wiring
- [ ] **Testbed:** Wire MCP config (same script as Bob)
- [ ] **Testbed:** Validate JSON

### Gateway Restart
- [ ] **Testbed:** Restart Mason's gateway
- [ ] **Testbed:** Verify gateway active

### Validation Test
- [ ] **Testbed:** Send test message to Mason confirming tool availability
- [ ] **Mason:** Responds with `mempalace_status` (should show 0 drawers — clean palace)

### Rollback (if needed)
- [ ] Restore Hetzner snapshot (full rollback — cleaner than JSON restore for new install)

### Sign-off
- [ ] **Testbed:** ✅ Mason MemPalace MCP operational
- [ ] **Pieter:** Approval to proceed to Forge

---

## Agent 3: Forge (forge-m1) 🔥

**Status:** Clean slate (no MemPalace)  
**IP:** 100.120.117.84  
**SSH Key:** `~/.ssh/bob_key`

### Pre-flight Checks
- [ ] Verify Forge's gateway is running
- [ ] Verify no existing MemPalace

### Backup Protocol
- [ ] **Pieter:** Create Hetzner snapshot `forge-m1-mempalace-install-2026-05-20`
- [ ] **Pieter:** Confirm snapshot created
- [ ] **Testbed:** Create JSON backup

### Installation
- [ ] **Testbed:** Install MemPalace 3.3.0 on Forge
- [ ] **Testbed:** Verify install

### MCP Wiring
- [ ] **Testbed:** Wire MCP config
- [ ] **Testbed:** Validate JSON

### Gateway Restart
- [ ] **Testbed:** Restart Forge's gateway
- [ ] **Testbed:** Verify gateway active

### Validation Test
- [ ] **Testbed:** Send test message to Forge confirming tool availability
- [ ] **Forge:** Responds with `mempalace_status` (should show 0 drawers)

### Rollback (if needed)
- [ ] Restore Hetzner snapshot

### Sign-off
- [ ] **Testbed:** ✅ Forge MemPalace MCP operational
- [ ] **Pieter:** Phase 8 complete

---

## Post-Rollout

### Documentation
- [ ] Update `MEMORY.md` — MemPalace moved from test queue to "Deployed (3.3.0)"
- [ ] Update `HANDOFF.md` — Phase 8 complete, 3.3.5 upgrade next
- [ ] Write daily log: `memory/2026-05-20.md`
- [ ] Commit workspace changes to GitHub

### Next Steps
- [ ] Schedule MemPalace 3.3.5 upgrade validation on testbed
- [ ] Document 3.3.5 upgrade procedure
- [ ] Roll 3.3.5 to production (same order: Bob → Mason → Forge)

---

## Rollback Emergency Contacts

| Issue | Action |
|-------|--------|
| Gateway won't start | Restore Hetzner snapshot |
| MCP server crashes sessions | Restore JSON backup, restart gateway |
| Tools not loading | Fresh session test — if still failing, restore JSON |
| Palace data corrupted | Bob only: Restore snapshot (has existing palace) |

---

**Testbed Notes:**
- Bob is highest risk (existing palace) but highest reward (most memory failures)
- Mason/Forge are clean installs — safer but less immediate value
- All three agents already have Dropbox MCP working (SOP-04 validated 2026-05-19)
- SSH access established using `~/.ssh/bob_key` (bobwebdev-m1 recovery key)

**Execution window:** 2026-05-20, after 1-day soak from testbed validation

---

**Checklist written:** 2026-05-19 12:02 CDT  
**Testbed signature:** 🧪
