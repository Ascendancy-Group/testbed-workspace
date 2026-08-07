# MAINTENANCE.md — Testbed

**Owner:** Testbed
**Last Updated:** 2026-08-07

---

## Rule 1 — Irrevocable

> **No changes on Fridays. Ever.**
> This includes maintenance, upgrades, config edits, restarts, and infrastructure work.
> No exceptions. No "quick fixes." No "it'll only take a minute."
> If it's Friday: document it, plan it, execute Monday.

---

## What Testbed Owns

All infrastructure maintenance across the Ascendancy Group org:

| Machine | Purpose | Tailscale IP |
|---|---|---|
| testbed-m1 | Testbed agent | 100.94.9.125 |
| honcho-m1 | MemPalace + Honcho + Dropbox MCP | 100.77.0.47 |
| bobwebdev-m1 | Bob | 100.126.243.57 |
| mason-m1 | Mason | 100.117.192.71 |
| forge-m1 | Forge | 100.95.36.105 |
| vera-m1 | Vera | TBD |
| paperclip-ash-m1 | Paperclip | 5.161.250.132 |

---

## Maintenance Schedule

### Monthly — first weekend (not Friday)

- Ubuntu security patches (`apt upgrade`) — testbed first, then prod
- Tailscale — update all machines
- 1Password CLI — update all machines
- GitHub PAT audit — check expiry dates in 1PW AgentStack vault
- Hetzner snapshot audit — at least one recent snapshot per active server

### Quarterly — first week of Jan, Apr, Jul, Oct

- OpenClaw — full testbed validation before any prod agent touches it
- Ubuntu kernel + full `apt upgrade`
- Node.js update
- Docker CE + Compose + containerd (honcho-m1)
- Python venvs (honcho, tessera worker, scripts)
- Redis
- SSL/TLS cert expiry check

### On Release — Patch (within 2 weeks)

- Honcho — rebuild image, redeploy
- MemPalace — `pip install --upgrade`
- Paperclip — `npx paperclipai@latest` version check

### On Release — Minor/Major (dedicated testbed session)

- OpenClaw — full regression before any prod agent
- Honcho minor — API compatibility check
- Docker major — validate compose stack

---

## Pre-Change Checklist (Every Time)

1. [ ] Is it Friday? → **STOP. Plan for Monday.**
2. [ ] Hetzner snapshot created and validated `available`?
3. [ ] Backup of config file made?
4. [ ] Rollback plan documented?
5. [ ] Tested on testbed-m1 first (where applicable)?

---

## Active Action Queue

*Updated after every session. This is the live work list.*

| # | Item | Machine | Action | Risk | Target Date | Status |
|---|---|---|---|---|---|---|
| 1 | Paperclip OpenRouter adapter | ash-m1 | Install Kaoz625 adapter, retire hermes_local, wire Praetor to OR | LOW | 2026-08-11 Mon | 🔴 READY |
| 2 | Add testbed SSH key to ash-m1 | ash-m1 | `~/.ssh/authorized_keys` append | LOW | 2026-08-11 Mon | 🔴 READY |
| 3 | Paperclip systemd service | ash-m1 | Replace nohup with systemd user service | LOW | 2026-08-11 Mon | 🔴 READY |
| 4 | Paperclip version upgrade | ash-m1 | 2026.707.0 → 2026.722.0 | LOW | 2026-08-11 Mon | 🔴 READY |
| 5 | Agent GitHub forced sync | all agents | Design + implement systemd timer per agent | MED | 2026-08-11 Mon | 🔴 READY |
| 6 | OpenClaw upgrade | all agents | 2026.5.18 → 2026.7.1-2, full testbed run first | MED | TBD | 🟡 PLAN FIRST |
| 7 | Honcho 3.0.11 → 3.0.12 | honcho-m1 | Rebuild image, redeploy | LOW | TBD | 🟡 SCHEDULE |
| 8 | Ubuntu apt upgrade (both) | testbed + honcho | Security + system packages incl. Docker stack | LOW | TBD | 🟡 SCHEDULE |
| 9 | Tailscale 1.98.4 → 1.102.2 | testbed-m1 | Update + verify | LOW | TBD | 🟡 SCHEDULE |
| 10 | Website Tester doc | — | Read Fast.io doc, write Testbed implementation doc | — | 2026-08-11 Mon | 🔴 READY |

---

## Version Log

*Append-only. One row per change.*

| Date | Service | From | To | Machine | Result | Snapshot |
|---|---|---|---|---|---|---|
| 2026-07-20 | MemPalace + Honcho | — | 3.0.11 | honcho-m1 | ✅ | Honch01-M1-Pre-MemPalace-07-20-2026 |
| 2026-08-07 | Honcho .env embedding fix | missing key | LLM_OPENAI_API_KEY set | honcho-m1 | ✅ | pre-honcho-addmessages-fix-2026-08-07-1048 (417407465) |

---

## References

- SOP-19: Infrastructure Maintenance Schedule (governance repo)
- AGENTS.md: Hetzner snapshot hard rule
- BOOTSTRAP.md: Session startup — Step 2 reads this file

---

*Read this file during bootstrap. Update action queue after every session.*
