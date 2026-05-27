# Bob Deployment Steps - Daily Start/End Implementation

**Date:** 2026-05-26  
**Target:** bobwebdev-m1 (100.126.243.57)  
**Deployer:** Testbed (via SSH) or Bob (self-deploy)

---

## Pre-Deployment Checklist

- [x] Testbed implementation complete and tested
- [x] Hetzner snapshot: `%AgentServer%POSTSlackInjectionChanges-05-26-2026`
- [x] Files in Dropbox: `(Admin)/Daily Sync/`
- [x] Bob has access to Dropbox (pending confirmation)

---

## Deployment Steps

### Step 1: Backup Bob's Workspace (5 min)

```bash
# SSH to Bob
ssh pieter@100.126.243.57

# Create granular backup
cd ~/.openclaw/workspace
TIMESTAMP=$(date +%Y-%m-%d_%H-%M)
BACKUP_DIR="Backups-Granular/bob-${TIMESTAMP}"
mkdir -p "$BACKUP_DIR"

for file in SOUL.md AGENTS.md MEMORY.md USER.md TOOLS.md HEARTBEAT.md IDENTITY.md HANDOFF.md BOOTSTRAP.md; do
  [ -f "$file" ] && cp "$file" "$BACKUP_DIR/"
done

# Commit backup (no openclaw.json - contains secrets)
git add Backups-Granular/
git commit -m "Pre-deployment backup: Daily Start/End implementation ${TIMESTAMP}"
git push
```

---

### Step 2: Install Dependencies (2 min)

```bash
# Check if PyYAML installed
python3 -c "import yaml" 2>/dev/null && echo "✅ PyYAML installed" || sudo apt install -y python3-yaml
```

---

### Step 3: Copy Scripts from Dropbox (10 min)

**Option A: Via MCP (if Bob has access)**
```bash
# Use Dropbox MCP to fetch files
# (Bob should know SOP-04 process)
```

**Option B: Via Testbed (SSH file transfer)**
```bash
# On Testbed:
scp ~/scripts/daily-checks.py pieter@100.126.243.57:~/scripts/
scp ~/scripts/daily-backup.py pieter@100.126.243.57:~/scripts/
scp ~/.openclaw/daily-checks.yaml pieter@100.126.243.57:~/.openclaw/

# On Bob: Make executable
chmod +x ~/scripts/daily-*.py
```

**Option C: Manual download from Dropbox web UI**
- Download 3 files from `(Admin)/Daily Sync/`
- Place in correct locations

---

### Step 4: Customize Bob's Config (5 min)

```bash
# Edit Bob's daily-checks.yaml
nano ~/.openclaw/daily-checks.yaml

# Change:
# 1. agent.name: testbed → bob
# 2. Personality test expect_contains: ['testbed'] → ['bob', 'builder', 'production']
# 3. Add Bob-specific checks (e.g., Paperclip health)
```

**Bob's custom checks:**
```yaml
# After standard checks, add:
- name: Paperclip Health
  type: http
  url: http://paperclip-url/health
  expect: ok
  required: false
  timeout: 10
```

---

### Step 5: Test Scripts Manually (5 min)

```bash
# Test daily checks
python3 ~/scripts/daily-checks.py

# Should see:
# === Daily Start Checks: bob ===
# ...
# ✅ All required checks passed

# Test backup script
python3 ~/scripts/daily-backup.py

# Should see:
# === Daily End-of-Day Backup: bob ===
# ...
# ✅ All backup operations completed successfully
```

---

### Step 6: Add to BOOTSTRAP.md (2 min)

```bash
cd ~/.openclaw/workspace

cat >> BOOTSTRAP.md << 'EOF'

## Daily Start Checks (Automatic)

```bash
# Run daily checks once per day at session start
TIMESTAMP_FILE=~/.openclaw/workspace/.daily-start-timestamp
TODAY=$(date +%Y-%m-%d)

if [ ! -f "$TIMESTAMP_FILE" ] || [ "$(cat $TIMESTAMP_FILE)" != "$TODAY" ]; then
  echo "Running daily start checks..."
  if python3 ~/scripts/daily-checks.py; then
    echo "$TODAY" > "$TIMESTAMP_FILE"
    echo "✅ Daily start checks passed"
  else
    echo "❌ Daily start checks FAILED - review logs before proceeding"
  fi
fi
```
EOF
```

---

### Step 7: Install Systemd Timer (5 min)

```bash
# Create systemd user directory
mkdir -p ~/.config/systemd/user

# Create timer
cat > ~/.config/systemd/user/daily-backup.timer << 'EOF'
[Unit]
Description=Daily Backup and Sync
Documentation=https://github.com/Ascendancy-Group/BobAccentWebDev

[Timer]
OnCalendar=18:00
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Create service
cat > ~/.config/systemd/user/daily-backup.service << 'EOF'
[Unit]
Description=Daily Backup and Sync

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/pieter/scripts/daily-backup.py
WorkingDirectory=/home/pieter/.openclaw/workspace
StandardOutput=append:/home/pieter/.openclaw/workspace/memory/daily-backup.log
StandardError=append:/home/pieter/.openclaw/workspace/memory/daily-backup.log
EOF

# Enable and start
systemctl --user daemon-reload
systemctl --user enable daily-backup.timer
systemctl --user start daily-backup.timer

# Verify
systemctl --user list-timers | grep daily-backup
```

---

### Step 8: Final Commit (2 min)

```bash
cd ~/.openclaw/workspace

git add -A
git commit -m "Daily Start/End implementation complete - Python/YAML

- daily-checks.py: Bob-specific checks
- daily-backup.py: 4 backup operations
- daily-checks.yaml: Bob config
- BOOTSTRAP.md: auto-run at session start
- systemd timer: active (next run 2026-05-27 18:00)

Issue #37"

git push
```

---

## Verification

**Check 1: Scripts exist**
```bash
ls -lh ~/scripts/daily-*.py
ls -lh ~/.openclaw/daily-checks.yaml
```

**Check 2: Manual test passed**
```bash
python3 ~/scripts/daily-checks.py
# Exit code should be 0
echo $?
```

**Check 3: Systemd timer active**
```bash
systemctl --user list-timers | grep daily-backup
# Should show next run time: Wed 2026-05-27 18:00:00
```

**Check 4: BOOTSTRAP.md updated**
```bash
tail -20 ~/.openclaw/workspace/BOOTSTRAP.md
# Should show Daily Start Checks section
```

---

## Rollback (if needed)

```bash
# Restore from Hetzner snapshot:
# %AgentServer%POSTSlackInjectionChanges-05-26-2026

# Or restore from granular backup:
cd ~/.openclaw/workspace
BACKUP_DIR="Backups-Granular/bob-2026-05-26_XX-XX"
for file in SOUL.md AGENTS.md MEMORY.md USER.md TOOLS.md HEARTBEAT.md IDENTITY.md HANDOFF.md BOOTSTRAP.md; do
  [ -f "$BACKUP_DIR/$file" ] && cp "$BACKUP_DIR/$file" .
done
```

---

## Expected Tomorrow (2026-05-27)

**Morning (session start):**
- BOOTSTRAP.md runs `daily-checks.py` automatically
- Bob's personality test checks for "bob", "builder", "production"
- Creates timestamp to prevent duplicate runs

**Evening (18:00 CDT):**
- Systemd timer triggers `daily-backup.py`
- 4 backup operations run
- Logs to `~/.openclaw/workspace/memory/daily-backup.log`

---

## Success Criteria

- [ ] All scripts copied and executable
- [ ] daily-checks.yaml customized for Bob
- [ ] Manual test of daily-checks.py: PASS
- [ ] Manual test of daily-backup.py: PASS
- [ ] BOOTSTRAP.md updated
- [ ] Systemd timer active
- [ ] All changes committed to GitHub
- [ ] No errors in logs

---

**Total time estimate:** 30-40 minutes

**Deployment method:** Option B (SSH from Testbed) recommended if Bob's Dropbox access still blocked
