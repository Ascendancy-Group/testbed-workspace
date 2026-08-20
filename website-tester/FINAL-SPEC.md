# Website Tester Agent — Final Combined Spec
*Authors: Testbed + Bob (collaboration, 2026-08-20)*
*Status: APPROVED FOR BUILD*

---

## Decision Log (where we differed, what we agreed)

| Topic | Testbed proposed | Bob proposed | Final decision | Rationale |
|---|---|---|---|---|
| Agent name | Falco Unguis | Probus | **Probus** | Shorter, cleaner, production-grade |
| Architecture | 4 agents (coordinator, explorer, a11y, reporter) | 2 agents (coordinator + explorer) | **2 agents to start** | Ship working first, add specialists when volume justifies |
| Schedule | Heartbeat | openclaw cron | **openclaw cron** | Fixed time, no drift |
| noSandbox | true (VPS) | false | **true** | VPS requires it — no user namespaces |
| headless | true | false | **true** | Server — no display |
| Install approach | Verify each tool independently | Install all then test | **Testbed approach** | Isolates failures cleanly |
| Primary target | GFMJ staging | gofindmyjob.com prod | **Both** — smoke prod nightly, dev on demand |
| Visual regression | Playwright built-in first | Playwright built-in | **Playwright built-in** | Zero external dependency |

---

## 1. What We're Building

A dedicated OpenClaw agent server (`probus-m1`) running two agents:
- `probus` — coordinator/main. Runs full audits, interprets results, writes reports, fires Slack alerts
- `probus-explorer` — cheap fast browser agent. Does the actual crawling, screenshots, form tests

Stack: OpenClaw + browser tool (CDP) + axe-core + Lighthouse + Playwright + Python Slack alerter

---

## 2. Server Spec

| Item | Value |
|---|---|
| Provider | Hetzner Cloud |
| Type | cx23 (cheapest — €6.49/mo) |
| Specs | 2 vCPU, 4GB RAM, 40GB disk |
| OS | Ubuntu 24.04 |
| Location | Same DC as existing fleet |
| Name | probus-m1 |
| SSH key | Default Ascendancy Provisioning Key (id: 111299452) |
| Tailscale | Yes — join ascendancy tailnet |
| OpenClaw | Install via standard SOP-10 provisioning |

---

## 3. Agent Identity

### probus (coordinator)
- Model: `github-copilot/claude-sonnet-4-6` (coordinates, judges, writes reports)
- Heartbeat: nightly at 02:15 America/Chicago via cron

### probus-explorer
- Model: `github-copilot/claude-haiku-4-5` (cheap fast crawler)
- No heartbeat — spawned by probus on demand

### SOUL.md (probus)
Senior adversarial QA engineer. Finds what breaks sites before users do. Systematic, evidence-based, blunt. Every finding must have severity, steps to reproduce, expected vs actual, evidence (screenshot or console output). Never marks a page passed without testing at least 3 negative/edge cases. Reports blockers — never guesses through them.

---

## 4. Toolchain

```
~/.openclaw/tools/
├── package.json
├── node_modules/
│   ├── @axe-core/playwright
│   ├── playwright
│   └── lighthouse
├── run-axe.js          # axe-core wrapper (from Bob's plan — clean, no changes needed)
└── slack_qa_alert.py   # Slack Block Kit alerter (from source doc Appendix H)

~/.openclaw/workspace/website-tester/
├── screenshots/
├── a11y/
├── lighthouse/
├── reports/
└── baselines/
```

---

## 5. Nightly Smoke Scope

Targets:
- `https://gofindmyjob.com` (prod — nightly)
- Staging URL on demand

Nightly checks:
1. Homepage loads (200, no critical console errors)
2. Main navigation renders and links resolve
3. Login page reachable, form renders
4. One critical happy-path flow (job search or sign-up)
5. axe-core on homepage + login (critical + serious violations only)
6. Lighthouse on homepage (Performance + Accessibility scores)
7. Full-page screenshot: desktop (1440px) + mobile (390px)

Output:
- Report: `reports/nightly-YYYY-MM-DD.md`
- Critical/High findings → Slack alert to #qa-alerts
- Clean run → "✅ Nightly smoke passed" summary
- Full report uploaded as file, never pasted inline
- Retain 14 days, delete older

---

## 6. openclaw.json Config (probus-m1)

```json
{
  "browser": {
    "enabled": true,
    "evaluateEnabled": true,
    "headless": true,
    "defaultProfile": "openclaw",
    "noSandbox": true,
    "profiles": {
      "openclaw": {}
    },
    "ssrfPolicy": {
      "dangerouslyAllowPrivateNetwork": false
    }
  },
  "agents": {
    "defaults": {
      "bootstrapMaxChars": 15000,
      "bootstrapTotalMaxChars": 60000
    },
    "entries": {
      "probus": {
        "default": true,
        "workspace": "/home/pieter/.openclaw/workspaces/probus"
      },
      "probus-explorer": {
        "workspace": "/home/pieter/.openclaw/workspaces/probus-explorer"
      }
    }
  }
}
```

Model config: via `openclaw models auth login-github-copilot` after provisioning (Probus@ascendancy GH account — Pieter to auth tonight).

---

## 7. Cron Setup

```bash
# Nightly smoke — 02:15 America/Chicago daily
openclaw cron add \
  --name "probus-nightly-smoke" \
  --schedule "15 2 * * *" \
  --timezone "America/Chicago" \
  --agent probus \
  --session-target isolated \
  --prompt "Execute the Nightly Smoke Audit from HEARTBEAT.md exactly. Target: https://gofindmyjob.com"

# Report retention — 03:00 daily
openclaw cron add \
  --name "probus-report-retention" \
  --schedule "0 3 * * *" \
  --agent probus \
  --session-target isolated \
  --prompt "Delete nightly reports older than 14 days: find ~/.openclaw/workspace/website-tester/reports -name 'nightly-*.md' -mtime +14 -delete"
```

---

## 8. Build Sequence (what I'm executing today)

1. ✅ Pre-work Hetzner snapshot of Testbed-M1 (safety)
2. Provision probus-m1 (cx23, Ubuntu 24.04) via Hetzner API
3. Bootstrap: Tailscale, OpenClaw install (SOP-10)
4. Write SOUL.md, AGENTS.md, HEARTBEAT.md to probus workspace
5. Install toolchain: npm + playwright + axe-core + lighthouse
6. Validate each tool independently (Testbed's install protocol)
7. Configure openclaw.json (browser + agents)
8. Set up cron jobs
9. Manual smoke test against gofindmyjob.com
10. **Pieter auths probus via GH Copilot device flow tonight**
11. Validate nightly smoke fires (manual trigger, not wait for 02:15)
12. Slack alert confirmed in #qa-alerts
13. Document + commit everything to testbed-workspace

---

## 9. What Pieter Does Tonight

One step: `openclaw models auth login-github-copilot --yes` on probus-m1

I'll have the server up and OpenClaw installed before end of day. You auth the GH Copilot account (Probus@ascendancy — same pattern as the reauth we did 2026-08-19 for Testbed and Vera) and it's live.

---

## 10. Hand-off Criteria

Testbed signs off when:
- [ ] All tool installs verified independently
- [ ] `openclaw browser snapshot` returns valid a11y tree on probus-m1
- [ ] axe-core runs clean against example.com
- [ ] Lighthouse returns JSON scores
- [ ] Manual smoke audit runs against gofindmyjob.com
- [ ] Nightly cron fires (manual trigger)
- [ ] Slack alert appears in #qa-alerts
- [ ] All scripts committed to testbed-workspace with README

---

*This spec supersedes both individual plans. Decisions are final.*
