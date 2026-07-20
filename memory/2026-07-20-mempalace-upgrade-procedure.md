# MemPalace Upgrade: v3.3.0 → v3.6.0

**Date:** 2026-07-20  
**Server:** honcho-m1 (100.77.0.47)  
**Snapshot:** ✅ `Honch01-M1-Pre-MemPalace & Honcho upgrade-07-20-2026`

---

## Pre-Upgrade Status

**Current Version:** v3.3.0  
**Target Version:** v3.6.0  
**Version Gap:** 3 minor versions (3.3.0 → 3.4.1 → 3.5.0 → 3.6.0)

**Fork Status:** ✅ Created at https://github.com/Ascendancy-Group/mempalace

**Current Data:**
- Location: `/opt/mempalace/`
- chroma.sqlite3: 226 MB
- knowledge_graph.sqlite3: 36 KB
- Total drawers: 16,225

---

## Upgrade Procedure

### Phase 1: Backup Current Data

```bash
ssh pieter@100.77.0.47

# Create timestamped backup
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
sudo mkdir -p /opt/mempalace-backups
sudo cp -r /opt/mempalace /opt/mempalace-backups/mempalace-backup-$TIMESTAMP

# Verify backup
ls -lh /opt/mempalace-backups/
du -sh /opt/mempalace-backups/mempalace-backup-$TIMESTAMP
```

### Phase 2: Stop Services Using MemPalace

```bash
# Check what's using MemPalace
ps aux | grep mempalace

# Stop OpenClaw on all agents using SSH MCP
# (They'll reconnect after upgrade)
```

### Phase 3: Upgrade MemPalace Package

```bash
# Upgrade from our fork
pip install --upgrade git+https://github.com/Ascendancy-Group/mempalace.git@v3.6.0

# Verify upgrade
pip show mempalace | grep Version
# Expected: Version: 3.6.0
```

### Phase 4: Test MemPalace Access

```bash
# Test import
python3 -c "import mempalace; print(f'MemPalace version: {mempalace.__version__}')"

# Test MCP server startup (don't leave running)
cd /opt/mempalace
python3 -m mempalace.mcp_server &
MCP_PID=$!
sleep 5
kill $MCP_PID
```

### Phase 5: Verify Data Integrity

```bash
# Check SQLite databases
sqlite3 /opt/mempalace/chroma.sqlite3 "PRAGMA integrity_check;"
# Expected: ok

sqlite3 /opt/mempalace/knowledge_graph.sqlite3 "PRAGMA integrity_check;"
# Expected: ok

# Check file sizes (should be unchanged)
ls -lh /opt/mempalace/*.sqlite3
```

### Phase 6: Test from Testbed

```bash
# On testbed-m1
# Test MemPalace tools
mempalace__mempalace_status
# Expected: 16,225+ drawers, palace_path: /opt/mempalace

mempalace__mempalace_search(query="test upgrade", limit=3)
# Expected: Returns results

mempalace__mempalace_kg_stats
# Expected: Current stats
```

### Phase 7: Post-Upgrade Snapshot

**Via Hetzner Console:**
- Name: `post-mempalace-upgrade-2026-07-20-HHMM`
- Validate creation

---

## Rollback Procedure

**If upgrade fails:**

```bash
# 1. Stop any running MemPalace processes
pkill -f mempalace

# 2. Uninstall new version
pip uninstall -y mempalace

# 3. Reinstall old version
pip install mempalace==3.3.0

# 4. Restore data backup (if corrupted)
sudo rm -rf /opt/mempalace
sudo cp -r /opt/mempalace-backups/mempalace-backup-TIMESTAMP /opt/mempalace
sudo chown -R pieter:pieter /opt/mempalace

# 5. Test
python3 -c "import mempalace; print(mempalace.__version__)"
# Expected: 3.3.0

# 6. Restore from Hetzner snapshot if needed
# (Via Hetzner console - Pieter)
```

---

## Success Criteria

- ✅ `pip show mempalace` reports v3.6.0
- ✅ SQLite integrity checks pass
- ✅ `mempalace__mempalace_status` returns 16,225+ drawers
- ✅ Search queries return results
- ✅ No errors in agent logs
- ✅ Post-upgrade snapshot created

---

## Key Changes in v3.6.0

**From v3.3.0 → v3.4.1:**
- Improved ChromaDB index recovery
- Better write contention handling

**From v3.4.1 → v3.5.0:**
- HTTP serving support
- Performance optimizations for large DBs

**From v3.5.0 → v3.6.0:**
- Atomic fact replacement
- Improved conversation chronology
- Stability improvements

**See:** https://github.com/MemPalace/mempalace/releases

---

## Estimated Timeline

| Phase | Duration |
|-------|----------|
| Backup current data | 2 min |
| Stop services | 1 min |
| Upgrade package | 3 min |
| Test access | 2 min |
| Verify integrity | 2 min |
| Test from testbed | 5 min |
| Post-upgrade snapshot | 3 min |
| **Total** | **18 min** |

---

## Status: Ready to Execute

**Blocker:** None  
**Snapshot:** ✅ Confirmed  
**Fork:** ✅ Created  
**Procedure:** ✅ Documented

**Awaiting:** Go-ahead from Pieter

---

*Prepared by: Testbed*  
*Date: 2026-07-20 13:45 CDT*
