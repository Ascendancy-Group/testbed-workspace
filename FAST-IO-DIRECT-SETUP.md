# Fast.io Direct Integration (No ClawHub)

**Two secure methods to integrate Fast.io with OpenClaw - NO ClawHub required**

---

## Option 1: Fastio CLI (Recommended - Shell-Native)

**Why:** Direct shell commands, no skill registry, no ClawHub dependency

### Installation

```bash
# Install Fastio CLI globally
npm install --global @vividengine/fastio-cli
```

**Verify:**
```bash
fastio --version
```

---

### Authentication

**Method A: Interactive Login (Browser OAuth)**
```bash
fastio auth login
```
- Opens browser
- Login to Fast.io
- Approves access
- Session stored locally (~/.fastio/)

**Method B: API Token**
```bash
# Get token from Fast.io dashboard → Settings → API Keys
# (Or: Profile → Developer → API Tokens)
fastio auth token <YOUR_API_TOKEN>
```

---

### Usage from OpenClaw

**OpenClaw agents can now invoke `fastio` commands directly:**

```bash
# Create workspace
fastio workspace create ascendancy-research --intelligence

# Upload file
fastio file upload ~/.openclaw/workspace/memory/2026-07-19-mempalace-fork-analysis.md \
  --workspace ascendancy-research \
  --path /research-documents/

# List files
fastio file list --workspace ascendancy-research

# Search files
fastio search "MemPalace critical fixes" --workspace ascendancy-research

# AI query (if Intelligence Mode enabled)
fastio chat ask "What are the n8n cost savings?" --workspace ascendancy-research

# Create share
fastio share create --workspace ascendancy-research --type send --password --expires 30d
```

---

### OpenClaw Integration

**Add to agent's shell tools via exec:**

OpenClaw can call `fastio` CLI commands through the `exec` tool:

```
Agent receives: "Upload research docs to Fast.io"
↓
Agent: exec("fastio file upload /path/to/docs --workspace research")
↓
Result: File uploaded, returns path
```

**No MCP server needed** - just shell commands

---

### Advantages

✅ **No ClawHub dependency** - pure CLI tool  
✅ **Shell-native** - works with existing OpenClaw exec tool  
✅ **Scriptable** - JSON output, pipe to jq  
✅ **Cross-platform** - Rust binary (macOS, Linux, Windows)  
✅ **Everything included** - upload, download, search, AI chat, shares  
✅ **Built-in MCP server** - CLI includes optional MCP server if needed later

---

## Option 2: Direct MCP Connection (No ClawHub)

**Why:** Native MCP protocol, full control, no third-party skill registry

### MCP Endpoints

**Fast.io provides two MCP transports:**
- Streamable HTTP: `https://mcp.fast.io/mcp`
- SSE (legacy): `https://mcp.fast.io/sse`

**Recommended:** Streamable HTTP

---

### Get Authentication Token

**Method A: OAuth Flow (Secure)**

1. Visit: https://fast.io/auth/oauth/authorize
2. Approve access
3. Get bearer token
4. Store in 1Password

**Method B: API Token (Simpler)**

1. Fast.io dashboard → Settings → API Keys (or Profile → Developer)
2. Create API token
3. Copy token
4. Store in 1Password

---

### Configure OpenClaw

**Edit:** `~/.openclaw/openclaw.json`

**Add to `mcpServers`:**

```json
{
  "mcpServers": {
    "fastio": {
      "transport": "http",
      "url": "https://mcp.fast.io/mcp",
      "headers": {
        "Authorization": "Bearer…KEN>"
      }
    }
  }
}
```

**Restart gateway:**
```bash
systemctl --user restart openclaw-gateway.service
```

---

### Verify Tools Available

**Check logs:**
```bash
journalctl --user -u openclaw-gateway.service -n 100 | grep -i fastio
```

**Expected:** MCP server registered, tools loaded

**Available tools (19 total):**
- fastio__workspace_create
- fastio__workspace_list
- fastio__file_upload
- fastio__file_download
- fastio__file_list
- fastio__file_search
- fastio__ai_chat
- fastio__share_create
- fastio__intelligence_toggle
- ... and 10 more

---

### Test Upload

**Via OpenClaw MCP:**

```bash
# The agent will use MCP tools naturally via chat:
"Upload file ~/.openclaw/workspace/memory/2026-07-19-mempalace-fork-analysis.md to Fast.io workspace ascendancy-research"
```

**Agent invokes:** `fastio__file_upload` MCP tool

**Result:** File uploaded

---

## Comparison

| Feature | CLI Method | Direct MCP |
|---------|-----------|------------|
| **Setup complexity** | Low (npm install) | Low (JSON config) |
| **ClawHub dependency** | ❌ None | ❌ None |
| **Authentication** | OAuth or API token | Bearer token in config |
| **OpenClaw integration** | exec tool | Native MCP tools |
| **Scriptability** | ✅ High (shell) | Medium (MCP only) |
| **Performance** | Fast (direct) | Fast (HTTP) |
| **Security** | Token in ~/.fastio/ | Token in openclaw.json |

**Both methods are secure and ClawHub-free.**

---

## Recommended Approach

**Use CLI method for Testbed:**
1. Install CLI: `npm install --global @vividengine/fastio-cli`
2. Auth: `fastio auth login` (browser OAuth)
3. Use: OpenClaw agents call `fastio` commands via exec

**Why:** 
- No ClawHub
- No MCP config changes needed
- Works with existing exec tool
- Shell-native (agents already know how to exec)
- Can script complex workflows

**For production rollout:**
- Deploy CLI on all agent machines
- One-time auth per machine
- Document `fastio` commands in agent SOPs

---

## Implementation Plan

### Phase 1: Install CLI on Testbed (5 min)

```bash
# On testbed-m1
npm install --global @vividengine/fastio-cli

# Verify
fastio --version

# Authenticate
fastio auth login
# (Opens browser, login, approve, done)

# Test
fastio workspace list
```

---

### Phase 2: Upload Research Docs (5 min)

```bash
# Create workspace (if not exists)
fastio workspace create ascendancy-research --intelligence

# Upload all docs
cd ~/.openclaw/workspace/memory
for file in 2026-07-*.md; do
  fastio file upload "$file" \
    --workspace ascendancy-research \
    --path /research-documents/
done

# Verify
fastio file list --workspace ascendancy-research
```

---

### Phase 3: Test from OpenClaw (2 min)

**Via chat to Testbed agent:**
```
"List files in Fast.io workspace ascendancy-research"
```

**Agent uses exec:**
```bash
exec("fastio file list --workspace ascendancy-research --output json")
```

**Returns:** JSON list of files

---

### Phase 4: Roll Out to Other Agents (10 min)

**On each agent machine (Bob, Mason, Forge):**

```bash
# Install CLI
npm install --global @vividengine/fastio-cli

# Authenticate
fastio auth login

# Test
fastio workspace list
```

**Done.** All agents can now use Fast.io via exec.

---

### Phase 5: Decommission Dropbox (5 min)

```bash
# Stop Dropbox MCP
ssh pieter@100.77.0.47
cd ~/docker/dropbox-mcp
docker compose down

# Backup
cp docker-compose.yml docker-compose.yml.backup-20260720
```

---

## Success Criteria

- [ ] Fastio CLI installed on testbed-m1
- [ ] Authenticated via browser OAuth
- [ ] Workspace "ascendancy-research" created
- [ ] All 6 research docs uploaded
- [ ] Intelligence Mode enabled
- [ ] OpenClaw agent can list files via exec
- [ ] CLI installed on Bob, Mason, Forge
- [ ] All agents authenticated
- [ ] Dropbox MCP stopped

---

## Security Notes

**CLI Method:**
- Auth token stored in `~/.fastio/credentials`
- File permissions: 600 (owner read/write only)
- Per-machine authentication
- OAuth flow (no API keys in config files)

**Direct MCP Method:**
- Bearer token in `~/.openclaw/openclaw.json`
- File permissions: 600 (should be)
- Shared token across agents (less ideal)

**Recommendation:** CLI method is more secure (per-machine OAuth)

---

## Timeline

**Total:** 27 minutes for complete migration

| Phase | Time |
|-------|------|
| Install CLI on Testbed | 5 min |
| Upload docs | 5 min |
| Test from OpenClaw | 2 min |
| Roll out to agents | 10 min |
| Decommission Dropbox | 5 min |

---

## Next Step

**Ready to execute CLI method?**

Just confirm and I'll:
1. Install Fastio CLI on testbed-m1
2. Authenticate via browser OAuth
3. Upload all 6 research documents
4. Test from OpenClaw
5. Roll out to other agents

**No ClawHub. No security risks. Pure shell tools.** ✅

---

*Plan created: 2026-07-20 05:10 UTC*  
*Method: Fastio CLI (shell-native, no ClawHub)*  
*Executor: Testbed*
