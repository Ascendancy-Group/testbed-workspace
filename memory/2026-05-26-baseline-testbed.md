# QW-01: Baseline Measurement — Testbed
*Date: 2026-05-26 15:50 CDT*
*Agent: Testbed (testbed-m1)*
*Ticket: https://github.com/Ascendancy-Group/ascendancy-testing/issues/28*

## Bootstrap Context Files

- **SOUL.md:** 6111 chars, 133 lines (~1527 tokens)
- **AGENTS.md:** 3905 chars, 81 lines (~976 tokens)
- **MEMORY.md:** 3977 chars, 153 lines (~994 tokens)
- **USER.md:** 1491 chars, 52 lines (~372 tokens)
- **TOOLS.md:** 636 chars, 19 lines (~159 tokens)
- **HEARTBEAT.md:** 392 chars, 10 lines (~98 tokens)
- **IDENTITY.md:** 1254 chars, 40 lines (~313 tokens)
- **HANDOFF.md:** 6014 chars, 152 lines (~1503 tokens)

**Total Bootstrap:** 23780 chars (~5945 tokens)

---

## Weekly Cost Analysis

[openclaw] Could not start the CLI.
[openclaw] Reason: Unknown command: openclaw analytics. No built-in command or plugin CLI metadata owns "analytics".
[openclaw] Debug: set OPENCLAW_DEBUG=1 to include the stack trace.
[openclaw] Try: openclaw doctor
[openclaw] Help: openclaw --help
Error: analytics command failed

*Note: `openclaw analytics` command not available in this version.*

## Gateway Status

Service: systemd user (enabled)
File logs: /tmp/openclaw/openclaw-2026-05-26.log
Command: /usr/bin/openclaw gateway run
Service file: ~/.config/systemd/user/openclaw-gateway.service

Config (cli): ~/.openclaw/openclaw.json
Config (service): ~/.openclaw/openclaw.json

Gateway: bind=loopback (127.0.0.1), port=18789 (env/config)
Probe target: ws://127.0.0.1:18789
Dashboard: http://127.0.0.1:18789/
Probe note: Loopback-only gateway; only local clients can connect.

CLI version: 2026.5.18 (/usr/bin/openclaw)
Gateway version: 2026.5.18

Runtime: running (pid 77086, state active, sub running, last exit 0, reason 0)
Connectivity probe: ok
Capability: admin-capable


---

## Summary

**Total bootstrap injection:** 23,780 characters (~5,945 tokens estimated)

**Largest files:**
1. HANDOFF.md: 6,014 chars
2. SOUL.md: 6,111 chars  
3. MEMORY.md: 3,977 chars (153 lines - **exceeds 100-line target**)

**Target after cleanup:**
- MEMORY.md: <100 lines (<3,000 chars)
- Total bootstrap: <20,000 chars

**Next:** QW-02 (MEMORY.md Cleanup)
