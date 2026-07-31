#!/usr/bin/env python3
"""
Daily export of #testing-env Slack channel to Fast.io.
Migrated from Dropbox implementation 2026-07-31.
Part of MemPalace Layer 1 — Channel History Infrastructure.
Run nightly via systemd timer.
"""

import json, os, sys, subprocess
from datetime import datetime, timedelta, timezone
import requests

CHANNEL_ID = "C0B1WLM3P8X"
CHANNEL_NAME = "testing-env"
LOCAL_EXPORT_BASE = os.path.expanduser("~/.openclaw/workspace/memory/slack-exports")
FASTIO_FOLDER_ID = "2mbwh-2sh23-fphxq-e7ika-ue5ti-e4ed"  # Slack Exports/testing-env

def get_bot_token():
    with open(os.path.expanduser("~/.openclaw/openclaw.json")) as f:
        d = json.load(f)
    return d["channels"]["slack"]["botToken"]

def get_fastio_config():
    env_path = os.path.expanduser("~/.openclaw/workspace/.env.fastio")
    with open(env_path) as f:
        lines = f.readlines()
    config = {}
    for line in lines:
        if line.startswith("FASTIO_"):
            key, val = line.strip().split("=", 1)
            config[key] = val
    return config

def fetch_history(token, oldest, latest):
    messages, cursor = [], None
    while True:
        params = {"channel": CHANNEL_ID, "oldest": str(oldest),
                  "latest": str(latest), "limit": 200, "inclusive": True}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get("https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {token}"}, params=params).json()
        if not resp.get("ok"):
            print(f"Error: {resp.get('error')}", file=sys.stderr); break
        messages.extend(resp.get("messages", []))
        if not resp.get("has_more"): break
        cursor = resp.get("response_metadata", {}).get("next_cursor")
    return messages

def get_user_name(token, uid, cache={}):
    if uid in cache: return cache[uid]
    r = requests.get("https://slack.com/api/users.info",
        headers={"Authorization": f"Bearer {token}"}, params={"user": uid}).json()
    name = r.get("user", {}).get("real_name", uid) if r.get("ok") else uid
    cache[uid] = name
    return name

def upload_to_fastio(local_path, fastio_token, workspace_id, folder_id):
    """Upload file to Fast.io using CLI."""
    cmd = [
        "fastio", "--token", fastio_token,
        "upload", "file",
        "--workspace", workspace_id,
        "--folder", folder_id,
        "--format", "json",
        local_path
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Upload failed: {result.stderr}", file=sys.stderr)
        return False
    
    return True

def main():
    target_date_str = sys.argv[1] if len(sys.argv) > 1 else None
    if target_date_str:
        target_date = datetime.strptime(target_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    else:
        target_date = (datetime.now(timezone.utc) - timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0)
    oldest = target_date.timestamp()
    latest = (target_date + timedelta(days=1)).timestamp()
    date_str = target_date.strftime("%Y-%m-%d")

    # Fetch Slack messages
    token = get_bot_token()
    messages = fetch_history(token, oldest, latest)
    messages = [m for m in messages if m.get("type") == "message" and not m.get("subtype")]
    messages.sort(key=lambda m: float(m.get("ts", 0)))

    # Generate markdown
    lines = [f"# #{CHANNEL_NAME} — {date_str}", ""]
    for m in messages:
        ts = datetime.fromtimestamp(float(m["ts"]), tz=timezone.utc).strftime("%H:%M UTC")
        user = get_user_name(token, m.get("user", "unknown"))
        text = m.get("text", "").replace("\n", "  \n")
        lines.append(f"**{ts} {user}:** {text}")
        lines.append("")

    # Write to local file
    out_dir = os.path.join(LOCAL_EXPORT_BASE, CHANNEL_NAME)
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{date_str}.md")
    with open(out_path, "w") as f:
        f.write("\n".join(lines))
    print(f"Exported {len(messages)} messages to {out_path}")

    # Upload to Fast.io
    fastio_config = get_fastio_config()
    fastio_token = fastio_config["FASTIO_TOKEN"]
    workspace_id = fastio_config["FASTIO_WORKSPACE_ID"]
    
    print(f"Uploading to Fast.io: Slack Exports/testing-env/{date_str}.md")
    success = upload_to_fastio(out_path, fastio_token, workspace_id, FASTIO_FOLDER_ID)
    
    if success:
        print(f"✅ Upload complete: Slack Exports/testing-env/{date_str}.md")
    else:
        print(f"❌ Upload failed", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
