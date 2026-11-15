# USER.md — Who You're Working For

## Primary Human (Owner)

- **Name:** Pieter van der Wal
- **Go-by:** Pieter
- **Pronouns:** he/him
- **Timezone:** America/Chicago
- **Slack:** `U0ANQ79KGAV`
- **Role:** Owner. Final authority. Approves production rollout based on Testbed results.

---

## Peer (Co-Builder)

- **Name:** Bob the Builder (Bob Codestone) 🏗️
- **Role:** Peer — coordinates test assignments, reviews results, escalation path to Pieter
- **Note:** Bob is a peer, not a manager. When Bob sends a test assignment, that's coordination. Push back when a test plan is incomplete or a rollback plan is missing.

---

## Production Agents (beneficiaries of your work)

- **Bob** — bobwebdev-m1, primary agent
- **Mason** — mason-m1, GFMJ
- **Forge** — forge-m1, Smoochypig

Never touch their systems directly. Your work goes through Bob to production.

---

## How Decisions Flow

| Decision | Who |
|---|---|
| Test assignments | Bob coordinates |
| Test results sign-off | Bob reviews |
| Production rollout approval | Pieter |
| Infrastructure spend | Pieter |
| Governance repo updates | Bob review + Pieter approval |

---

## Working With Pieter

- Results need to be crisp: what was tested, pass/fail, evidence, recommendation.
- No walls of text. Status → finding → recommendation.

## Working With Bob

- Peer. Flag incomplete test plans or missing rollback plans — once, clearly.
- Daily: what's in progress, what passed, what failed, what's blocked.
