# MemPalace Migration Completion Plan — 2026-06-22

**Goal:** Complete MemPalace migration to honcho-m1 and enable on Testbed today.

---

## Current State

### honcho-m1
- ✅ MemPalace 3.3.0 installed
- ✅ Palace directory `/opt/mempalace` exists
- ✅ Palace initialized (empty, 0 drawers)
- ⚠️ No MCP network server running (stdio-only limitation confirmed 2026-06-19)

### testbed-m1
- ✅ Local MemPalace 3.3.0 installed
- ✅ Local palace at `~/.mempalace` (validated 2026-05-19)
- ❌ Not configured to use honcho-m1 palace
- ❌ MCP tools not wired in openclaw.json

---

## Architecture Decision (from 2026-06-19 research)

**Problem:** MemPalace MCP server is stdio-only, no HTTP/WebSocket mode.

**Solution:** Use SSH + stdio approach:
- Each agent's openclaw.json runs `ssh pieter@100.77.0.47 python3 -m mempalace.mcp_server`
- MCP tools communicate via SSH tunnel to honcho-m1
- `MEMPALACE_DIR=/opt/mempalace` environment variable points to centralized palace

**Benefits:**
- No custom proxy needed
- Leverages existing Tailscale auth
- Works with current MemPalace version

**Tradeoffs:**
- SSH overhead per call (acceptable for memory operations)
- Requires SSH key setup for non-interactive auth

---

## Completion Tasks

### Task 1: Verify SSH key auth (testbed → honcho-m1)
**Status:** To verify

```bash
ssh pieter@100.77.0.47 "echo SSH auth working"
```

**Expected:** No password prompt, immediate response.

**If fails:** 
- Copy SSH key: `ssh-copy-id pieter@100.77.0.47`
- Test again

---

### Task 2: Backup testbed openclaw.json
**Status:** Pending

```bash
cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-mempalace-network-$(date +%Y%m%d-%H%M%S)
```

---

### Task 3: Add MemPalace MCP config to testbed openclaw.json
**Status:** Pending

**Target config:**
```json
{
  "mcp": {
    "servers": {
      "mempalace": {
        "command": "ssh",
        "args": [
          "pieter@100.77.0.47",
          "python3",
          "-m",
          "mempalace.mcp_server"
        ],
        "env": {
          "MEMPALACE_DIR": "/opt/mempalace"
        }
      }
    }
  }
}
```

**Method:**
1. Read current openclaw.json
2. Add/merge MCP config
3. Write updated JSON
4. Verify JSON syntax

---

### Task 4: Restart testbed gateway
**Status:** Pending

```bash
oc-restart
```

Wait for gateway to come up (check logs).

---

### Task 5: Verify MCP tools available
**Status:** Pending

**Test 1: List available tools**
```bash
# Check tool list includes mempalace_* tools
```

**Test 2: Run mempalace_status**
Use `mempalace__mempalace_status` tool in this session.

**Expected result:** Should show honcho-m1 palace status (0 drawers initially).

---

### Task 6: Migrate testbed memory to honcho-m1
**Status:** Pending

**Steps:**
1. Export testbed local palace
   ```bash
   cd ~/.mempalace
   tar czf /tmp/testbed-mempalace-export-$(date +%Y%m%d).tar.gz .
   ```

2. Transfer to honcho-m1
   ```bash
   scp /tmp/testbed-mempalace-export-*.tar.gz pieter@100.77.0.47:/tmp/
   ```

3. Import to honcho-m1
   ```bash
   ssh pieter@100.77.0.47 "cd /opt/mempalace && tar xzf /tmp/testbed-mempalace-export-*.tar.gz"
   ```

4. Reindex
   ```bash
   ssh pieter@100.77.0.47 "cd /opt/mempalace && ~/.local/bin/mempalace reindex"
   ```

5. Verify migration
   - Use `mempalace__mempalace_search` tool with known query from testbed memory
   - Compare result count before/after

---

### Task 7: Test end-to-end functionality
**Status:** Pending

**Test cases:**
1. Search: `mempalace__mempalace_search` with query "mempalace validation"
2. Status: `mempalace__mempalace_status` shows correct drawer count
3. Add drawer: `mempalace__mempalace_add_drawer` with test content
4. Retrieve: Search for newly added content

**Success criteria:** All operations work via network MCP.

---

### Task 8: Document completion
**Status:** Pending

**Deliverables:**
1. Update HANDOFF.md with completion status
2. Write completion report in memory/2026-06-22.md
3. Update MEMORY.md with:
   - MemPalace now on honcho-m1
   - Testbed configured for network access
   - Migration validated
4. Upload completion report to Dropbox

---

## Rollback Plan

**If any step fails:**

1. Stop and assess
2. Restore JSON backup:
   ```bash
   cp ~/.openclaw/openclaw.json.backup-mempalace-network-* ~/.openclaw/openclaw.json
   oc-restart
   ```
3. Document failure in daily note
4. Alert Pieter

**Data safety:** Testbed local palace remains untouched until migration validated.

---

## Timeline Estimate

| Task | Duration | Total |
|---|---|---|
| SSH key verification | 5 min | 0:05 |
| Backup JSON | 2 min | 0:07 |
| Update openclaw.json | 10 min | 0:17 |
| Restart gateway | 3 min | 0:20 |
| Verify tools | 5 min | 0:25 |
| Migrate data | 15 min | 0:40 |
| Test end-to-end | 15 min | 0:55 |
| Document | 15 min | 1:10 |

**Total: ~1.5 hours** (with buffer for troubleshooting)

---

## Success Criteria

✅ Testbed MCP config points to honcho-m1
✅ `mempalace__*` tools available in session
✅ All testbed memory migrated (no data loss)
✅ Search results match pre-migration
✅ Add/search operations work end-to-end
✅ Documentation complete

---

## Next Actions

1. Execute Task 1 (verify SSH)
2. Execute Task 2-8 in sequence
3. Report completion to Pieter

**Start time:** 2026-06-22 13:51 CDT
**Target completion:** 2026-06-22 15:30 CDT
