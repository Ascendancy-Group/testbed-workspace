# MemPalace v3.6.0 Upgrade Plan — 2026-07-20

## Executive Summary

**Target:** Upgrade honcho-m1 MemPalace from v3.3.6 → v3.6.0  
**Scheduled:** 2026-07-20 (pending Pieter approval)  
**Executor:** Testbed  
**Approval channel:** #testing-env--public (Slack)  
**Estimated duration:** 60-90 minutes (including backups)  
**Risk level:** Medium (3 major versions, active production palace)

---

## Pre-Upgrade Requirements

### ✅ Approval Gate
- [ ] **Pieter approval required** via #testing-env--public before execution
- [ ] Confirm backup window acceptable
- [ ] Confirm agents can tolerate 30-60 min MemPalace unavailability

### ✅ Backup Verification
- [ ] Hetzner snapshot: honcho-m1 (pre-upgrade baseline)
- [ ] Off-server backup: `/opt/mempalace/` → Dropbox
- [ ] Backup integrity verification (file count, size)
- [ ] Restore procedure documented and tested

---

## Backup Strategy

### Three-Tier Approach

#### Tier 1: Hetzner Snapshot (Infrastructure)
- **What:** Full VM snapshot
- **Where:** Hetzner Cloud (native)
- **Retention:** 7 days
- **Recovery time:** 15-30 minutes (full VM restore)
- **Use case:** Complete system failure, rollback entire machine

#### Tier 2: Local Backup (On honcho-m1)
- **What:** `/opt/mempalace/` directory copy
- **Where:** `/opt/mempalace-backups/pre-upgrade-v3.3.6-YYYY-MM-DD/`
- **Retention:** 30 days (manual cleanup)
- **Recovery time:** 2-5 minutes (directory swap)
- **Use case:** Quick rollback, palace corruption

#### Tier 3: Off-Server Backup (Disaster Recovery)
- **What:** `/opt/mempalace/` tarball
- **Where:** Dropbox `/Backups/MemPalace/YYYY-MM-DD/`
- **Retention:** 90 days
- **Recovery time:** 10-20 minutes (download + extract)
- **Use case:** Hetzner failure, data center loss, catastrophic failure

---

## Backup Execution Plan

### Step 1: Hetzner Snapshot
```bash
# Via Testbed on testbed-m1
curl -X POST \
  -H "Authorization: Bearer $(op item get 'Hetzner API Token' --vault AgentStack --fields label=token --reveal)" \
  -H "Content-Type: application/json" \
  -d '{"description":"Pre-MemPalace-v3.6.0-Upgrade-2026-07-20","type":"snapshot"}' \
  https://api.hetzner.cloud/v1/servers/$(hcloud server describe honcho-m1 -o json | jq -r .id)/actions/create_image
```

**Verification:**
```bash
hcloud image list | grep honcho-m1 | grep $(date +%Y-%m-%d)
```

---

### Step 2: Local Backup (On honcho-m1)
```bash
# SSH to honcho-m1
ssh pieter@100.77.0.47

# Create backup directory
BACKUP_DATE=$(date +%Y-%m-%d-%H%M)
BACKUP_DIR="/opt/mempalace-backups/pre-upgrade-v3.3.6-${BACKUP_DATE}"
sudo mkdir -p "$BACKUP_DIR"

# Stop MCP server (if running as systemd service)
sudo systemctl stop mempalace-mcp 2>/dev/null || true

# Copy palace directory
sudo cp -a /opt/mempalace/. "$BACKUP_DIR/"

# Verify backup
echo "Backup size: $(du -sh $BACKUP_DIR | cut -f1)"
echo "File count: $(find $BACKUP_DIR -type f | wc -l)"
ls -lh "$BACKUP_DIR"

# Record backup metadata
cat > "$BACKUP_DIR/BACKUP-METADATA.txt" <<EOF
Backup Date: $(date -u +%Y-%m-%d\ %H:%M\ UTC)
Source: /opt/mempalace/
MemPalace Version: v3.3.6
Palace Size: $(du -sh /opt/mempalace/chroma.sqlite3 | cut -f1)
Backed up by: Testbed
Reason: Pre-v3.6.0 upgrade safety backup
EOF

# Create restore script
cat > "$BACKUP_DIR/RESTORE.sh" <<'RESTORE_SCRIPT'
#!/bin/bash
# MemPalace v3.3.6 Restore Script
set -e

echo "⚠️  WARNING: This will overwrite /opt/mempalace/ with v3.3.6 backup"
read -p "Continue? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
  echo "Aborted."
  exit 1
fi

# Stop MCP server
sudo systemctl stop mempalace-mcp 2>/dev/null || true

# Backup current (possibly broken) state
FAILED_DIR="/opt/mempalace-failed-$(date +%Y-%m-%d-%H%M)"
sudo mv /opt/mempalace "$FAILED_DIR"
echo "Failed state moved to: $FAILED_DIR"

# Restore from backup
sudo cp -a . /opt/mempalace/
sudo rm /opt/mempalace/BACKUP-METADATA.txt
sudo rm /opt/mempalace/RESTORE.sh

# Verify
echo "Restored palace size: $(du -sh /opt/mempalace/chroma.sqlite3 | cut -f1)"

# Restart MCP server
sudo systemctl start mempalace-mcp 2>/dev/null || echo "Start MCP manually"

echo "✅ Restore complete. Verify functionality before deleting $FAILED_DIR"
RESTORE_SCRIPT

chmod +x "$BACKUP_DIR/RESTORE.sh"
```

**Verification:**
```bash
# Compare file counts
echo "Original: $(find /opt/mempalace -type f | wc -l)"
echo "Backup:   $(find $BACKUP_DIR -type f | wc -l)"

# Compare sizes
du -sh /opt/mempalace
du -sh $BACKUP_DIR
```

---

### Step 3: Off-Server Backup (Dropbox)
```bash
# Create tarball (on honcho-m1)
cd /opt
TARBALL="mempalace-v3.3.6-$(date +%Y-%m-%d-%H%M).tar.gz"
sudo tar czf "/tmp/$TARBALL" mempalace/

# Calculate checksum
sha256sum "/tmp/$TARBALL" > "/tmp/$TARBALL.sha256"

# Get file size
ls -lh "/tmp/$TARBALL"
```

```bash
# Upload to Dropbox (from testbed-m1 using Dropbox MCP)
# Transfer tarball to testbed first, then upload
```

**Dropbox path:** `/Backups/MemPalace/2026-07-20/mempalace-v3.3.6-YYYY-MM-DD-HHMM.tar.gz`

**Verification:**
```bash
# Verify Dropbox upload
# Check file exists and size matches
# Download checksum and verify
```

---

## Upgrade Execution Plan

### Phase 1: Pre-Flight Checks (5 min)

```bash
# On honcho-m1
ssh pieter@100.77.0.47

# 1. Verify current version
python3 -m mempalace --version
# Expected: 3.3.6

# 2. Check palace health
cd /opt/mempalace
python3 -m mempalace status
# Expected: No critical errors

# 3. Check disk space (need ~500 MB free for upgrade)
df -h /opt
# Expected: >1 GB free

# 4. Verify all backups complete
ls -lh /opt/mempalace-backups/pre-upgrade-v3.3.6-*/
# Expected: Backup directory exists, ~240 MB

# 5. Check MCP server status
systemctl --user status openclaw-gateway.service
# Expected: Active on connected agents
```

---

### Phase 2: Sync Bob's Fork (10 min)

```bash
# On testbed-m1 (using Bob's PAT)
cd ~
git clone https://github.com/BobAccentWebDev/mempalace.git mempalace-fork-sync
cd mempalace-fork-sync

# Add upstream
git remote add upstream https://github.com/MemPalace/mempalace.git
git fetch upstream

# Check divergence
git log --oneline HEAD..upstream/develop | wc -l
# Expected: 1163 commits

# Sync develop branch
git checkout develop
git merge upstream/develop

# Resolve conflicts (if any)
# ... manual resolution ...

# Push to Bob's fork
GH_TOKEN=$(op item get "Bob (BobAccentWebDev) — GitHub PAT — Full Ascendancy-Group Org Access" --vault AgentStack --fields label=token --reveal)
git push origin develop
```

**Approval gate:** If conflicts exist, document and request Pieter review before proceeding.

---

### Phase 3: Upgrade Execution (20 min)

```bash
# On honcho-m1
ssh pieter@100.77.0.47
cd /opt/mempalace

# 1. Stop MCP server
# (If running as systemd service)
sudo systemctl stop mempalace-mcp 2>/dev/null || echo "No systemd service"

# 2. Upgrade via pip
sudo -u pieter python3 -m pip install --upgrade mempalace

# OR: Install from Bob's synced fork
sudo -u pieter python3 -m pip install --upgrade git+https://github.com/BobAccentWebDev/mempalace.git@develop

# 3. Verify new version
python3 -m mempalace --version
# Expected: 3.6.0

# 4. Check for schema migrations
python3 -m mempalace status --palace /opt/mempalace
# Expected: May trigger HNSW rebuild, SQLite integrity checks

# 5. Run repair if prompted
python3 -m mempalace repair --mode from-sqlite --palace /opt/mempalace
# (Only if status indicates divergence)
```

---

### Phase 4: Post-Upgrade Verification (15 min)

```bash
# On honcho-m1

# 1. Palace status
python3 -m mempalace status --palace /opt/mempalace
# Expected: No critical errors, all checks pass

# 2. Test search
python3 -m mempalace search "test query" --palace /opt/mempalace
# Expected: Results returned

# 3. Test MCP tools (via OpenClaw)
# From testbed-m1
```

**OpenClaw tool verification:**
```bash
# Test critical tools
# - mempalace_status
# - mempalace_search
# - mempalace_add_drawer
# - mempalace_list_wings
# - mempalace_kg_query
```

**Expected:** All 28 tools responsive, schema updated in OpenClaw.

---

### Phase 5: Restart Services (5 min)

```bash
# On honcho-m1
# If MCP server is systemd service
sudo systemctl start mempalace-mcp
sudo systemctl status mempalace-mcp

# On agent machines (Bob, Mason, Forge, Testbed)
# Restart OpenClaw gateway to refresh MCP schema
systemctl --user restart openclaw-gateway.service
```

---

## Rollback Procedure

### Scenario 1: Upgrade Fails During Installation

```bash
# On honcho-m1
cd /opt/mempalace-backups/pre-upgrade-v3.3.6-*/
sudo ./RESTORE.sh

# Downgrade pip package
sudo -u pieter python3 -m pip install mempalace==3.3.6
```

**Recovery time:** 5 minutes

---

### Scenario 2: Post-Upgrade Palace Corruption

```bash
# On honcho-m1
cd /opt/mempalace-backups/pre-upgrade-v3.3.6-*/
sudo ./RESTORE.sh

# Verify restore
python3 -m mempalace status --palace /opt/mempalace

# Downgrade
sudo -u pieter python3 -m pip install mempalace==3.3.6
```

**Recovery time:** 5-10 minutes

---

### Scenario 3: Complete System Failure

```bash
# Via Hetzner Cloud Console or API
# 1. Restore from snapshot
hcloud server rebuild honcho-m1 --image <snapshot-id>

# 2. Wait for VM boot (5-10 min)

# 3. Verify services
ssh pieter@100.77.0.47 "systemctl --user status openclaw-gateway"
```

**Recovery time:** 15-30 minutes

---

### Scenario 4: Hetzner Data Center Failure

```bash
# On testbed-m1 (or any machine with Dropbox access)

# 1. Provision new VM (honcho-m1-recovery)
hcloud server create --name honcho-m1-recovery --type cpx31 --image ubuntu-24.04 --location ash

# 2. Download backup from Dropbox
# (Use Dropbox MCP tools)

# 3. Extract to /opt/mempalace
ssh pieter@<new-ip> "sudo mkdir -p /opt/mempalace"
scp mempalace-backup.tar.gz pieter@<new-ip>:/tmp/
ssh pieter@<new-ip> "cd /opt && sudo tar xzf /tmp/mempalace-backup.tar.gz"

# 4. Install MemPalace v3.3.6
ssh pieter@<new-ip> "python3 -m pip install mempalace==3.3.6"

# 5. Verify
ssh pieter@<new-ip> "python3 -m mempalace status --palace /opt/mempalace"

# 6. Update Tailscale IP in agent configs
```

**Recovery time:** 30-60 minutes

---

## Backup Scheduling

### Automated Daily Backups

**Approach:** systemd timer on honcho-m1

```bash
# On honcho-m1
sudo cat > /etc/systemd/system/mempalace-backup.service <<'EOF'
[Unit]
Description=MemPalace Daily Backup
After=network-online.target

[Service]
Type=oneshot
User=pieter
WorkingDirectory=/opt
ExecStart=/usr/local/bin/mempalace-backup.sh
StandardOutput=journal
StandardError=journal
EOF

sudo cat > /etc/systemd/system/mempalace-backup.timer <<'EOF'
[Unit]
Description=MemPalace Daily Backup Timer

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo cat > /usr/local/bin/mempalace-backup.sh <<'BACKUP_SCRIPT'
#!/bin/bash
# MemPalace Daily Backup Script
set -e

BACKUP_DATE=$(date +%Y-%m-%d)
BACKUP_ROOT="/opt/mempalace-backups"
BACKUP_DIR="$BACKUP_ROOT/daily-$BACKUP_DATE"
RETENTION_DAYS=30

# Create backup
mkdir -p "$BACKUP_DIR"
cp -a /opt/mempalace/. "$BACKUP_DIR/"

# Record metadata
cat > "$BACKUP_DIR/BACKUP-METADATA.txt" <<METADATA
Backup Date: $(date -u +%Y-%m-%d %H:%M UTC)
Backup Type: Automated Daily
Source: /opt/mempalace/
Palace Size: $(du -sh /opt/mempalace/chroma.sqlite3 | cut -f1)
File Count: $(find /opt/mempalace -type f | wc -l)
METADATA

# Cleanup old backups (>30 days)
find "$BACKUP_ROOT" -maxdepth 1 -type d -name "daily-*" -mtime +$RETENTION_DAYS -exec rm -rf {} \;

# Log completion
echo "Backup complete: $BACKUP_DIR ($(du -sh $BACKUP_DIR | cut -f1))"

# Optional: Upload to Dropbox weekly (Sundays)
if [ "$(date +%u)" = "7" ]; then
  echo "Weekly off-server backup triggered"
  # TODO: Implement Dropbox upload via API or rclone
fi
BACKUP_SCRIPT

sudo chmod +x /usr/local/bin/mempalace-backup.sh

# Enable timer
sudo systemctl daemon-reload
sudo systemctl enable mempalace-backup.timer
sudo systemctl start mempalace-backup.timer

# Verify
sudo systemctl status mempalace-backup.timer
```

**Schedule:**
- **Daily local backup:** 02:00 UTC (21:00 CDT)
- **Weekly Dropbox backup:** Sunday 02:00 UTC
- **Retention:** 30 days local, 90 days Dropbox

---

## Documentation

### Backup & Restore SOP

**Location:** `ascendancy-infra` repo  
**Path:** `docs/runbooks/mempalace-backup-restore.md`

**Contents:**
1. Backup strategy overview
2. Manual backup procedure
3. Automated backup setup
4. Restore procedures (all scenarios)
5. Verification checklists
6. Disaster recovery contacts

---

## Approval Checklist

Before executing upgrade, confirm:

- [ ] **Pieter approval** received in #testing-env--public
- [ ] Hetzner snapshot created and verified
- [ ] Local backup created and verified
- [ ] Dropbox backup uploaded and verified
- [ ] Restore script tested (on testbed copy)
- [ ] Backup schedule documented
- [ ] Rollback procedures documented
- [ ] Agent downtime window acceptable
- [ ] All backup tiers operational

---

## Timeline

**Total estimated time:** 60-90 minutes

| Phase | Duration | Description |
|-------|----------|-------------|
| Backups (Tier 1-3) | 20-30 min | Hetzner snapshot + local + Dropbox |
| Fork sync | 10 min | Merge upstream develop into Bob's fork |
| Upgrade execution | 20 min | pip install, schema migrations |
| Verification | 15 min | Test tools, palace health |
| Service restart | 5 min | Restart MCP + agent gateways |
| Buffer | 10 min | Unexpected issues |

**Downtime:** 30-60 minutes (MemPalace unavailable)

---

## Success Criteria

- [ ] MemPalace version: 3.6.0
- [ ] `mempalace status`: No critical errors
- [ ] All 28 MCP tools functional in OpenClaw
- [ ] Search returns results
- [ ] Knowledge graph queries working
- [ ] No data loss (drawer count unchanged)
- [ ] All backups verified
- [ ] Restore procedure documented

---

## Escalation

**If upgrade fails:**
1. Execute rollback procedure
2. Document failure in daily note
3. Alert Pieter in #testing-env--public
4. Request guidance before retry

---

*Plan created: 2026-07-20 03:00 UTC*  
*Executor: Testbed*  
*Approval required: Pieter van der Wal*
