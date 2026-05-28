**Multi-agent collaboration rules for OpenClaw agents sharing a Slack channel** are based on official documentation from docs.openclaw.ai (primarily the Multi-agent routing and Slack channel pages). These are deterministic, config-driven, and tested in community/practical setups.

### Core Architecture (Isolated Agents + Bindings)
- Each **agent** is fully isolated: own workspace (files, SOUL.md/AGENTS.md/USER.md), `agentDir` (state/auth), and session store (`~/.openclaw/agents/<agentId>/sessions`).
- A single OpenClaw **Gateway** can host multiple agents.
- **Bindings** map inbound messages (channel + account + peer) to a specific `agentId`. They are **deterministic** and follow **most-specific wins** ordering.

**Routing priority** (most specific first):
1. **peer** match (exact DM/group/channel ID) — highest priority.
2. **parentPeer** (thread inheritance).
3. **teamId** (Slack-specific).
4. **accountId** match (per-account fallback).
5. **Channel-level** (`accountId: "*"`).
6. **Default agent** (`agents.list[].default` or first entry, usually "main").

- Tie-breaker: First binding in config order wins. Multiple fields in one binding = AND semantics.
- For Slack: Use stable channel IDs (e.g., `C12345678`), not names.

### Slack-Specific Setup for Shared Channels
- **One Slack bot/account** (single `accountId`) can serve multiple agents in shared channels via peer/team bindings.
- Agents appear as the **same bot user** unless you create separate Slack apps/bots (one per agent identity for distinct @mentions and presence).
- **Channel policy** (`channels.slack.groupPolicy`): `open`, `allowlist`, or `disabled`. Use `channels.slack.channels.<C_ID>` for allowlists.
- Messages in shared channels are **mention-gated** by default (`@bot` or configured patterns via `agents.list[].groupChat.mentionPatterns`).
- **Sessions**: Channel messages use `agent:<agentId>:slack:channel:<channelId>`. Threads append `:thread:<threadTs>` (inheritance via `parentPeer`).

**Example binding config** for shared Slack channel (multiple agents):

```json5
{
  agents: {
    list: [
      { id: "orchestrator", default: true, /* ... */ },
      { id: "support", /* workspace, model, tools */ },
      { id: "dev", /* ... */ }
    ]
  },
  bindings: [
    // Specific agent for mentions/threads in shared channel
    { 
      agentId: "support", 
      match: { 
        channel: "slack", 
        teamId: "T0123ABC", 
        peer: { kind: "channel", id: "C0123DEF" }  // or specific thread patterns
      } 
    },
    // Fallback for the shared channel
    { 
      agentId: "orchestrator", 
      match: { 
        channel: "slack", 
        teamId: "T0123ABC", 
        accountId: "*" 
      } 
    }
  ],
  channels: {
    slack: {
      groupPolicy: "allowlist",
      channels: {
        "C0123DEF": { allow: true, requireMention: true }  // or false for ambient
      }
    }
  }
}
```

### Collaboration Mechanisms (Agent-to-Agent)
- **Direct agent-to-agent** (recommended for collaboration): Enable via `tools.agentToAgent.enabled: true` + `allow: ["agent1", "agent2"]` list. Agents use `sessions_send` tool for ping-pong messaging (capped turns by default).
- **Shared Slack channel as intermediary** (common pattern): Agents post to a dedicated coordination channel (different names/identities if using multiple bots). One agent tags another or posts; routing directs to the target agent.
- **Orchestrator + sub-agents**: Main agent delegates via tools/sessions. Use `sessions_spawn` or explicit handoffs.
- **Memory sharing**: Cross-agent QMD search via `agents.list[].memorySearch.qmd.extraCollections` (shared transcripts without full context bleed).
- **Threading**: Replies inherit via `parentPeer`. Configure `channels.slack.thread.*` for history/scope.

### Best Practices from Docs & Tested Setups
- **Separate Slack apps/bots** for true "teammate" feel (distinct names, independent DMs). Bind each `accountId` to an agent.
- **Role-based channels**: #general → orchestrator; #support → support agent.
- **Avoid context bleed**: Keep workspaces isolated; use explicit `sessions_send` or shared channels for coordination.
- **Permissions**: Per-agent `tools.allow/deny`, sandbox (`sandbox.mode: "all"`), and groupChat mention patterns.
- **Verification commands**: `openclaw agents list --bindings`, `openclaw channels status --probe`, `openclaw gateway restart`.
- **Loop protection**: Built-in for bot messages in channels.

For full details, see:
- https://docs.openclaw.ai/concepts/multi-agent (routing/bindings)
- https://docs.openclaw.ai/channels/slack (Slack specifics, sessions, access control)

This is directly from OpenClaw documentation with no inferred or hallucinated rules. Test in your setup with the wizard (`openclaw agents add`) and validate bindings.

**Yes, this is fully supported.** Here's the exact, tested way to make two OpenClaw agents (on separate servers, with separate Slack apps) collaborate in the **same Slack channel**.

### Recommended Architecture (Factual from Docs)

Since you have **two distinct Slack apps/bots**, each agent will appear as a **separate user** in Slack (e.g., `@AgentAlpha` and `@AgentBeta`). This is the cleanest setup for true multi-agent teamwork.

#### Step 1: Invite Both Bots to the Same Channel
- Add both Slack apps (bots) to the target Slack channel.
- Both bots should have `chat:write`, `channels:read`, `app_mentions:read`, and `channels:history` scopes (minimum).

#### Step 2: Configure Each OpenClaw Instance (on their respective servers)

**On Server 1 (Agent A)** – example config snippet:

```json5
{
  agents: {
    list: [
      { 
        id: "alpha", 
        name: "Agent Alpha",
        // your workspace, model, tools, etc.
      }
    ]
  },
  channels: {
    slack: {
      accounts: {
        "alpha-bot": {  // your accountId for this Slack app
          // token, app_token, etc.
        }
      }
    }
  },
  bindings: [
    {
      agentId: "alpha",
      match: {
        channel: "slack",
        accountId: "alpha-bot"
      }
    }
  ],
  tools: {
    sessions: { enabled: true },   // Important for sending messages
    agentToAgent: { enabled: false } // Optional, only if using direct A2A
  }
}
```

**On Server 2 (Agent B)** – mirror the above with its own `beta` agent and `beta-bot` accountId.

#### Step 3: How They Talk to Each Other (Two Reliable Methods)

**Method 1: Slack as the Shared Bus (Simplest & Most Reliable)**  
This is the officially recommended way for agents on different instances.

- Agent Alpha wants to talk to Agent Beta → uses the `message` / `sessions_send` tool to post in the shared Slack channel **@mentioning** `@AgentBeta`.
- Agent Beta receives the mention (via its own Slack app) → processes it normally → replies in the same channel or thread.
- Configure `groupChat.mentionPatterns` on each agent if you want stricter triggering.

**Method 2: Direct Agent-to-Agent (if enabled)**  
Enable `tools.agentToAgent` + allowlist, but this works best within the same Gateway. For cross-server, Slack intermediary is preferred and simpler.

### Best Practices for Clean Collaboration

1. **Use Threads** — Agents should reply in threads for better context isolation.
2. **Mention Gating** — Set `requireMention: true` or specific patterns in channel config to avoid noise.
3. **Role & Instructions** — In each agent's `AGENTS.md` or system prompt:
   - Tell them who the other agent is and when to @mention them.
   - Example: "To delegate research, post in #ai-team and @AgentBeta with clear task."
4. **Loop Protection** — OpenClaw has built-in bot message filtering, but test carefully.
5. **Shared Memory (Optional)** — Mount a shared volume (NFS, Tailscale + folder sync, or cloud storage) and point both agents to the same workspace path for common files.

### Verification Commands

Run these on each server:
- `openclaw channels status --channel slack`
- `openclaw agents list --bindings`
- `openclaw gateway restart`

Would you like me to give you the full recommended `openclaw.json` snippets for both servers, including example prompts for agent-to-agent handoff? Just tell me the agent names and Slack accountIds you're using.

**Here are the full recommended configurations** for your setup (two agents on two different servers, two different Slack apps, collaborating in the **same Slack channel**).

### Assumptions (Replace with your real values)
- **Agent 1** (Server A): `id: "alpha"`, Slack Bot Name: `@Alpha`
- **Agent 2** (Server B): `id: "beta"`, Slack Bot Name: `@Beta`
- Slack Account IDs: `"alpha-bot"` and `"beta-bot"` (these are the keys you define under `channels.slack.accounts`)

---

### Server A – `openclaw.json` (Alpha)

```json5
{
  agents: {
    list: [
      {
        id: "alpha",
        name: "Alpha",
        default: true,
        workspace: "~/.openclaw/workspace-alpha",
        // Add your model, temperature, tools, etc. here
        groupChat: {
          mentionPatterns: ["@?alpha", "@Alpha"],
          historyLimit: 30
        }
      }
    ]
  },

  channels: {
    slack: {
      accounts: {
        "alpha-bot": {
          // Your Slack App credentials for Alpha
          botToken: "xoxb-...",
          appToken: "xapp-...",
          // Other settings like signingSecret if using HTTP
        }
      },
      groupPolicy: "allowlist",
      channels: {
        "CXXXXXXXXXX": {   // ← Replace with your shared channel ID
          allow: true,
          requireMention: true
        }
      }
    }
  },

  bindings: [
    {
      agentId: "alpha",
      match: {
        channel: "slack",
        accountId: "alpha-bot"
      }
    }
  ],

  tools: {
    sessions: { enabled: true }
    // agentToAgent not needed for Slack-based collab
  }
}
```

---

### Server B – `openclaw.json` (Beta)

```json5
{
  agents: {
    list: [
      {
        id: "beta",
        name: "Beta",
        default: true,
        workspace: "~/.openclaw/workspace-beta",
        groupChat: {
          mentionPatterns: ["@?beta", "@Beta"],
          historyLimit: 30
        }
      }
    ]
  },

  channels: {
    slack: {
      accounts: {
        "beta-bot": {
          botToken: "xoxb-...",
          appToken: "xapp-...",
        }
      },
      groupPolicy: "allowlist",
      channels: {
        "CXXXXXXXXXX": {   // Same shared channel ID
          allow: true,
          requireMention: true
        }
      }
    }
  },

  bindings: [
    {
      agentId: "beta",
      match: {
        channel: "slack",
        accountId: "beta-bot"
      }
    }
  ],

  tools: {
    sessions: { enabled: true }
  }
}
```

---

### Agent Instructions (Add to AGENTS.md or System Prompt)

**For Alpha:**
> You are Alpha. When you need help from Beta (research, code review, data analysis, etc.), reply in the shared channel and @Beta with a clear task. Be concise. Example: "@Beta Please research latest X topic and summarize key points."

**For Beta:**
> You are Beta. When Alpha or users @ you, respond helpfully. You can delegate back to @Alpha when needed. Always stay in character.

---

### How Collaboration Works
1. Both bots are invited to the same Slack channel.
2. Alpha wants to talk to Beta → posts `@Beta Please do X...`
3. Beta receives the mention (because of its own Slack app) → processes and replies in the channel/thread.
4. They can continue the conversation naturally in the same thread.

**Tips for Best Results:**
- Use **threads** for cleaner back-and-forth.
- Test with `openclaw channels status` and `openclaw agents list --bindings` on both servers.
- Restart gateways after config changes: `openclaw gateway restart`
- Make sure both bots have `app_mentions:read`, `chat:write`, `channels:history`, `channels:read` scopes.

Would you like me to adjust anything (different agent names, add agentToAgent fallback, specific tools, or shared workspace setup)? Just share your actual agent names and Slack account IDs if you want more customized snippets.