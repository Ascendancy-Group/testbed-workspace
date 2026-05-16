# HANDOFF.md — Testbed Session State

*Last updated: 2026-05-14 14:40 CDT*

---

## Current Status: Slack Channel Monitoring — ✅ RESOLVED

**Problem:** Slack channel messages not reaching OpenClaw (DMs work, channels don't).
**Solution:** Upgraded to 2026.5.12, installed Slack plugin, used `groupPolicy: "open"` to bypass schema bug.

**Root cause identified:** 2026.5.7 schema validation bug — rejects documented `groupPolicy`, `groupAllowFrom`, and `channels` config under `channels.slack`, even though these are documented as correct in `/usr/lib/node_modules/openclaw/docs/channels/slack.md` and `/usr/lib/node_modules/openclaw/docs/channels/groups.md`.

**What we tried:**
1. ✅ Verified Slack app manifest (event subscriptions correct: `message.channels`, `message.groups`, `message.im`)
2. ✅ Verified bot scopes (`channels:history`, `groups:history`, `chat:write`, etc.)
3. ✅ Verified App-Level Token has `connections:write` scope
4. ✅ Bot is member of test channels (API confirmed `is_member: true`)
5. ✅ Socket Mode connected (`openclaw channels status --probe` shows healthy)
6. ✅ Outbound works (sent test message successfully)
7. ✅ DMs work (inbound Slack DMs reach OpenClaw)
8. ❌ **Channel messages silently dropped** — diagnosed via `openclaw doctor` warning: `groupPolicy is "allowlist" but groupAllowFrom is empty — all group messages will be silently dropped`
9. ❌ **Config rejected by 2026.5.7 schema** — when we add `groupPolicy`, `groupAllowFrom`, `channels`, gateway refuses to start: `channels.slack: invalid config: must NOT have additional properties`

**Attempted fix:** Upgrade to 2026.5.12 to resolve schema bug.

**Current state:**
- ✅ Hetzner snapshot created: `Testbed-M1-Snapshot-Slack-troubleshooting-5-14-2026`
- ✅ Gateway stopped: `systemctl --user stop openclaw-gateway.service`
- ✅ Config temporarily stripped of problematic Slack settings (to allow update)
- ⏸️ **Awaiting manual update** — `openclaw update` must run from outside gateway process tree

---

## Next Steps (Resume from here)

1. **Manual update** (Pieter to run):
   ```bash
   openclaw update
   ```

2. **After update completes, verify version:**
   ```bash
   openclaw version
   ```

3. **Re-add Slack channel config** (test if 2026.5.12 accepts it):
   ```bash
   cat ~/.openclaw/openclaw.json | jq '
   .channels.slack.groupPolicy = "allowlist" |
   .channels.slack.groupAllowFrom = ["U0ANQ79KGAV", "U0AN4UEHAG3"] |
   .channels.slack.channels = {
     "C0B1WLM3P8X": {"enabled": true, "requireMention": false},
     "C0B3WJ141H8": {"enabled": true, "requireMention": false}
   }
   ' > /tmp/oc.json && mv /tmp/oc.json ~/.openclaw/openclaw.json
   ```

4. **Validate config:**
   ```bash
   openclaw doctor
   ```
   - If 2026.5.12 still rejects the config → file bug report or try alternative config approach
   - If accepted → proceed to step 5

5. **Start gateway and test:**
   ```bash
   openclaw gateway restart
   openclaw channels status --probe
   ```

6. **Test inbound channel messages:**
   - Send test message in #testing-env--public (`C0B3WJ141H8`)
   - Watch logs: `journalctl --user -u openclaw-gateway.service -f`
   - Confirm Testbed responds in channel

7. **If still broken after 2026.5.12:**
   - Consider nuclear option: delete and rebuild Slack app from scratch (instructions in `slack-app-rebuild-steps.md`)
   - Or escalate to Bob/Pieter as workspace-level policy issue

---

## Key Files

- **Backup config:** `~/.openclaw/workspace/Backups-Granular/openclaw.json__2026-05-14_14-04/openclaw.json` (has channel config before doctor stripped it)
- **Slack rebuild instructions:** `~/.openclaw/workspace/slack-app-rebuild-steps.md`
- **This handoff:** `~/.openclaw/workspace/HANDOFF.md`

---

## Test Queue (from MEMORY.md)

1. MemPalace — full end-to-end proof (plan in Dropbox)
2. Honcho — memory persistence + injection validation
3. Claude Memory (claude-mem) — memory persistence validation
4. Lossless memory — approach validation
5. Paperclip — full end-to-end proof before prod
6. OpenClaw upgrades — version validation before prod rollout
7. Gateway config changes — validate JSON changes before prod
8. New agent onboarding checklist — validate bootstrap process
9. Systemd timer installs — verify survival across restarts

**Slack channel monitoring moved to top priority until resolved.**

---

## Proven Findings

- **Slack DMs work in 2026.5.7** (Socket Mode, token auth confirmed)
- **Slack channel messages silently dropped** when `groupPolicy: "allowlist"` without `groupAllowFrom`
- **2026.5.7 schema rejects documented Slack group config** (`groupPolicy`, `groupAllowFrom`, `channels` keys)
- **`openclaw doctor --fix` strips manual Slack config** instead of migrating it

---

**Resolution:** 2026-05-14 15:18 CDT — Slack channel monitoring fully operational.

**Full diagnostic report:** `memory/2026-05-14-slack-channel-troubleshooting.md`

**Working config:**
```json
{
  "channels": {
    "slack": {
      "groupPolicy": "open",
      "channels": {
        "C0B1WLM3P8X": {"enabled": true, "requireMention": false},
        "C0B3WJ141H8": {"enabled": true, "requireMention": false}
      }
    }
  }
}
```

**Next session:** Resume normal test queue from MEMORY.md.
