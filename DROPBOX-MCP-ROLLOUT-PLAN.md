# Dropbox MCP Rollout Plan — All Agents

*Created: 2026-05-19 | Author: Testbed | Status: Ready for execution*

---

## Overview

All production agents (Bob, Mason, Forge) need Dropbox MCP access configured. This document defines the rollout sequence, backup requirements, and verification steps.

**Completed:**
- ✅ Testbed-M1 (2026-05-19)
- ✅ Bob-M1 (2026-05-19)

**Pending:**
- ⏸️ Mason-M1
- ⏸️ Forge-M1

---

## Prerequisites (Every Agent)

Before making any JSON changes:

1. **Hetzner snapshot** (Pieter creates these)
2. **JSON backup** with naming convention: `{agent}-dropbox-addition-YYYY-MM-DD_HH-MM.json`
3. **SSH access confirmed** from testbed-m1 to target agent machine
4. **1Password service account working** on testbed-m1 (already verified)
5. **MCP server running** on honcho-m1 (already verified)

---

## Per-Agent Sequence

### 1. Create Hetzner Snapshot
**Who:** Pieter  
**Format:** `{machine}-dropbox-mcp-YYYY-MM-DD`

Examples:
- `mason-m1-dropbox-mcp-05-19-2026`
- `forge-m1-dropbox-mcp-05-19-2026`

### 2. Backup JSON
**Who:** Testbed (via SSH)

```bash
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
AGENT_NAME='{agent}'
TIMESTAMP=\$(date +%Y-%m-%d_%H-%M)
cp ~/.openclaw/openclaw.json ~/.openclaw/\${AGENT_NAME}-dropbox-addition-\${TIMESTAMP}.json
python3 -c 'import json; json.load(open(\"/home/pieter/.openclaw/\${AGENT_NAME}-dropbox-addition-\${TIMESTAMP}.json\")); print(\"backup valid\")'
ls -lh ~/.openclaw/\${AGENT_NAME}-dropbox-addition-*.json | tail -1
"
```

### 3. Apply MCP Config
**Who:** Testbed (via SSH + Python)

```bash
MCP_KEY="$(op read 'op://AgentStack/Ascendancy MCP API Key/credential')"
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
python3 -c \"
import json

path = '/home/pieter/.openclaw/openclaw.json'
with open(path) as f:
    d = json.load(f)

# Add Dropbox MCP config
d.setdefault('mcp', {}).setdefault('servers', {})
d['mcp']['servers']['dropbox'] = {
    'url': 'http://100.77.0.47:3001/sse',
    'headers': {'x-api-key': '$MCP_KEY'}
}

with open(path, 'w') as f:
    json.dump(d, f, indent=2)

print('✅ Dropbox MCP config added')
\"
"
```

### 4. Validate JSON
```bash
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
python3 -c 'import json; json.load(open(\"/home/pieter/.openclaw/openclaw.json\")); print(\"JSON valid\")'
"
```

### 5. Restart Gateway
```bash
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
/home/pieter/.local/bin/oc-restart
sleep 8
curl -s -m 5 http://localhost:18789/status | head -c 100
systemctl --user is-active openclaw-gateway.service
"
```

### 6. Verify Config
```bash
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
python3 -c '
import json
with open(\"/home/pieter/.openclaw/openclaw.json\") as f:
    d = json.load(f)
dropbox = d.get(\"mcp\", {}).get(\"servers\", {}).get(\"dropbox\", {})
print(\"URL:\", dropbox.get(\"url\", \"MISSING\"))
key = dropbox.get(\"headers\", {}).get(\"x-api-key\", \"MISSING\")
print(\"Key:\", key[:20] + \"...\" if len(key) > 20 else key)
'
"
```

### 7. Test Dropbox Access
```bash
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
MCP_KEY=\$(python3 -c 'import json; d=json.load(open(\"/home/pieter/.openclaw/openclaw.json\")); print(d[\"mcp\"][\"servers\"][\"dropbox\"][\"headers\"][\"x-api-key\"])')
curl -s -m 5 http://100.77.0.47:3001/sse -H \"x-api-key: \$MCP_KEY\" | head -c 150
"
```

Expected: `event: endpoint` response.

### 8. Update SOP-04 Status Table
Mark agent as ✅ in `~/repos/ascendancy-governance/playbook/sops/04-dropbox.md`.

---

## Agent-Specific Details

### Mason-M1
- **Tailscale IP:** `100.117.192.71`
- **Machine:** mason-m1
- **Agent name:** `mason`
- **Hetzner snapshot format:** `mason-m1-dropbox-mcp-05-19-2026`
- **JSON backup format:** `mason-dropbox-addition-2026-05-19_HH-MM.json`

### Forge-M1
- **Tailscale IP:** `100.95.36.105`
- **Machine:** forge-m1
- **Agent name:** `forge`
- **Hetzner snapshot format:** `forge-m1-dropbox-mcp-05-19-2026`
- **JSON backup format:** `forge-dropbox-addition-2026-05-19_HH-MM.json`

---

## Rollback Procedure (If Anything Goes Wrong)

### Immediate Rollback (JSON corruption or gateway won't start)
```bash
ssh -i ~/.ssh/bob_key pieter@{MACHINE_IP} "
# Find most recent backup
BACKUP=\$(ls -t ~/.openclaw/{agent}-dropbox-addition-*.json | head -1)
echo \"Restoring from: \$BACKUP\"

# Restore backup
cp \$BACKUP ~/.openclaw/openclaw.json

# Validate restored JSON
python3 -c 'import json; json.load(open(\"/home/pieter/.openclaw/openclaw.json\")); print(\"restore valid\")'

# Restart gateway
/home/pieter/.local/bin/oc-restart
"
```

### Full Rollback (Gateway issues persist)
1. Pieter restores from Hetzner snapshot
2. Machine reboots to pre-change state
3. Diagnose issue before re-attempting

---

## Success Criteria (Per Agent)

- ✅ Hetzner snapshot created
- ✅ JSON backup created and validated
- ✅ MCP config added to `openclaw.json`
- ✅ Gateway restarted successfully
- ✅ MCP endpoint responds with `event: endpoint`
- ✅ SOP-04 status table updated
- ✅ Agent can read Dropbox exports (via fallback method test)

---

## Execution Order

**Phase 1:** Bob-M1 ✅ (completed 2026-05-19)  
**Phase 2:** Mason-M1 (next)  
**Phase 3:** Forge-M1 (after Mason confirmed working)

**Rationale:** Staggered rollout. If Mason has issues, Forge remains untouched.

---

## Communication Protocol

After each agent completion:
1. Testbed posts evidence in #testing-env
2. Pieter confirms before moving to next agent
3. Bob verifies his Dropbox access is still working (canary check)

---

## Notes

- **Bob + Testbed complete** — both agents now have working Dropbox MCP access
- **Mason + Forge pending** — awaiting Pieter's approval to proceed
- **MCP server stable** — running on honcho-m1, no crashes since restart
- **All backups in place** — Hetzner snapshots + JSON backups for rollback

---

*Ready to execute Mason-M1 on Pieter's approval.*
