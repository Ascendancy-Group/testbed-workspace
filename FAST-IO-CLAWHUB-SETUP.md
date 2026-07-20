# Fast.io Setup via ClawHub — Correct Method

**Discovery:** Fast.io for OpenClaw uses **ClawHub skill** with OAuth - no manual API keys needed!

---

## Method 1: ClawHub Skill (Recommended for OpenClaw)

### Step 1: Install ClawHub CLI (Me - Testbed)

```bash
npm install -g @clawhub/cli
```

**Verify:**
```bash
clawhub list
```

---

### Step 2: Install Fast.io Skill (Me - Testbed)

```bash
clawhub install dbalve/fast-io
```

**What this does:**
- Adds 14 Fastio MCP tools to OpenClaw
- Sets up OAuth authentication flow
- No manual API key configuration needed

**Restart OpenClaw:**
```bash
systemctl --user restart openclaw-gateway.service
```

---

### Step 3: Authenticate via Chat (Me - via OpenClaw)

**In OpenClaw chat, I'll say:**
```
"Sign into Fastio"
```

**OpenClaw will respond with:**
- Option 1: API Key method (paste key from Fast.io dashboard)
- Option 2: PKCE Login (browser OAuth flow)
- Option 3: Signup (create agent account)

**I'll choose:** PKCE Login (most secure, no API key needed)

**Flow:**
1. OpenClaw gives me a browser URL
2. I open URL in browser
3. Login to Fast.io
4. Approve access
5. Copy code from browser
6. Paste code back to OpenClaw

**Result:** Authenticated, session persists

---

### Step 4: Create/Access Workspace

**Via OpenClaw chat:**
```
"List my Fastio workspaces"
```

**If workspace already exists:**
```
"Switch to workspace 'ascendancy-research'"
```

**If need to create:**
```
"Create Fastio workspace 'ascendancy-research' with intelligence enabled"
```

---

### Step 5: Upload Research Documents

**Via OpenClaw chat:**
```
"Upload file ~/.openclaw/workspace/memory/2026-07-19-mempalace-fork-analysis.md to Fastio workspace 'ascendancy-research'"
```

**Repeat for all 6 files:**
- 2026-07-19-mempalace-fork-analysis.md
- 2026-07-20-mempalace-upgrade-plan.md
- 2026-07-20-n8n-research-integration-plan.md
- 2026-07-20-zapier-vs-n8n-detailed-comparison.md
- 2026-07-20-dropbox-permanent-fix-plan.md
- 2026-07-20-fastio-evaluation.md

---

### Step 6: Test Semantic Search

**Via OpenClaw chat:**
```
"What are the MemPalace critical fixes?"
```

**Expected:** Cited answer from uploaded research docs

---

### Step 7: Roll Out to Other Agents

**On each agent machine (Bob, Mason, Forge):**

```bash
# Install ClawHub CLI
npm install -g @clawhub/cli

# Install Fast.io skill
clawhub install dbalve/fast-io

# Restart gateway
systemctl --user restart openclaw-gateway.service
```

**Then via chat on each agent:**
```
"Sign into Fastio"
```

*Follow PKCE login flow (browser → approve → paste code)*

---

## Method 2: Manual API Key (Alternative)

**If ClawHub doesn't work, fall back to manual config:**

### Get API Key

**You (Pieter):**
1. Fast.io dashboard → Settings → API Keys (or go.fast.io/settings/api-keys)
2. Create API key
3. Copy key

**Alternative if no API Keys section:**
- Click profile → Developer → Generate Token
- Or use PKCE login URL from Fast.io dashboard

---

### Configure OpenClaw Manually

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

---

## What You Need to Do (Pieter)

**Option A: Nothing (Recommended)**
- Let me handle ClawHub skill installation
- I'll authenticate via PKCE OAuth (no API key needed)
- You just verify workspace exists in Fast.io dashboard

**Option B: If you prefer API key method**
- Go to Fast.io → Settings → API Keys (or profile → Developer)
- Generate API key
- Share with me

---

## Timeline

| Step | Duration | Who |
|------|----------|-----|
| Install ClawHub CLI | 2 min | Testbed |
| Install Fast.io skill | 2 min | Testbed |
| OAuth authentication | 3 min | Testbed |
| Upload 6 documents | 5 min | Testbed |
| Test semantic search | 2 min | Testbed |
| Roll out to other agents | 10 min | Testbed |
| **TOTAL** | **24 min** | |

---

## Next Step

**I'll proceed with ClawHub method (no API key needed):**

1. Install ClawHub CLI on testbed-m1
2. Install Fast.io skill
3. Authenticate via PKCE OAuth
4. Upload all research documents
5. Test semantic search
6. Roll out to other agents

**You don't need to do anything** - I'll handle the full setup via ClawHub!

**Ready to proceed?** Just confirm and I'll start immediately.

---

*Updated: 2026-07-20 05:10 UTC*  
*Method: ClawHub skill with OAuth (no manual API key)*  
*Executor: Testbed*
