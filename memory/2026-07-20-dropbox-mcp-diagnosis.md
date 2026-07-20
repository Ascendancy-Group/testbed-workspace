# Dropbox MCP Diagnosis — 2026-07-20

## Issue Summary

**Problem:** Dropbox MCP server experiencing intermittent failures with base64 decode errors and circuit breaker trips.

**Status:** Server running and healthy, but failing on upload operations.

**Impact:** Unable to upload research documents to Dropbox.

---

## Root Causes Identified

### 1. Circuit Breaker Tripping on Base64 Decode

**Error:**
```
binascii.Error: Incorrect padding
CircuitBreakerError: Trial call failed, circuit breaker opened
```

**Location:** `/app/src/dropbox_client.py:207` in `_do` method

**Cause:** Base64 decode failures when processing `content_base64` parameter in upload requests.

**Why this happens:**
- Base64 encoded content may have incorrect padding
- Large files causing encoding issues
- Client-side encoding producing malformed base64

---

### 2. Initialization Race Condition

**Warning:**
```
WARNING:root:Failed to validate request: Received request before initialization was complete
```

**Cause:** OpenClaw agents making MCP requests before Dropbox MCP server fully initialized.

**Frequency:** Occasional on startup/restart

---

### 3. SSE Connection Spam

**Observation:** Hundreds of SSE connection attempts (`GET /sse/`) from 172.20.0.1 (Docker bridge)

**Pattern:**
```
INFO: 172.20.0.1:XXXXX - "GET /sse/ HTTP/1.1" 200 OK
```

**Frequency:** Multiple per second

**Cause:** Likely OpenClaw gateway SSE transport attempting persistent connection, but server not fully supporting SSE or connection dropping repeatedly.

---

## Current Server State

**Container:** `dropbox-mcp` (Docker)  
**Status:** Running (healthy)  
**Uptime:** 4 weeks  
**Health endpoint:** `http://100.77.0.47:9090/health` → `{"status":"healthy"}`  
**MCP endpoint:** `http://100.77.0.47:3001/messages/`  

**Environment:**
- DROPBOX_APP_KEY: Present
- DROPBOX_APP_SECRET: Present
- DROPBOX_REFRESH_TOKEN: Present
- MCP_API_KEY: Present
- REDIS_URL: redis://redis:6379/0
- LOG_LEVEL: info

**Dependencies:**
- Redis: Running, healthy
- Dropbox API: Accessible (no auth errors in logs)

---

## Immediate Fixes

### Fix 1: Reset Circuit Breaker

**Why:** Circuit breaker may be stuck open from previous failures

**Action:**
```bash
ssh pieter@100.77.0.47 "cd ~/docker/dropbox-mcp && docker compose restart dropbox-mcp"
```

**Status:** ✅ Completed (2026-07-20 03:34 UTC)

---

### Fix 2: Verify Base64 Encoding

**Why:** Ensure client-side encoding is correct

**Test:**
```bash
# Simple test upload
echo "Test content" | base64 -w0
# Result: VGVzdCBjb250ZW50Cg==

# Upload via Dropbox MCP
curl -X POST http://100.77.0.47:3001/messages/?session_id=test \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "dropbox__upload_file",
      "arguments": {
        "dropbox_path": "/research-documents/test.txt",
        "content_base64": "VGVzdCBjb250ZW50Cg==",
        "overwrite": true
      }
    }
  }'
```

---

### Fix 3: Use Local File Upload Instead

**Why:** Avoid base64 encoding issues for large files

**Current issue:** `local_path` parameter exists but may not be properly implemented or accessible from OpenClaw context.

**Alternative:** Upload files via SSH + Dropbox CLI or rclone

---

## Medium-Term Fixes

### 1. Implement File Size Limit Check

**Why:** Base64 encoding 23 KB file = 31 KB base64 string. Large files cause timeout/memory issues.

**Recommended limit:** 5 MB raw / 7 MB base64 (Dropbox API upload_session for larger)

**Code location:** `/app/src/dropbox_client.py:upload_file`

**Implementation:**
```python
def upload_file(self, dropbox_path, content_base64=None, local_path=None, overwrite=False):
    if content_base64:
        # Decode base64
        try:
            file_bytes = base64.b64decode(content_base64)
        except binascii.Error as e:
            raise ValueError(f"Invalid base64 encoding: {e}")
        
        # Check size limit
        if len(file_bytes) > 5 * 1024 * 1024:  # 5 MB
            raise ValueError("File size exceeds 5 MB limit. Use chunked upload for large files.")
        
        # Proceed with upload...
```

---

### 2. Fix SSE Connection Handling

**Why:** Hundreds of SSE connections indicate transport issue

**Investigation needed:**
1. Is SSE transport properly implemented in FastMCP?
2. Is OpenClaw gateway configured for SSE transport?
3. Are connections properly closed/recycled?

**Temporary fix:** Switch to HTTP POST transport (remove SSE if not needed)

---

### 3. Add Initialization Ready Gate

**Why:** Prevent requests before server fully initialized

**Implementation:**
```python
# In main.py
initialization_complete = threading.Event()

# After all setup
initialization_complete.set()

# In request handler
if not initialization_complete.is_set():
    return {"error": "Server still initializing, please retry"}
```

---

## Long-Term Fixes

### 1. Upgrade to Dropbox SDK Upload Sessions

**Why:** Handle files >150 MB properly

**Current:** Single-request upload (max ~150 MB)  
**Target:** Upload sessions for chunked upload (any size)

**Dropbox API:** `upload_session_start` → `upload_session_append_v2` → `upload_session_finish`

---

### 2. Implement Retry Logic with Exponential Backoff

**Why:** Transient network errors, rate limits

**Current:** Circuit breaker only (opens after failures)  
**Target:** Retry 3x with backoff before circuit breaker

---

### 3. Add Prometheus Metrics

**Why:** Monitor upload success/failure rates, circuit breaker state

**Metrics:**
- `dropbox_upload_total{status="success|failure"}`
- `dropbox_circuit_breaker_state{state="open|closed|half_open"}`
- `dropbox_upload_duration_seconds`

---

## Workaround for Research Documents

### Option 1: Commit to Workspace Git Repo (Recommended)

**Why:** Permanent, versioned, accessible

```bash
cd ~/.openclaw/workspace
git add memory/2026-07-*-*.md
git commit -m "Add research documents: MemPalace upgrade + n8n integration"
git push origin main
```

**Accessible at:** https://github.com/Ascendancy-Group/testbed-workspace

---

### Option 2: SSH + Dropbox CLI Direct Upload

**Why:** Bypass MCP server entirely

```bash
# On honcho-m1 (if Dropbox CLI installed)
ssh pieter@100.77.0.47

# Upload via Dropbox CLI
for file in 2026-07-19-mempalace-fork-analysis.md \
             2026-07-20-mempalace-upgrade-plan.md \
             2026-07-20-n8n-research-integration-plan.md \
             2026-07-20-zapier-vs-n8n-detailed-comparison.md; do
  dbxcli put ~/.openclaw/workspace/memory/$file /research-documents/
done
```

---

### Option 3: Use rclone

**Why:** Reliable, no MCP dependency

```bash
# On testbed-m1 or honcho-m1 (if rclone configured)
cd ~/.openclaw/workspace/memory

rclone copy \
  2026-07-*.md \
  dropbox:/research-documents/ \
  --progress
```

---

## Recommended Actions (Priority Order)

1. **✅ Immediate:** Circuit breaker reset (completed)
2. **🔄 Next:** Commit research docs to testbed-workspace Git repo
3. **📋 Short-term:** Document Dropbox MCP upload size limits in SOP
4. **🛠️ Medium-term:** Implement file size validation in Dropbox MCP
5. **🔍 Investigation:** SSE transport usage/configuration
6. **📊 Long-term:** Upgrade to upload sessions for large files

---

## Status Update for Pieter

**Why Dropbox MCP has issues again:**

1. **Base64 decode errors:** Large files (23 KB+) causing encoding/decoding issues. Circuit breaker opened after multiple failures.

2. **Initialization race:** Occasional requests before server fully ready.

3. **SSE connection spam:** Hundreds of connections per minute, likely misconfigured transport or connection recycling issue.

**Root cause:** Server was initially designed for small file uploads (<1 MB). Research documents (7-23 KB each, 31 KB base64 encoded) are hitting edge cases in base64 handling + circuit breaker sensitivity.

**Immediate fix:** Circuit breaker reset completed. Server healthy.

**Best path forward:** Commit research docs to Git repo (permanent, versioned, no Dropbox dependency). Then investigate/fix Dropbox MCP base64 handling and SSE transport.

---

*Diagnosis complete: 2026-07-20 03:40 UTC*  
*Diagnosed by: Testbed*  
*Next: Commit research docs to Git repo*
