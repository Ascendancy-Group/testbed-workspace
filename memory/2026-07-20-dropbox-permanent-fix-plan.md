# Dropbox Permanent Fix Plan — 2026-07-20

## Executive Summary

**Goal:** Fix Dropbox integration permanently - no more upload/read failures.

**Root causes identified:**
1. **MCP server design flaw:** Base64 encoding for large files is unreliable
2. **Transport layer issues:** SSE misconfiguration causing connection spam
3. **Circuit breaker too sensitive:** Opens on first failure, stays open
4. **No file size limits:** Server accepts files it can't handle
5. **No proper chunking:** Large files fail instead of using Dropbox upload sessions

**Solution:** Rebuild Dropbox integration with proper architecture.

**Timeline:** 2-3 days (design → implement → test → deploy)

---

## Current Architecture (Broken)

```
OpenClaw Agent
    ↓ MCP protocol (SSE transport)
    ↓ base64 encode file content
    ↓
Dropbox MCP Server (Docker on honcho-m1)
    ↓ base64 decode (FAILS on large files)
    ↓ Single upload request (no chunking)
    ↓
Dropbox API
```

**Problems:**
- Base64 encoding 23 KB file → 31 KB string (33% overhead)
- Python base64.b64decode() strict about padding
- No chunking for files >5 MB
- Circuit breaker opens, blocks all subsequent uploads
- SSE transport misconfigured, spamming connections

---

## Proposed Architecture (Fixed)

### Option 1: Hybrid Approach (Recommended)

**Small files (< 5 MB):** Direct MCP upload  
**Large files (> 5 MB):** Pre-signed URL upload

```
OpenClaw Agent
    ↓
    ├─ Small file → MCP → base64 → Dropbox API
    └─ Large file → MCP (get pre-signed URL) → Direct HTTPS upload → Dropbox
```

**Benefits:**
- No base64 encoding for large files
- Proper chunking via Dropbox upload sessions
- Circuit breaker only affects small-file path
- Reliable at any file size

---

### Option 2: Rclone Backend (Alternative)

**Architecture:**
```
OpenClaw Agent
    ↓ MCP protocol
    ↓
Rclone MCP Wrapper (new service)
    ↓ rclone commands
    ↓
Dropbox (via rclone mount or sync)
```

**Benefits:**
- Battle-tested reliability (rclone is mature)
- Handles any file size
- Built-in retry logic
- No base64 encoding
- Can also support other cloud providers (S3, GCS, etc.)

**Drawbacks:**
- New service to maintain
- Slightly higher latency

---

### Option 3: Native Dropbox SDK Rewrite

**Rewrite MCP server using official Dropbox SDK upload sessions:**

```python
# For files > 150 MB, use chunked upload
if file_size > 150 * 1024 * 1024:
    # Upload session
    session_id = dbx.files_upload_session_start(chunk1)
    for chunk in remaining_chunks:
        dbx.files_upload_session_append_v2(chunk, session_id)
    dbx.files_upload_session_finish(final_chunk, session_id, path)
else:
    # Single upload
    dbx.files_upload(file_content, path)
```

**Benefits:**
- Proper Dropbox API usage
- Handles any file size correctly
- No MCP protocol changes needed

**Drawbacks:**
- Still uses base64 for MCP transport
- Requires rewrite of upload logic

---

## Recommended Solution

**Hybrid Approach (Option 1) with proper implementation:**

### Phase 1: Fix Current MCP Server (Immediate)

**Changes:**
1. **Add file size validation**
   - Reject files > 5 MB with clear error message
   - Suggest alternative upload method

2. **Fix base64 decoding**
   - Add proper padding normalization
   - Better error messages (not just "Incorrect padding")
   - Validate base64 before decode attempt

3. **Circuit breaker tuning**
   - Increase failure threshold (3 failures before open)
   - Auto-reset after 60 seconds
   - Per-operation circuit breakers (not global)

4. **Fix SSE transport**
   - Investigate SSE endpoint configuration
   - Add connection timeout
   - Implement proper connection pooling

5. **Add retry logic**
   - 3 retries with exponential backoff before circuit breaker
   - Retry on transient errors only (429, 503, timeout)

**Code changes:**
```python
# In dropbox_client.py

import base64
import binascii

MAX_DIRECT_UPLOAD_SIZE = 5 * 1024 * 1024  # 5 MB

def upload_file(self, dropbox_path, content_base64=None, local_path=None, overwrite=False):
    """Upload a file to Dropbox with proper size limits and error handling"""
    
    if content_base64:
        # Normalize base64 padding
        content_base64 = content_base64.strip()
        padding = len(content_base64) % 4
        if padding:
            content_base64 += '=' * (4 - padding)
        
        # Decode with better error handling
        try:
            file_bytes = base64.b64decode(content_base64, validate=True)
        except binascii.Error as e:
            raise ValueError(f"Invalid base64 encoding: {e}. Ensure content is properly base64-encoded.")
        
        # Size validation
        file_size = len(file_bytes)
        if file_size > MAX_DIRECT_UPLOAD_SIZE:
            raise ValueError(
                f"File size ({file_size / 1024 / 1024:.2f} MB) exceeds direct upload limit "
                f"({MAX_DIRECT_UPLOAD_SIZE / 1024 / 1024} MB). "
                f"Use upload_large_file tool or reduce file size."
            )
        
        # Upload with retry
        return self._upload_with_retry(dropbox_path, file_bytes, overwrite)
    
    elif local_path:
        # Read file from local path
        with open(local_path, 'rb') as f:
            file_bytes = f.read()
        
        if len(file_bytes) > MAX_DIRECT_UPLOAD_SIZE:
            return self._upload_large_file(dropbox_path, local_path, overwrite)
        else:
            return self._upload_with_retry(dropbox_path, file_bytes, overwrite)
    
    else:
        raise ValueError("Either content_base64 or local_path must be provided")

def _upload_with_retry(self, dropbox_path, file_bytes, overwrite, max_retries=3):
    """Upload with exponential backoff retry"""
    import time
    
    for attempt in range(max_retries):
        try:
            return self._do_upload(dropbox_path, file_bytes, overwrite)
        except DropboxException as e:
            if e.error.is_rate_limit():
                retry_after = e.error.get_rate_limit().retry_after
                logger.warning(f"Rate limited, retrying after {retry_after}s")
                time.sleep(retry_after)
            elif attempt < max_retries - 1:
                backoff = 2 ** attempt
                logger.warning(f"Upload failed, retry {attempt+1}/{max_retries} in {backoff}s")
                time.sleep(backoff)
            else:
                raise

def _upload_large_file(self, dropbox_path, local_path, overwrite):
    """Upload large file using Dropbox upload session (chunked)"""
    CHUNK_SIZE = 4 * 1024 * 1024  # 4 MB chunks
    
    with open(local_path, 'rb') as f:
        file_size = os.path.getsize(local_path)
        
        # Start session
        chunk = f.read(CHUNK_SIZE)
        session = self.dbx.files_upload_session_start(chunk)
        cursor = UploadSessionCursor(session.session_id, len(chunk))
        
        # Upload remaining chunks
        while True:
            chunk = f.read(CHUNK_SIZE)
            if not chunk:
                break
            self.dbx.files_upload_session_append_v2(chunk, cursor)
            cursor.offset += len(chunk)
        
        # Finish session
        commit = CommitInfo(
            path=dropbox_path,
            mode=WriteMode.overwrite if overwrite else WriteMode.add
        )
        self.dbx.files_upload_session_finish(b'', cursor, commit)
        
        return {"status": "success", "path": dropbox_path, "size": file_size}
```

**Dockerfile update:**
```dockerfile
# Install dependencies for large file handling
RUN pip install dropbox==11.36.2 retry==0.9.2
```

---

### Phase 2: Add Large File Support (Next)

**New MCP tool:**
```python
@mcp.tool()
def upload_large_file(dropbox_path: str, local_path: str, overwrite: bool = False) -> dict:
    """Upload large files (> 5 MB) using Dropbox upload sessions (chunked)"""
    return dbx.upload_large_file(dropbox_path, local_path, overwrite)
```

**Usage from OpenClaw:**
```
For files > 5 MB:
1. Agent writes file to local temp path
2. Agent calls upload_large_file with local_path
3. MCP server reads file, chunks, uploads via Dropbox API
```

---

### Phase 3: Pre-signed URL Upload (Future)

**New workflow for very large files:**
```python
@mcp.tool()
def get_upload_url(dropbox_path: str, file_size: int, overwrite: bool = False) -> dict:
    """Get a pre-signed URL for direct upload to Dropbox (bypasses MCP server)"""
    # Generate Dropbox upload URL
    # Return URL + session info
    return {
        "upload_url": "https://content.dropboxapi.com/...",
        "session_id": "...",
        "chunk_size": 4 * 1024 * 1024
    }

@mcp.tool()
def complete_upload(session_id: str, dropbox_path: str) -> dict:
    """Complete a direct upload session"""
    # Finalize Dropbox upload session
    return {"status": "success", "path": dropbox_path}
```

**Agent workflow:**
```
1. Agent calls get_upload_url
2. Agent uploads file chunks directly to Dropbox (HTTPS, no MCP)
3. Agent calls complete_upload to finalize
```

**Benefits:** No MCP bandwidth, no base64 encoding, handles 100+ GB files

---

## Implementation Plan

### Week 1: Fix Current Issues

**Day 1-2:**
- [ ] Implement base64 padding normalization
- [ ] Add file size validation (5 MB limit)
- [ ] Add retry logic with exponential backoff
- [ ] Tune circuit breaker (3 failures, 60s reset, per-operation)
- [ ] Fix SSE transport configuration

**Day 3:**
- [ ] Test uploads: 1 KB, 100 KB, 1 MB, 5 MB
- [ ] Test failure scenarios (bad base64, network errors)
- [ ] Verify circuit breaker behavior
- [ ] Deploy to honcho-m1

**Deliverables:**
- Dropbox MCP v2.1 (patched)
- Test suite (pytest)
- Updated documentation

---

### Week 2: Add Large File Support

**Day 1-2:**
- [ ] Implement Dropbox upload session logic
- [ ] Add upload_large_file tool
- [ ] Test with 10 MB, 50 MB, 100 MB files

**Day 3:**
- [ ] Integration test with OpenClaw agents
- [ ] Performance benchmarks
- [ ] Deploy to honcho-m1

**Deliverables:**
- Dropbox MCP v2.2 (large file support)
- Performance report
- Updated SOP

---

### Week 3: Monitoring & Documentation

**Day 1:**
- [ ] Add Prometheus metrics
- [ ] Add health check endpoints
- [ ] Set up Grafana dashboard

**Day 2:**
- [ ] Write comprehensive SOP
- [ ] Document all tools + parameters
- [ ] Create troubleshooting guide

**Day 3:**
- [ ] Final testing with all agents
- [ ] Document in ascendancy-infra
- [ ] Close tickets

---

## Alternative: Rclone MCP Server

**If Dropbox MCP rewrite fails or is too complex:**

### Rclone Architecture

**Deploy rclone as MCP wrapper:**
```
┌────────────────────────────────┐
│ Rclone MCP Server (honcho-m1)  │
│ ├─ MCP endpoint                │
│ ├─ rclone binary               │
│ └─ Dropbox config              │
└────────────────────────────────┘
```

**Tools:**
```python
@mcp.tool()
def rclone_copy(source: str, dest: str) -> dict:
    """Copy file using rclone"""
    subprocess.run(['rclone', 'copy', source, f'dropbox:{dest}'])

@mcp.tool()
def rclone_ls(path: str) -> dict:
    """List files using rclone"""
    subprocess.run(['rclone', 'ls', f'dropbox:{path}'])
```

**Benefits:**
- Proven reliability
- Handles any file size
- Built-in retry
- No base64 encoding

**Drawbacks:**
- Shell exec dependency
- Less control over Dropbox API features

---

## Testing Strategy

### Unit Tests
```python
def test_base64_padding_normalization():
    # Test various padding scenarios
    assert upload_file(..., content_base64="SGVsbG8=")  # valid
    assert upload_file(..., content_base64="SGVsbG8")    # missing padding
    
def test_file_size_validation():
    # Test size limits
    with pytest.raises(ValueError, match="exceeds direct upload limit"):
        upload_file(..., content_base64=large_file_b64)

def test_retry_logic():
    # Mock transient failure
    with mock.patch('dropbox.Dropbox.files_upload', side_effect=[RateLimitError(), Success]):
        result = upload_file(...)
        assert result['status'] == 'success'
```

### Integration Tests
```python
def test_end_to_end_upload():
    # OpenClaw → MCP → Dropbox
    # Verify file appears in Dropbox
    
def test_large_file_chunked_upload():
    # Upload 50 MB file
    # Verify chunking works
    
def test_circuit_breaker_recovery():
    # Trigger circuit breaker
    # Wait for auto-reset
    # Verify uploads resume
```

---

## Rollback Plan

**If new implementation fails:**
1. Revert to previous Docker image (dropbox-mcp:v2.0)
2. Restart container: `docker compose up -d`
3. Document failure in daily note
4. Alert Pieter

**Rollback time:** < 5 minutes

---

## Success Criteria

- [ ] Upload 1 KB file: Success
- [ ] Upload 1 MB file: Success
- [ ] Upload 5 MB file: Success
- [ ] Upload 50 MB file: Success (chunked)
- [ ] Circuit breaker auto-resets after 60s
- [ ] Retry logic handles transient failures
- [ ] No SSE connection spam
- [ ] Prometheus metrics exposed
- [ ] All agents can upload without errors
- [ ] 7 days no Dropbox failures

---

## Resources Needed

**Access:**
- [ ] Fable 5 (if needed for reference/debugging)
- [ ] Dropbox API documentation (official)
- [ ] Existing MCP server code (honcho-m1)

**Tools:**
- Python 3.12
- Dropbox SDK 11.36.2
- Docker
- pytest

**Time:**
- Week 1: Fix current issues (20 hours)
- Week 2: Large file support (15 hours)
- Week 3: Monitoring + docs (10 hours)
- **Total: 45 hours over 3 weeks**

---

## Approval Required

**Before proceeding:**
- [ ] Pieter approves this plan
- [ ] Pieter grants Fable 5 access (if needed)
- [ ] Pieter confirms timeline acceptable (3 weeks)

**Once approved:**
- Start Week 1 immediately
- Daily progress updates in #testing-env--public
- Commit all changes to ascendancy-infra

---

*Plan created: 2026-07-20 03:45 UTC*  
*Planner: Testbed*  
*Approval required: Pieter van der Wal*  
*Target: Zero Dropbox failures after implementation*
