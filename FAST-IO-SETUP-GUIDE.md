# Fast.io Setup Guide — Step-by-Step

**For:** Pieter van der Wal  
**Goal:** Get Fast.io API key and integrate with OpenClaw agents  
**Time:** 10-15 minutes total

---

## Step 1: Get Fast.io API Key (You)

### 1.1 Log into Fast.io Dashboard

**URL:** https://fast.io/ or https://app.fast.io/

**Login with:** Your Fast.io account credentials

---

### 1.2 Navigate to API Keys

**Path:** Click your profile icon (bottom-left) → **Settings** → **API Keys**

**Alternative path:** **Account & Admin** → **API Keys**

---

### 1.3 Create New API Key

**Click:** "Create API Key" button

**Name it:** `OpenClaw-Ascendancy` (or similar descriptive name)

**Scopes:** 
- If prompted, grant full workspace access
- Select your newly created workspace

**Click:** "Create"

---

### 1.4 Copy the API Key

**⚠️ IMPORTANT:** The API key is shown **ONLY ONCE**

**Copy immediately:** The key will look like: `sk-fast-xxxxxxxxxxxxxxxxxxxxxxxx`

**DO NOT CLOSE** the dialog until you've saved it!

---

### 1.5 Store in 1Password

**Create new item in 1Password:**

```
Title: Fast.io API Key - Ascendancy
Vault: AgentStack
Type: API Credential

Fields:
- API Key: sk-fast-xxxxxxxxxxxxxxxxxxxxxxxx
- Workspace Name: [your workspace name]
- Workspace ID: [if shown in dashboard]
- Created: 2026-07-20
- Purpose: OpenClaw agent file storage
```

**Click:** "Done" in Fast.io dialog after saving to 1Password

---

## Step 2: Share with Testbed (You)

**Send to me in #testing-env--public:**

```
Fast.io API Key: sk-fast-xxxxxxxxxxxxxxxxxxxxxxxx
Workspace Name: [name]
```

(I'll configure it immediately and delete from chat history after setup)

**Alternative:** Just tell me it's in 1Password and I'll retrieve it via `op` command

---

## Step 3: I Configure Testbed (Me)

### 3.1 Add to OpenClaw Config

**File:** `/home/pieter/.openclaw/openclaw.json`

**Add this to `mcpServers` section:**

```json
{
  "mcpServers": {
    "fastio": {
      "transport": "http",
      "url": "https://mcp.fast.io/mcp",
      "headers": {
        "Authorization": "Bearer sk-fast-xxxxxxxxxxxxxxxxxxxxxxxx"
      }
    }
  }
}
```

---

### 3.2 Restart Gateway

```bash
systemctl --user restart openclaw-gateway.service
```

---

### 3.3 Verify MCP Tools Available

**Check logs:**
```bash
journalctl --user -u openclaw-gateway.service -n 50 | grep fastio
```

**Expected:** MCP server registered, tools loaded

---

### 3.4 Test Upload

**Create test file:**
```bash
echo "Fast.io integration test - $(date)" > /tmp/fastio-test.txt
```

**Upload via MCP tool:**
- Tool: `fastio__write_file` or `fastio__upload_file`
- Path: `/research-documents/test-2026-07-20.txt`
- Content: test file

**Expected:** Success, file appears in Fast.io dashboard

---

### 3.5 Upload All Research Documents

**Files:**
1. 2026-07-19-mempalace-fork-analysis.md
2. 2026-07-20-mempalace-upgrade-plan.md
3. 2026-07-20-n8n-research-integration-plan.md
4. 2026-07-20-zapier-vs-n8n-detailed-comparison.md
5. 2026-07-20-dropbox-permanent-fix-plan.md
6. 2026-07-20-fastio-evaluation.md

**Destination:** `/research-documents/` folder

**Method:** Loop through files, upload each via MCP

---

## Step 4: Enable Intelligence Mode (You)

### 4.1 Go to Workspace Settings

**Path:** Fast.io dashboard → Your workspace → Settings

---

### 4.2 Toggle Intelligence Mode

**Setting:** Intelligence Mode → **Toggle ON**

**What happens:**
- Files automatically indexed for semantic search
- Enables RAG queries across documents
- Allows natural language questions about content

---

### 4.3 Test Semantic Search

**Try asking:**
- "What are the MemPalace critical fixes?"
- "How much do we save with n8n vs Zapier?"
- "What is the Fast.io recommendation?"

**Expected:** Cited answers from uploaded research docs

---

## Step 5: Roll Out to Other Agents (Me)

### 5.1 Configure Bob

**SSH to bobwebdev-m1:**
```bash
ssh pieter@[bob-ip]
```

**Edit:** `/home/pieter/.openclaw/openclaw.json`

**Add same Fast.io MCP config**

**Restart:** `systemctl --user restart openclaw-gateway.service`

---

### 5.2 Configure Mason

**Same process on mason-m1**

---

### 5.3 Configure Forge

**Same process on forge-m1**

---

### 5.4 Verify All Agents

**Test:** Each agent can list files in Fast.io workspace

**Expected:** All agents see research documents

---

## Step 6: Decommission Dropbox MCP (Me)

### 6.1 Stop Dropbox MCP Service

**SSH to honcho-m1:**
```bash
ssh pieter@100.77.0.47
cd ~/docker/dropbox-mcp
docker compose down
```

---

### 6.2 Backup Config (Just in Case)

```bash
cp docker-compose.yml docker-compose.yml.backup-20260720
tar czf ~/dropbox-mcp-backup-20260720.tar.gz ~/docker/dropbox-mcp/
```

---

### 6.3 Update Documentation

**Files to update:**
- `ascendancy-governance/playbook/sops/SOP-XX-file-storage.md`
- Remove Dropbox MCP references
- Add Fast.io usage instructions

---

## Success Checklist

- [ ] Fast.io API key generated
- [ ] API key saved in 1Password (AgentStack)
- [ ] API key shared with Testbed
- [ ] Fast.io MCP configured on Testbed
- [ ] Gateway restarted successfully
- [ ] Test upload: Success
- [ ] All 6 research documents uploaded
- [ ] Documents visible in Fast.io dashboard
- [ ] Intelligence Mode enabled
- [ ] Semantic search working
- [ ] Fast.io MCP configured on Bob
- [ ] Fast.io MCP configured on Mason
- [ ] Fast.io MCP configured on Forge
- [ ] All agents verified working
- [ ] Dropbox MCP stopped
- [ ] Dropbox MCP backed up
- [ ] Documentation updated

---

## Timeline

| Phase | Duration | Who |
|-------|----------|-----|
| Get API key | 5 min | Pieter |
| Share with Testbed | 1 min | Pieter |
| Configure Testbed | 5 min | Testbed |
| Test & upload docs | 5 min | Testbed |
| Enable Intelligence Mode | 2 min | Pieter |
| Roll out to agents | 10 min | Testbed |
| Decommission Dropbox | 5 min | Testbed |
| **TOTAL** | **33 min** | |

---

## What You Need to Do (Pieter)

**Right now:**
1. ✅ Log into Fast.io dashboard
2. ✅ Go to Settings → API Keys
3. ✅ Create API key named "OpenClaw-Ascendancy"
4. ✅ Copy the key (shown only once!)
5. ✅ Save in 1Password (AgentStack vault)
6. ✅ Share key with me in #testing-env--public

**After I upload docs:**
7. ✅ Go to Fast.io workspace settings
8. ✅ Enable Intelligence Mode
9. ✅ Test semantic search

**That's it!** I handle all the technical config.

---

## Troubleshooting

### "I can't find API Keys in settings"

**Try:** Profile icon → Account & Admin → API Keys

**Alternative:** Look for "Developers" or "Integrations" menu

---

### "The API key dialog closed before I copied it"

**Solution:** Create a new API key (you can have multiple)

**Then:** Delete the unused one after copying the new one

---

### "I don't see Intelligence Mode toggle"

**Check:** Your plan includes Intelligence Mode (should be on Starter+)

**Alternative:** Contact Fast.io support to enable

---

## Need Help?

**Stuck on any step?** Just tell me where you are and I'll guide you through it.

**Ready to proceed?** Share the API key and I'll handle the rest!

---

*Guide created: 2026-07-20 05:05 UTC*  
*For: Pieter van der Wal*  
*By: Testbed*
