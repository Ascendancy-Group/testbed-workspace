# Slack Channel Troubleshooting — 2026-05-14

**Problem:** OpenClaw agent (Testbed) could receive Slack DMs but not channel messages.

**Duration:** ~3 hours of systematic diagnostics

**Final Status:** ✅ **RESOLVED**

---

## Symptoms

- ✅ Slack DMs worked (inbound messages received)
- ✅ Outbound channel messages worked (bot could send to channels)
- ❌ **Inbound channel messages silently dropped** (no response, no errors in logs)
- ✅ Bot was member of channels (verified via Slack API)
- ✅ Socket Mode connected (verified in logs)

---

## Root Causes Identified

### 1. Missing Slack Event Subscriptions (Initial)
**Problem:** Slack app had event subscriptions disabled.

**Fix:** Enabled in Slack app settings → Event Subscriptions → Subscribe to bot events:
- `message.channels`
- `message.groups`
- `message.im`
- `app_mention`

**Result:** Still didn't work — led to deeper investigation.

---

### 2. OpenClaw 2026.5.7 Schema Validation Bug (Major Blocker)
**Problem:** Documented Slack group config syntax was rejected by 2026.5.7 config validator.

**Attempted config (from official docs):**
```json
{
  "channels": {
    "slack": {
      "groupPolicy": "allowlist",
      "groupAllowFrom": ["U0ANQ79KGAV", "U0AN4UEHAG3"],
      "channels": {
        "C0B1WLM3P8X": {"enabled": true, "requireMention": false}
      }
    }
  }
}
```

**Error:**
```
channels.slack: invalid config: must NOT have additional properties
Gateway aborted: config is invalid.
```

**Diagnosis:**
- Config syntax is documented in `/usr/lib/node_modules/openclaw/docs/channels/groups.md` and `slack.md`
- 2026.5.7 schema validator rejects `groupAllowFrom` as "additional property"
- `openclaw doctor --fix` would **strip out** manually-added channel config instead of migrating it
- Bug persists in 2026.5.12 as well

**Root cause:** `groupPolicy: "allowlist"` + empty `groupAllowFrom` = **all group/channel messages silently dropped**

Per `openclaw doctor` warning:
> channels.slack.groupPolicy is "allowlist" but groupAllowFrom (and allowFrom) is empty — all group messages will be silently dropped.

---

### 3. Missing Slack Plugin After Upgrade (2026.5.12)
**Problem:** After upgrading from 2026.5.7 → 2026.5.12, Slack plugin was no longer bundled.

**Error:**
```
│ Slack    │ ON      │ WARN   │ plugin not installed - run openclaw plugins install @openclaw/slack
```

**Fix:**
```bash
openclaw plugins install @openclaw/slack
openclaw gateway restart
```

**Note:** First attempt used `sudo` which installed to `/root/.openclaw/` instead of `/home/pieter/.openclaw/`. Had to reinstall without sudo.

---

## Working Solution

### Final Config (`~/.openclaw/openclaw.json`)

```json
{
  "channels": {
    "slack": {
      "botToken": "xoxb-...",
      "appToken": "xapp-...",
      "enabled": true,
      "groupPolicy": "open",
      "channels": {
        "C0B1WLM3P8X": {
          "enabled": true,
          "requireMention": false
        },
        "C0B3WJ141H8": {
          "enabled": true,
          "requireMention": false
        }
      }
    }
  }
}
```

**Key change:** `"groupPolicy": "open"` instead of `"allowlist"`

**Why this works:**
- `"open"` bypasses sender allowlists entirely
- No need for `groupAllowFrom` (which the schema rejects anyway)
- Channel messages are accepted from any sender
- Still respects `channels` allowlist (only configured channels are monitored)

**Security trade-off:** This allows ANY workspace member to trigger the agent in configured channels. For testbed, this is acceptable. For production, consider:
- Using private channels with explicit membership
- Adding `requireMention: true` if you want @mention gating
- Or wait for schema fix to use `groupPolicy: "allowlist"` with `groupAllowFrom`

---

## Verification Steps

After applying the working config:

```bash
# 1. Upgrade to 2026.5.12
sudo openclaw update

# 2. Install Slack plugin (without sudo)
openclaw plugins install @openclaw/slack

# 3. Restart gateway
openclaw gateway restart

# 4. Verify Slack status
openclaw status | grep -A2 "Slack"
# Expected: │ Slack    │ ON      │ OK     │ tokens ok...

# 5. Verify channels resolved
journalctl --user -u openclaw-gateway.service -n 100 | grep "channels resolved"
# Expected: [slack] channels resolved: C0B1WLM3P8X→testing-env, C0B3WJ141H8→testing-env--public

# 6. Test in Slack
# Send a message in #testing-env or #testing-env--public
# Bot should respond without requiring @mention
```

---

## What Didn't Work (Dead Ends)

1. **Rebuilding Slack app from scratch** — considered but unnecessary; app config was correct
2. **Removing/re-inviting bot to channels** — didn't help; wasn't a membership issue
3. **Manual token regeneration** — tokens were already valid
4. **Switching to HTTP Request URLs mode** — Socket Mode was working; not the issue
5. **`groupPolicy: "allowlist"` with `groupAllowFrom`** — rejected by schema validator in both 2026.5.7 and 2026.5.12

---

## Lessons Learned

### For Future Slack Troubleshooting

**Start here (checklist):**

1. **Verify event subscriptions** in Slack app:
   - `message.channels` (public channels)
   - `message.groups` (private channels)
   - `message.im` (DMs)
   - After changes: **reinstall app to workspace**

2. **Check OpenClaw config:**
   ```bash
   openclaw doctor
   ```
   Look for: `groupPolicy is "allowlist" but groupAllowFrom is empty`

3. **Verify plugin installed:**
   ```bash
   openclaw status | grep Slack
   ```
   If `WARN plugin not installed`: `openclaw plugins install @openclaw/slack`

4. **Use `groupPolicy: "open"` as first-pass workaround** if schema rejects `groupAllowFrom`

5. **Verify Socket Mode connected:**
   ```bash
   journalctl --user -u openclaw-gateway.service | grep "socket mode connected"
   ```

6. **Test DMs first** — if DMs don't work, it's an auth/token issue; if only channels fail, it's group policy

### Known Bugs in 2026.5.7 and 2026.5.12

- Schema validator rejects `groupAllowFrom` under `channels.slack` even though it's documented
- `openclaw doctor --fix` strips manually-added Slack group config instead of migrating it
- Slack plugin not bundled in 2026.5.12 (must be installed separately)

### Recommended Production Config (when schema is fixed)

```json
{
  "channels": {
    "slack": {
      "groupPolicy": "allowlist",
      "groupAllowFrom": ["U0ANQ79KGAV", "U0AN4UEHAG3"],
      "channels": {
        "C0B1WLM3P8X": {"enabled": true, "requireMention": false}
      }
    }
  }
}
```

**When schema accepts this**, switch from `"open"` to `"allowlist"` for better security.

---

## Timeline

| Time | Event |
|------|-------|
| 12:43 | Initial request: configure Slack channel monitoring |
| 12:49 | Added channel config, backed up `openclaw.json` |
| 12:50 | Set `requireMention: false` for #testing-env |
| 12:53 | Verified outbound works (sent test message) |
| 12:57 | Confirmed Slack app event subscriptions were disabled |
| 12:59 | Enabled event subscriptions, reinstalled Slack app |
| 13:01 | Still no channel messages (only DMs working) |
| 13:04 | Created public test channel (#testing-env--public) |
| 13:06 | Confirmed bot is member of both channels (API verified) |
| 13:11 | Removed/re-invited bot (no effect) |
| 13:13 | Diagnosed: Slack app config correct, but events not delivered |
| 13:16 | Read troubleshooting doc: identified `groupAllowFrom` requirement |
| 13:18 | Added `groupAllowFrom` → schema rejected config |
| 13:40 | Created Hetzner snapshot: `Testbed-M1-Snapshot-Slack-troubleshooting-5-14-2026` |
| 14:04 | Attempted `openclaw doctor --fix` → stripped config instead of fixing |
| 14:10 | Approved upgrade to 2026.5.12 (after snapshot) |
| 14:49 | Upgrade completed (required `sudo openclaw update`) |
| 14:55 | Discovered Slack plugin missing in 2026.5.12 |
| 15:14 | Installed Slack plugin (wrong user first, then corrected) |
| 15:16 | Changed to `groupPolicy: "open"` (bypasses schema bug) |
| 15:18 | ✅ **SUCCESS** — channel messages working |

**Total diagnostic time:** ~3 hours

---

## Follow-Up Actions

1. **File bug report** for OpenClaw schema validator rejecting `groupAllowFrom` (documented but unsupported in 2026.5.7 and 2026.5.12)
2. **Update HANDOFF.md** with resolution
3. **Update MEMORY.md** with proven approaches
4. **Consider security hardening** when schema is fixed (switch to `groupPolicy: "allowlist"`)
5. **Document for Bob** — if he hits similar issues in production, use `groupPolicy: "open"` workaround

---

## Files Changed

- `~/.openclaw/openclaw.json` — added Slack channel config with `groupPolicy: "open"`
- `~/.openclaw/workspace/HANDOFF.md` — documented troubleshooting state
- `~/.openclaw/workspace/memory/2026-05-14-slack-channel-troubleshooting.md` — this file
- `~/.openclaw/workspace/Backups-Granular/openclaw.json__*` — multiple backups during troubleshooting

---

## Success Criteria Met

- ✅ Testbed responds to messages in #testing-env (private channel)
- ✅ Testbed responds to messages in #testing-env--public (public channel)
- ✅ No @mention required (`requireMention: false`)
- ✅ DMs continue to work
- ✅ Socket Mode connected and stable
- ✅ Config survives `openclaw gateway restart`

---

**Status:** RESOLVED — Slack channel monitoring fully operational as of 2026-05-14 15:18 CDT.
