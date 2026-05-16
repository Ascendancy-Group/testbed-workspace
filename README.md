# Testbed — Workspace 🧪

*Agent: Testbed*
*Owner: Pieter van der Wal*
*Last updated: 2026-05-12*

---

## What This Is

Testbed's workspace — infrastructure tester and recovery engineer operating under OpenClaw. Nothing goes to production without passing through here first.

This repo is *public within Ascendancy-Group* by design. Proven scripts, approaches, and checklists here are available for Bob, Mason, and Forge to copy and deploy to production.

---

## Key Files

| File | Purpose |
|---|---|
| `SOUL.md` | Identity, values, behavior — who Testbed is |
| `IDENTITY.md` | Name, role, machine, chain of command |
| `AGENTS.md` | Session startup and end discipline |
| `BRIEF.md` | Mission, test queue, what Testbed does/doesn't do |
| `USER.md` | About Pieter, about Bob, how decisions flow |
| `TRUST.md` | Chain of command, approval gates |
| `MEMORY.md` | Test queue, proven approaches, known failures |
| `HANDOFF.md` | Current test state between sessions |
| `memory/YYYY-MM-DD.md` | Daily test logs |

---

## Key Principle

Every successful test produces three things:
1. A written result
2. A repeatable script
3. A verification checklist

If you can't produce all three, the test isn't done.

---

## Governance

Testbed reads `Ascendancy-Group/ascendancy-governance` every session — SOPs, lessons learned, toolsets, workflows.
When a test proves a new approach → update or create an SOP in the governance repo.
Identity files (this repo) are Testbed's own. Governance repo is process only.
