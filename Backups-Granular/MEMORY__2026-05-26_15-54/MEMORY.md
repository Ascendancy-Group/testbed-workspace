# MEMORY.md — Testbed Core Memory

*Last updated: 2026-05-12*

---

## Identity

- **Name:** Testbed | **Machine:** testbed-m1 | **Role:** Infrastructure tester
- **Tailscale IP:** 100.94.9.125
- **Workspace repo:** Ascendancy-Group/testbed-workspace (public — proven scripts available to all agents)

---

## Purpose

Test infrastructure changes before they touch production. Document everything. Script repeatability. Hand proven approaches to Bob for production deployment.

---

## Test Queue (Priority Order)

1. MemPalace — full end-to-end proof (plan in Dropbox)
2. Honcho — memory persistence + injection validation
3. Claude Memory (claude-mem) — memory persistence validation
4. Lossless memory — approach validation
5. Paperclip — full end-to-end proof before prod
6. OpenClaw upgrades — version validation before prod rollout
7. Gateway config changes — validate JSON changes before prod
8. New agent onboarding checklist — validate bootstrap process
9. Systemd timer installs — verify survival across restarts

---

## Proven Approaches

### Slack Channel Monitoring (2026-05-14)
**Problem:** Channel messages not reaching OpenClaw (DMs work, channels don't).

**Root causes:**
1. 2026.5.7/2026.5.12 schema bug: rejects documented `groupAllowFrom` config
2. Missing Slack plugin in 2026.5.12 (must install separately)
3. `groupPolicy: "allowlist"` + empty `groupAllowFrom` = all messages dropped

**Working solution:**
```json
{
  "channels": {
    "slack": {
      "groupPolicy": "open",
      "channels": {
        "<CHANNEL_ID>": {"enabled": true, "requireMention": false}
      }
    }
  }
}
```

**After 2026.5.12 upgrade:**
```bash
openclaw plugins install @openclaw/slack  # without sudo
openclaw gateway restart
```

**Full report:** `memory/2026-05-14-slack-channel-troubleshooting.md`

---

## Known Failures

### OpenClaw 2026.5.7 and 2026.5.12 Schema Bug
**What:** Documented Slack `groupAllowFrom` config rejected by schema validator.

**Error:**
```
channels.slack: invalid config: must NOT have additional properties
```

**What fails:**
```json
{
  "channels": {
    "slack": {
      "groupPolicy": "allowlist",
      "groupAllowFrom": ["U0ANQ79KGAV"],  // <-- rejected
      "channels": {...}
    }
  }
}
```

**Documented but unsupported** in 2026.5.7 and 2026.5.12.

**Workaround:** Use `groupPolicy: "open"` (less secure but accepted).

**Avoid:** Running `openclaw doctor --fix` when manual Slack config is present — it strips the config instead of migrating it.

---

## Infrastructure

| Item | Detail |
|---|---|
| Machine | testbed-m1, Hetzner VPS |
| Tailscale IP | 100.94.9.125 |
| OS | Ubuntu 24.04 |
| Honcho server | http://100.77.0.47:8000 (honcho-m1) |
| Dropbox MCP | http://100.77.0.47:3001 (honcho-m1, SOP-03) |
| Workspace repo | Ascendancy-Group/testbed-workspace |

### Hetzner Snapshots

**Latest GOLD snapshot:** `Testbed-M1-GOLD-Slack&JSON-05-14-2026`
- Created: 2026-05-14 15:32 CDT
- Status: Known-good baseline with working Slack integration
- Rollback point for destructive tests

---

## Standing Decisions

- No Chinese-origin models. Ever.
- All scheduled jobs use systemd timers — no crontab
- Gateway restart: `oc-restart` only
- Production Law: nothing to prod without passing testbed first
- Dropbox: MCP server on honcho-m1 only (SOP-03)
- `trash` > `rm`

## 🚨 Hard Rules (Non-Negotiable)

**Two-Tier Backup Protocol (2026-05-14)**

Before ANY JSON or major config change:

1. **Pieter makes Hetzner snapshot** — infrastructure rollback point
2. **Agent makes full JSON backup** with format:
   ```bash
   cp ~/.openclaw/openclaw.json ~/.openclaw/openclaw.json.backup-[description]-$(date +%Y%m%d-%H%M%S)
   ```

**Both required. Every time. No shortcuts. No exceptions.**

This applies to:
- openclaw.json edits
- Scope changes
- New channel configurations
- Agent identity changes
- Token rotations
- Major system updates

---

*Full daily test logs in `memory/YYYY-MM-DD.md`.*
