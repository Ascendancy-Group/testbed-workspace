# MEMORY.md — Testbed Core Memory

*Last updated: 2026-05-26*

---

## Identity
- **Name:** Testbed | **Machine:** testbed-m1 | **Role:** Infrastructure tester
- **Tailscale IP:** 100.94.9.125
- **Workspace repo:** Ascendancy-Group/testbed-workspace

---

## Purpose
Test infrastructure changes before they touch production. Document everything. Script repeatability. Hand proven approaches to Bob for production deployment.

---

## Test Queue (Top 5 Priority)
1. **Agent Slack Memory Config** — Context injection control (QW-02 in progress)
2. MemPalace — full end-to-end proof (plan in Dropbox)
3. Honcho — memory persistence + injection validation
4. OpenClaw upgrades — version validation before prod rollout
5. Gateway config changes — validate JSON changes before prod

*Full queue in daily notes.*

---

## Infrastructure

| Item | Detail |
|---|---|
| Machine | testbed-m1, Hetzner VPS |
| Tailscale IP | 100.94.9.125 |
| OS | Ubuntu 24.04 |
| Honcho server | http://100.77.0.47:8000 |
| Dropbox MCP | http://100.77.0.47:3001 (SOP-03) |
| Workspace repo | Ascendancy-Group/testbed-workspace |

---

## Standing Decisions
- No Chinese-origin models. Ever.
- All scheduled jobs use systemd timers — no crontab
- Gateway restart: `oc-restart` only
- Production Law: nothing to prod without passing testbed first
- Dropbox: MCP server on honcho-m1 only (SOP-03)
- `trash` > `rm`

---

## 🚨 Hard Rules (Non-Negotiable)

**Two-Tier Backup Protocol:**
1. Pieter makes Hetzner snapshot
2. Agent makes JSON backup: `openclaw.json.backup-[description]-$(date +%Y%m%d-%H%M%S)`

**Both required. Every time. No shortcuts. No exceptions.**

Applies to: openclaw.json edits, scope changes, channel configs, identity changes, token rotations, major updates.

---

## Key Findings (Recent)

**Slack Channel Monitoring (2026-05-14):**
- 2026.5.7/5.12 schema bug rejects documented `groupAllowFrom`
- Working: `groupPolicy: "open"` + per-channel config
- After 2026.5.12: must install `@openclaw/slack` plugin separately
- Full report: `memory/2026-05-14-slack-channel-troubleshooting.md`

**OpenClaw Schema Validation (2026-05-26 PRE-01):**
- Schema strictly validates openclaw.json keys
- Arbitrary keys rejected (safety feature)
- Config keys must exist in schema before use
- Rollback procedure validated and proven

---

## Latest Hetzner Snapshot
**Pre-Implementation:** `testbed-m1-PreInjectionChanges-05-26-2026` (2026-05-26)
- Baseline before Agent Slack Memory Config implementation
- Rollback point for QW-02, QW-03, SQL-01 tickets

---

*Detailed context, proven approaches, and full test logs: `memory/YYYY-MM-DD.md` and archived reports.*
*Use `memory_search` tool to retrieve historical context.*
