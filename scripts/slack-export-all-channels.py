#!/usr/bin/env python3
"""
Daily export of ALL Slack channels to Fast.io Ascendancy Context folder.
Owner: Testbed (assigned 2026-07-31)
Run nightly via systemd timer.
"""

import json, os, sys, subprocess
from datetime import datetime, timedelta, timezone
import requests

LOCAL_EXPORT_BASE = os.path.expanduser("~/.openclaw/workspace/memory/slack-exports")
FASTIO_ASCENDANCY_CONTEXT_ID = "2empi-q7kbz-3cg26-ijavr-m22ue-hyic"

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

def get_all_channels(token):
    """Fetch all public and private channels."""
    channels = []
    cursor = None
    
    while True:
        params = {"types": "public_channel,private_channel", "limit": 100}
        if cursor:
            params["cursor"] = cursor
        
        resp = requests.get("https://slack.com/api/conversations.list",
            headers={"Authorization": f"Bearer {token}"}, params=params).json()
        
        if not resp.get("ok"):
            print(f"Error fetching channels: {resp.get('error')}", file=sys.stderr)
            break
        
        channels.extend(resp.get("channels", []))
        
        if not resp.get("response_metadata", {}).get("next_cursor"):
            break
        cursor = resp["response_metadata"]["next_cursor"]
    
    return channels

def fetch_history(token, channel_id, oldest, latest):
    messages, cursor = [], None
    while True:
        params = {"channel": channel_id, "oldest": str(oldest),
                  "latest": str(latest), "limit": 200, "inclusive": True}
        if cursor:
            params["cursor"] = cursor
        resp = requests.get("https://slack.com/api/conversations.history",
            headers={"Authorization": f"Bearer {token}"}, params=params).json()
        if not resp.get("ok"):
            if resp.get("error") == "not_in_channel":
                # Bot not in channel, skip silently
                return []
            print(f"Error fetching history for {channel_id}: {resp.get('error')}", file=sys.stderr)
            break
        messages.extend(resp.get("messages", []))
        if not resp.get("has_more"):
            break
        cursor = resp.get("response_metadata", {}).get("next_cursor")
    return messages

def get_user_name(token, uid, cache={}):
    if uid in cache:
        return cache[uid]
    r = requests.get("https://slack.com/api/users.info",
        headers={"Authorization": f"Bearer {token}"}, params={"user": uid}).json()
    name = r.get("user", {}).get("real_name", uid) if r.get("ok") else uid
    cache[uid] = name
    return name

def get_or_create_channel_folder(fastio_token, workspace_id, parent_id, channel_name):
    """Get or create subfolder for channel under Ascendancy Context."""
    # List existing folders
    cmd = [
        "fastio", "--token", fastio_token,
        "files", "list",
        "--workspace", workspace_id,
        "--folder", parent_id,
        "--format", "json"
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        data = json.loads(result.stdout)
        for item in data.get("nodes", {}).get("items", []):
            if item.get("type") == "folder" and item.get("name") == channel_name:
                return item.get("id")
    
    # Create folder
    cmd = [
        "fastio", "--token", fastio_token,
        "files", "create-folder",
        "--workspace", workspace_id,
        "--parent", parent_id,
        "--format", "json",
        channel_name
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        return json.loads(result.stdout).get("node", {}).get("id")
    
    return None

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
    return result.returncode == 0

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

    # Get Slack token and channels
    token = get_bot_token()
    channels = get_all_channels(token)
    
    # Get Fast.io config
    fastio_config = get_fastio_config()
    fastio_token = fastio_config["FASTIO_TOKEN"]
    workspace_id = fastio_config["FASTIO_WORKSPACE_ID"]
    
    print(f"Exporting {len(channels)} channels for {date_str}")
    
    success_count = 0
    skip_count = 0
    error_count = 0
    
    for channel in channels:
        channel_name = channel["name"]
        channel_id = channel["id"]
        
        # Fetch messages
        messages = fetch_history(token, channel_id, oldest, latest)
        
        if not messages:
            skip_count += 1
            continue
        
        # Filter and sort
        messages = [m for m in messages if m.get("type") == "message" and not m.get("subtype")]
        messages.sort(key=lambda m: float(m.get("ts", 0)))
        
        # Generate markdown
        lines = [f"# #{channel_name} — {date_str}", ""]
        for m in messages:
            ts = datetime.fromtimestamp(float(m["ts"]), tz=timezone.utc).strftime("%H:%M UTC")
            user = get_user_name(token, m.get("user", "unknown"))
            text = m.get("text", "").replace("\n", "  \n")
            lines.append(f"**{ts} {user}:** {text}")
            lines.append("")
        
        # Write to local file
        out_dir = os.path.join(LOCAL_EXPORT_BASE, channel_name)
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"{date_str}.md")
        with open(out_path, "w") as f:
            f.write("\n".join(lines))
        
        # Get or create channel folder in Fast.io
        folder_id = get_or_create_channel_folder(fastio_token, workspace_id, 
                                                  FASTIO_ASCENDANCY_CONTEXT_ID, channel_name)
        
        if not folder_id:
            print(f"❌ Failed to create folder for #{channel_name}", file=sys.stderr)
            error_count += 1
            continue
        
        # Upload to Fast.io
        if upload_to_fastio(out_path, fastio_token, workspace_id, folder_id):
            print(f"✅ #{channel_name}: {len(messages)} messages → Ascendancy Context/{channel_name}/{date_str}.md")
            success_count += 1
        else:
            print(f"❌ Upload failed for #{channel_name}", file=sys.stderr)
            error_count += 1
    
    print(f"\n📊 Summary: {success_count} succeeded, {skip_count} skipped (no messages), {error_count} failed")
    
    if error_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
