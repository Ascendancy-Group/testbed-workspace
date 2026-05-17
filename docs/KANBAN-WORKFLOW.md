# Kanban-Driven Agent Collaboration Workflow

**Last Updated:** 2026-05-16  
**Status:** Proven and Active  
**Scope:** Infrastructure testing, app dev, web dev, Azure deployments, security testing

---

## Overview

Autonomous agent collaboration via GitHub Issues + automated polling. Agents monitor assigned tickets, pick up work automatically, post evidence, and hand off without manual coordination.

**Key Principle:** Work = assigned GitHub issue. No issue assigned = agent idles. Evidence lives in the ticket, not chat.

---

## Architecture

### Components

1. **GitHub Issues** — work tickets with clear pass/fail criteria
2. **Systemd poller** — checks for assigned tickets every 2 minutes
3. **Agent runtime** — OpenClaw agent executes work when poller finds assignment
4. **Evidence trail** — all command output, findings, and decisions posted to ticket
5. **GitHub Discussions** (optional) — design debates and blockers before ticketing

### Workflow States

```
Unassigned → Assigned → In Progress → Evidence Posted → Closed
```

---

## Setup (Per Agent)

### 1. GitHub Account & PAT

Each agent needs:
- GitHub account (e.g., `Testbed-Ascendancy`)
- Personal Access Token with `repo` scope
- Org membership in `Ascendancy-Group`
- Collaborator or write access to testing repo

**Store PAT in:**
- 1Password: `<AgentName>-GitHub-PAT`
- Configure `gh` CLI: `gh auth login --with-token < token_file`

### 2. Polling Script

**Location:** `~/.openclaw/workspace/scripts/kanban-monitor.py`

```python
#!/usr/bin/env python3
"""
Kanban ticket monitor — checks for assigned GitHub issues every 2 minutes.
When an assigned ticket is found, triggers OpenClaw session to work it.
"""

import subprocess
import sys
import json

REPO = "Ascendancy-Group/ascendancy-testing"

def check_assigned_tickets():
    """Query GitHub for issues assigned to @me"""
    result = subprocess.run(
        ["gh", "issue", "list", "--repo", REPO, "--assignee", "@me", 
         "--state", "open", "--json", "number,title"],
        capture_output=True, text=True
    )
    
    if result.returncode != 0:
        print(f"Error querying GitHub: {result.stderr}", file=sys.stderr)
        return []
    
    try:
        issues = json.loads(result.stdout)
        return issues
    except json.JSONDecodeError:
        print(f"Failed to parse GitHub response", file=sys.stderr)
        return []

def main():
    issues = check_assigned_tickets()
    
    if not issues:
        print("No assigned tickets")
        return
    
    for issue in issues:
        print(f"Found assigned ticket: #{issue['number']} - {issue['title']}")
        # Trigger OpenClaw session to work the ticket
        # Implementation depends on your OpenClaw setup
        # Example: subprocess.run(["openclaw", "run", "--task", f"Work on ticket #{issue['number']}"])

if __name__ == "__main__":
    main()
```

**Make executable:**
```bash
chmod +x ~/.openclaw/workspace/scripts/kanban-monitor.py
```

### 3. Systemd Service

**Service file:** `~/.config/systemd/user/kanban-poll.service`

```ini
[Unit]
Description=Kanban Polling Service — Auto-pickup assigned GitHub tickets
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 %h/.openclaw/workspace/scripts/kanban-monitor.py
Restart=always
RestartSec=120

[Install]
WantedBy=default.target
```

**Enable and start:**
```bash
systemctl --user daemon-reload
systemctl --user enable kanban-poll.service
systemctl --user start kanban-poll.service
```

**Verify:**
```bash
systemctl --user status kanban-poll.service
journalctl --user -u kanban-poll.service -f
```

---

## Creating Work Tickets

### Ticket Structure

**Title:** `[TEST-XX] Brief description — what's being validated`

**Required sections:**

```markdown
## Goal
What are we proving or building?

## Pass Criteria
1. Criterion 1 — specific, testable
2. Criterion 2 — specific, testable
3. Criterion 3 — specific, testable

## Evidence Required
- Actual command output (no paraphrasing)
- Screenshots where applicable
- Links to artifacts

## Reference
Link to design docs, prior tickets, or templates

## Notes
- Scope boundaries
- Out-of-scope items
- Dependencies
```

**Example:** See [TEST-02 (Issue #3)](https://github.com/Ascendancy-Group/ascendancy-testing/issues/3)

### Ticket Lifecycle

1. **Creation** — Bob, Pieter, or agent creates ticket (unassigned by default)
2. **Assignment** — Assign to agent GitHub username when ready to start
3. **Auto-pickup** — Agent poller detects assignment within 2 minutes
4. **Work** — Agent validates criteria, posts evidence as comments
5. **Completion** — Agent posts summary, requests closure (if no permissions) or closes directly
6. **Review** — Bob/Pieter reviews evidence, closes if passed

---

## Agent Work Protocol

### When Poller Finds Assignment

1. **Fetch ticket details:** `gh issue view <number> --repo <repo>`
2. **Parse pass criteria** — extract testable items
3. **Execute validation** — run commands, capture output
4. **Post evidence** — `gh issue comment <number> --body "<evidence>"`
5. **Update status** — close if passed and permitted, otherwise request closure

### Evidence Standards

**DO:**
- Post actual command output verbatim
- Include timestamps and system context
- Show both success and failure paths
- Link to artifacts (commits, files, logs)

**DON'T:**
- Paraphrase output
- Claim success without evidence
- Skip edge cases
- Post private/secret data

### Example Evidence Comment

```markdown
## ✅ Criterion 1: Export script exists

​```
$ ls -lh ~/.openclaw/workspace/scripts/slack-export-testing-env.py
-rwxrwxr-x 1 pieter pieter 2.7K May 16 18:52 /home/pieter/.openclaw/workspace/scripts/slack-export-testing-env.py
​```

## ✅ Criterion 2: Output directory exists

​```
$ ls -lah ~/.openclaw/workspace/memory/slack-exports/testing-env/
total 92K
drwxrwxr-x 2 pieter pieter 4.0K May 16 18:53 .
drwxrwxr-x 3 pieter pieter 4.0K May 16 10:03 ..
-rw-rw-r-- 1 pieter pieter 43K May 15 23:00 2026-05-15.md
-rw-rw-r-- 1 pieter pieter 48K May 16 18:53 2026-05-16.md
​```
```

---

## GitHub Discussions (Optional)

Use Discussions for design debates and blockers **before** creating tickets.

### Categories

- **💡 Ideas & Proposals** — architecture decisions, test approach debates
- **🚧 Blockers** — issues needing input before work can proceed
- **📚 Knowledge Base** — "How does X work?" reference material
- **🔄 Retrospectives** — what worked/failed after test cycles

### Discussion → Issue Flow

1. Unclear architecture? → Start Discussion
2. Gather input from Bob/Pieter/peers
3. Decision made? → Create Issue with clear pass criteria
4. Issue assigned → Agent picks up automatically

**Benefit:** Keeps Issues actionable (poller-friendly) while Discussions capture messy pre-work thinking.

---

## Operational Rules

### Assignment Protocol

- **Only assign when ready to start** — agent picks up within 2 minutes
- **One agent per ticket** — no concurrent assignments
- **Reassign for handoff** — remove current assignee, add next agent

### Communication Boundaries

- **Evidence → Ticket comments** (primary record)
- **Blockers → Ticket comments** (quick) or Discussions (complex)
- **Status updates → Ticket comments** (not Slack)
- **Slack** → coordination, approvals, urgent escalations only

### No-Spam Rule

Agents do NOT:
- Post every 2-minute poll result to Slack
- Flood channels with status updates
- Announce ticket pickup/completion in chat (unless explicitly requested)

---

## Cost Management

### Free Model for Polling

Poller uses **no LLM calls** — just GitHub API checks every 2 minutes.

**Cost:** ~$0/month for polling loop itself.

### Paid Model for Work

When an assigned ticket is found, agent invokes OpenClaw session with configured model (e.g., `claude-sonnet-4-5`).

**Cost:** Only incurred during active work on assigned tickets.

### Overnight Behavior

**Recommended:** Leave poller running 24/7.
- No assigned tickets = no cost
- Timer survives reboots
- Picks up morning assignments automatically

---

## Proven Outcomes (2026-05-16)

### TEST-01: Kanban Polling Setup
- ✅ Systemd service running 4+ hours continuously
- ✅ Polling every 2 minutes
- ✅ Auto-restart on failure
- ✅ Evidence: [Issue #2](https://github.com/Ascendancy-Group/ascendancy-testing/issues/2)

### TEST-02: MemPalace Validation
- ✅ Ticket assigned at 18:51 CDT
- ✅ Agent picked up within 1 minute (already active)
- ✅ Diagnosed path misconfiguration
- ✅ Applied fix, validated 5 criteria
- ✅ Posted full evidence with command output
- ✅ Completed at 18:54 CDT (3-minute turnaround)
- ✅ Evidence: [Issue #3](https://github.com/Ascendancy-Group/ascendancy-testing/issues/3)

---

## Scaling to Other Work Types

This workflow applies to:

- **Infrastructure testing** (current use)
- **App development** — feature tickets with acceptance criteria
- **Web development** — UI component tickets with screenshots
- **Azure deployments** — deployment tickets with validation steps
- **Security testing** — pentest tickets with findings and remediation

**Key:** Clear pass criteria + evidence requirements = autonomous agent work.

---

## Troubleshooting

### Poller not picking up assigned ticket

1. Verify service is running: `systemctl --user status kanban-poll.service`
2. Check logs: `journalctl --user -u kanban-poll.service -n 50`
3. Verify assignment: `gh issue view <number> --repo <repo> --json assignees`
4. Verify `gh` CLI auth: `gh auth status`

### Agent lacks permissions to close issues

Grant agent account **Triage** or **Write** role in GitHub repo settings.

Workaround: Agent posts "Ready to close" comment, human closes manually.

### Secret leaked in ticket comment

GitHub push protection catches secrets in code, but not in Issue comments.

**Prevention:**
- Redact PATs, passwords, API keys before posting
- Use `[REDACTED]` placeholders
- Review evidence before submitting

---

## Future Enhancements

- [ ] Auto-close on pass (requires Write permissions)
- [ ] Slack notification on ticket completion (opt-in)
- [ ] Time-boxed ticket execution (auto-reassign after X hours)
- [ ] Priority labels (high/normal/low)
- [ ] Scheduled ticket visibility (GitHub Actions workflow)

---

## References

- **Testing repo:** https://github.com/Ascendancy-Group/ascendancy-testing
- **Testbed workspace:** https://github.com/Ascendancy-Group/testbed-workspace
- **Kanban board:** https://github.com/orgs/Ascendancy-Group/projects/8
- **Proven test examples:** Issues #2, #3

---

**Maintained by:** Testbed, Bob, Pieter  
**Status:** Production-ready as of 2026-05-16
