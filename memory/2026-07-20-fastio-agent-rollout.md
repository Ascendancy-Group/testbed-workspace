# Fast.io Agent Rollout - Bob, Mason, Forge

**Date:** 2026-07-20  
**Status:** Pending execution  
**Approved by:** Pieter van der Wal

---

## Target Agents

1. **Bob** (bobwebdev-m1) - Tailscale IP TBD
2. **Mason** (mason-m1) - Tailscale IP: 100.117.192.71
3. **Forge** (forge-m1) - Tailscale IP TBD

---

## Installation Procedure (Per Agent)

### Step 1: Install Fast.io CLI

```bash
npm install --global @vividengine/fastio-cli
```

**Verify:**
```bash
fastio --version
# Expected: fastio 0.2.12 or later
```

### Step 2: Create Token Environment File

```bash
cd ~/.openclaw/workspace

# Get token from 1Password
TOKEN=$(op item get "Fast.io" --vault AgentStack --fields label=API)

# Create .env.fastio
cat > .env.fastio <<EOF
# Fast.io API Token - Ascendancy Group
# Created: 2026-07-20
# Stored in 1Password: AgentStack vault > Fast.io > API
# Workspace: Ascendancy Group Main Share (4857845230237369802)

FASTIO_TOKEN=$TOKEN
FASTIO_WORKSPACE_ID=4857845230237369802
EOF

chmod 600 .env.fastio
```

### Step 3: Configure OpenClaw MCP

**Backup openclaw.json first:**
```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-fastio-$(date +%Y%m%d-%H%M%S)
```

**Add Fast.io MCP server:**

Edit `~/.openclaw/openclaw.json` and add to `mcpServers` section:

```json
{
  "mcpServers": {
    "fastio": {
      "transport": "stdio",
      "command": "fastio",
      "args": ["mcp"],
      "env": {
        "FASTIO_TOKEN": "v7l6kexp2jp488bmmw7g5in6k68nilpwp4lqjy8wpve096pvdp"
      }
    }
  }
}
```

**⚠️ Important:** Replace `FASTIO_TOKEN` value with actual token from 1Password:
```bash
op item get "Fast.io" --vault AgentStack --fields label=API
```

### Step 4: Restart Gateway

```bash
systemctl --user restart openclaw-gateway.service
```

**Verify:**
```bash
systemctl --user status openclaw-gateway.service | head -20
```

### Step 5: Test Fast.io Access

**From within OpenClaw session (not bash):**

Test workspace access (exact tool names TBD after MCP schema loads)

**Via CLI:**
```bash
source ~/.openclaw/workspace/.env.fastio
fastio --token "$FASTIO_TOKEN" workspace list --format json
# Expected: Shows "Ascendancy Group Main Share"
```

---

## Success Criteria (Per Agent)

- [ ] Fast.io CLI installed (version 0.2.12+)
- [ ] `.env.fastio` created with correct token
- [ ] `openclaw.json` updated with Fast.io MCP server
- [ ] Gateway restarted successfully
- [ ] Fast.io tools available in OpenClaw (check via gateway status)
- [ ] Workspace accessible via CLI

---

## Rollback Procedure

**If Fast.io causes issues:**

```bash
# 1. Remove Fast.io MCP server from openclaw.json
# Restore from backup:
cp ~/.openclaw/openclaw.json.backup-fastio-TIMESTAMP ~/.openclaw/openclaw.json

# 2. Restart gateway
systemctl --user restart openclaw-gateway.service

# 3. Verify
systemctl --user status openclaw-gateway.service
```

---

## Execution Plan

### Option A: Manual Execution (Fastest)

**Pieter executes on each machine:**
1. SSH to each agent
2. Run installation procedure
3. Verify success criteria
4. Report completion

**Estimated time:** 15 minutes per agent, 45 minutes total

### Option B: Agent Self-Install (Via Sessions_send)

**Testbed sends instructions to Bob:**
- Bob installs on bobwebdev-m1
- Bob SSH to Mason and Forge to install there
- Bob reports completion

**Estimated time:** 30-60 minutes (depends on Bob's availability)

---

## Status Tracking

| Agent | CLI Installed | Config Updated | Gateway Restarted | Verified | Completed |
|-------|---------------|----------------|-------------------|----------|-----------|
| Bob   | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| Mason | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |
| Forge | ⏳ | ⏳ | ⏳ | ⏳ | ⏳ |

---

## Post-Installation

**After all three agents have Fast.io:**
1. Test file upload from each agent
2. Verify all agents can see same workspace files
3. Document in daily note
4. Update SOP-04 with production agent rollout confirmation

---

**Prepared by:** Testbed  
**Date:** 2026-07-20 16:20 CDT  
**Awaiting:** Execution decision (Option A or B)
