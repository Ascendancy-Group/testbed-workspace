# Fast.io MCP Server - Implementation Plan

**Date:** 2026-07-21  
**Agent:** Testbed  
**Status:** Planning & Build Phase

---

## Executive Summary

Build a Fast.io MCP server on honcho-m1 to give Bob (and later Mason/Forge) programmatic access to Fast.io workspace management through OpenClaw tools.

**Architecture:** HTTP MCP server (same pattern as Dropbox MCP)  
**Location:** honcho-m1 (100.77.0.47), Docker container, port 9091  
**Language:** TypeScript/Node.js  
**Protocol:** HTTP MCP (stdio also supported if needed)

---

## Deployment Architecture

```
honcho-m1 (100.77.0.47)
├── MemPalace (SSH MCP, /opt/mempalace)
├── Honcho Server (HTTP API, port 8000)
├── Dropbox MCP (Docker, port 9090) ✅ Existing
└── Fast.io MCP (Docker, port 9091) ← NEW
```

**All agents connect via Tailscale:**
- Bob (100.126.243.57)
- Mason (100.117.192.71)
- Forge (100.95.36.105)
- Testbed (100.94.9.125)

---

## Current State

### Fast.io Deployment Status

| Agent | CLI Installed | Credentials | API Access | Notes |
|-------|---------------|-------------|------------|-------|
| Testbed | ✅ v0.2.12 | ✅ .env.fastio | ✅ Working | Reference system |
| Bob | ✅ v0.2.12 | ✅ .env.fastio | ✅ Working | Ready for MCP |
| Mason | ❌ Not installed | ❌ Missing | ❌ No access | Needs installation |
| Forge | ❌ Not installed | ❌ Missing | ❌ No access | Needs installation |

### Fast.io Workspace Details

**Workspace:** Ascendancy Group Main Share  
**ID:** 4857845230237369802  
**Owner:** ascendancygroup  
**Storage:** Enabled  
**Intelligence:** ❌ Disabled (requires plan upgrade)  
**Workflow:** ✅ Enabled  
**Assets:** can_edit=true

**Current Contents:**
- 32 items total (12 files + 20 folders)
- Research documents uploaded: 12
- Storage used: Minimal (text files only)

---

## 🎯 DISCOVERY: Fast.io Native MCP Server Available

**Fast.io provides official MCP server endpoints:**
- **Streamable HTTP:** `https://mcp.fast.io/mcp`
- **Legacy SSE:** `https://mcp.fast.io/sse`
- **Skills/Tools:** Available at `/skill.md` endpoint

**Two modes:**
- **Named Mode** (Claude Desktop): Multiple domain-specific tools + widget tools
- **Code Mode** (Cursor, etc.): Streamlined tool set

**Resources available:**
- `skill://guide` - Integration guide
- `session://status` - Session status
- Guided prompts for common workflows

**Authentication:** Bearer token (same as API)

### Decision Point: Native vs Custom MCP Server

**Option A: Use Fast.io Native MCP (RECOMMENDED)**
- ✅ Already built and maintained by Fast.io
- ✅ Zero custom code to maintain
- ✅ Direct connection from agents
- ✅ Automatic updates when Fast.io adds features
- ✅ Immediate deployment (hours, not days)
- ❌ Agents connect directly (distributed, not centralized)
- ❌ No custom circuit breaker/retry logic
- ❌ No centralized monitoring point

**Option B: Build Custom MCP Proxy on honcho-m1**
- ✅ Centralized service on honcho-m1
- ✅ Custom circuit breaker, retry, monitoring
- ✅ Credential management in one place
- ❌ Custom code to build and maintain
- ❌ 12-16 hour build time
- ❌ Duplicate functionality
- ❌ Update lag when Fast.io changes

**Recommended: Option A** - Use native Fast.io MCP server, add centralized monitoring later if needed.

## Implementation Phases (REVISED)

### Phase 1: Test Native Fast.io MCP ✅ IN PROGRESS

**Tasks:**
1. ✅ Snapshot honcho-m1 (pre-fastio-mcp-build-2026-07-21-1007)
2. ✅ Research Fast.io API (https://api.fast.io/llms.txt)
3. Test native MCP connection from Testbed
4. Verify tool availability via `/skill.md`
5. Document authentication flow
6. Test upload, download, list operations

**API Endpoints to Support:**
- Workspace operations (list, info)
- File operations (upload, download, list, delete)
- Folder operations (create, list, delete)
- Search operations (semantic search if Intelligence enabled)
- Share operations (create links, manage permissions)

---

### Phase 2: Deploy to Testbed (Native MCP) ✅ REVISED

**Testbed openclaw.json Configuration:**
```json
{
  "channels": {
    "slack": {
      "mcp": {
        "servers": {
          "fastio": {
            "transport": "http",
            "url": "https://mcp.fast.io/mcp",
            "headers": {
              "Authorization": "Bearer ${FASTIO_TOKEN}"
            }
          }
        }
      }
    }
  }
}
```

**Environment Variables:**
- Add `FASTIO_TOKEN` to Testbed's environment
- Load from `.env.fastio` or systemd service file

**Testing:**
1. Restart gateway: `oc-restart`
2. Verify MCP schema loaded: Check gateway logs
3. List available tools: Query `/skill.md` or inspect MCP tools
4. Test upload via OpenClaw tool
5. Test download, list, search
6. Document all available tools

---

### Phase 3: Local Testing (Testbed)

**Test Environment:**
- Build Docker image on testbed-m1
- Run container locally (port 9091)
- Test all tools via OpenClaw gateway
- Validate error handling (401, 404, 500)
- Test circuit breaker behavior
- Document all operations

**Test Cases:**
1. Upload text file (small, <1MB)
2. Upload binary file (PDF, image)
3. Download existing file
4. List workspace root
5. List nested folder
6. Search for content (if Intelligence enabled)
7. Delete test file
8. Handle missing file (404)
9. Handle auth failure (401)
10. Handle rate limiting (429)

---

### Phase 4: (SKIPPED - Using Native MCP)

**Native MCP eliminates need for honcho-m1 deployment.**

Agents connect directly to `https://mcp.fast.io/mcp`.

**Benefits:**
- No custom server to maintain
- No Docker container
- No port management
- No health monitoring infrastructure needed
- Fast.io handles uptime, updates, monitoring

**Monitoring (if needed later):**
- Gateway logs show MCP tool calls
- Fast.io API provides activity tracking
- Can build centralized monitoring dashboard if Bob needs it

---

### Phase 5: Wire Bob as Intelligent Manager

**Bob's openclaw.json Configuration:**
```json
{
  "channels": {
    "slack": {
      "mcp": {
        "servers": {
          "fastio": {
            "transport": "http",
            "url": "https://mcp.fast.io/mcp",
            "headers": {
              "Authorization": "Bearer ${FASTIO_TOKEN}"
            }
          }
        }
      }
    }
  }
}
```

**Environment Setup:**
- Ensure `FASTIO_TOKEN` available in Bob's systemd service
- Option 1: Add to service file `Environment=`
- Option 2: Load from `.env.fastio` in ExecStartPre
- Option 3: Use 1Password Connect (if available)

**Testing with Bob:**
1. Restart Bob's gateway
2. Verify MCP schema loaded
3. Test upload via Slack command
4. Test download via agent request
5. Test list/search operations
6. Document Bob's workflow

**Bob's Use Cases:**
- Upload research documents to Fast.io
- Download files for analysis
- Search workspace for specific content
- Manage file organization
- Create shared links for Pieter

---

### Phase 6: Rollout to Mason & Forge

**Prerequisites:**
1. Install fastio CLI on Mason-m1
2. Install fastio CLI on Forge-m1
3. Create `.env.fastio` on both servers
4. Test CLI access before MCP config
5. Add MCP config to openclaw.json
6. Restart gateways
7. Verify tool access

---

## Credentials Management

**Token Storage:**
- 1Password: "Fast.io" item (credential field)
- Value: `v7l6kexp2jp488bmmw7g...` (full token)
- Format: Bearer token for API Authorization header

**MCP Server .env:**
```bash
FASTIO_TOKEN=v7l6kexp2jp488bmmw7g...
FASTIO_WORKSPACE_ID=4857845230237369802
PORT=9091
LOG_LEVEL=info
```

**Security:**
- No token in docker-compose.yml (use .env)
- No token in git (add .env to .gitignore)
- Token rotation: Update .env + restart container

---

## Error Handling Strategy

**Circuit Breaker:**
- 5 consecutive failures → OPEN (stop requests)
- 60-second timeout → HALF_OPEN (test request)
- Success → CLOSED (resume normal operation)

**Error Types:**
- 401 Unauthorized → Log + alert (credentials invalid)
- 404 Not Found → Return empty result
- 429 Rate Limited → Exponential backoff + retry
- 500 Server Error → Circuit breaker + fallback
- Network timeout → Retry with exponential backoff

**Logging:**
- All API calls logged (timestamp, method, path, status)
- Errors logged with full stack trace
- Token masked in logs (first 4 chars only)

---

## Documentation Deliverables

1. **README.md** - MCP server usage, setup, troubleshooting
2. **API.md** - Tool schema, parameters, examples
3. **DEPLOYMENT.md** - Docker setup, environment variables
4. **SOP-04 Update** - Add Fast.io MCP section to Cloud Storage SOP
5. **Daily Note** - Build log, test results, deployment steps

---

## Rollback Plan

**If MCP server fails:**
1. Stop container: `docker compose down`
2. Remove from agent openclaw.json
3. Restart agent gateways
4. Agents fall back to CLI access
5. Restore honcho-m1 snapshot if needed

**Snapshot Created:**
- Name: `pre-fastio-mcp-build-2026-07-21-1007`
- Server: Honch01-M1 (ID: 127076404)
- Action ID: 643961633177842
- Status: Running (completion check pending)

---

## Success Criteria

**Phase 1-2 (Build):**
- ✅ MCP server starts without errors
- ✅ Health endpoint returns 200 OK
- ✅ All priority tools implemented
- ✅ TypeScript compiles without errors

**Phase 3 (Testing):**
- ✅ All test cases pass
- ✅ Error handling validated
- ✅ Circuit breaker works
- ✅ Documentation complete

**Phase 4-5 (Deployment):**
- ✅ Bob can upload files via OpenClaw
- ✅ Bob can list workspace contents
- ✅ Bob can download files
- ✅ Bob can search (if Intelligence enabled)
- ✅ Zero downtime deployment

**Phase 6 (Rollout):**
- ✅ Mason & Forge have tool access
- ✅ All agents can manage Fast.io workspace
- ✅ SOP-04 updated with MCP server docs

---

## Timeline (REVISED - Native MCP)

| Phase | Duration | Notes |
|-------|----------|-------|
| Phase 1: Test Native MCP | 1-2 hours | Connection, tool discovery |
| Phase 2: Deploy to Testbed | 30 min | Config + restart |
| Phase 3: Full Testing | 1-2 hours | All tools, error cases |
| Phase 4: (Skipped) | — | Using native MCP |
| Phase 5: Bob Wiring | 1 hour | Config + testing |
| Phase 6: Rollout | 1-2 hours | Mason + Forge |
| **Total** | **4-8 hours** | 50-67% time savings vs custom build |

---

## Next Steps (Immediate)

1. ✅ Snapshot honcho-m1 (IN PROGRESS)
2. Research Fast.io API (https://api.fast.io/llms.txt)
3. Review Fast.io CLI source code (if available)
4. Design MCP tool schema
5. Create project directory: `~/projects/fastio-mcp/`
6. Initialize TypeScript project
7. Implement first tool (workspace_info)
8. Test locally on Testbed

---

**Status:** Snapshot running, proceeding to Phase 1 research

**Updated:** 2026-07-21 10:10 CDT
