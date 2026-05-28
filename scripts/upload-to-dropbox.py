#!/home/pieter/.openclaw/workspace/.venv-dropbox/bin/python3
"""
Upload file to Dropbox using 1Password credentials
Based on SOP-04 fallback method
"""
import urllib.request
import urllib.parse
import json
import os
import sys
from pathlib import Path

def get_1password_field(item, field):
    """Get a field from 1Password using op CLI"""
    import subprocess
    result = subprocess.run(
        ['op', 'read', f'op://AgentStack/{item}/{field}'],
        capture_output=True,
        text=True
    )
    if result.returncode != 0:
        raise RuntimeError(f"Failed to read {item}/{field} from 1Password: {result.stderr}")
    return result.stdout.strip()

def get_access_token():
    """Get Dropbox access token via refresh token"""
    app_key = get_1password_field('Dropbox - BobBuilder App', 'App Key')
    app_secret = get_1password_field('Dropbox - BobBuilder App', 'App Secret')
    refresh_token = get_1password_field('Dropbox - BobBuilder App', 'Refresh Token')
    
    body = urllib.parse.urlencode({
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': app_key,
        'client_secret': app_secret
    }).encode()
    
    req = urllib.request.Request(
        'https://api.dropboxapi.com/oauth2/token',
        data=body
    )
    
    response = urllib.request.urlopen(req)
    result = json.loads(response.read())
    return result['access_token']

def upload_file(local_path, dropbox_path):
    """Upload a file to Dropbox"""
    file_path = Path(local_path).expanduser()
    if not file_path.exists():
        print(f"❌ Error: File not found: {local_path}", file=sys.stderr)
        return False
    
    # Get access token
    print("🔑 Getting Dropbox access token...", file=sys.stderr)
    token = get_access_token()
    
    # Read file
    with open(file_path, 'rb') as f:
        data = f.read()
    
    # Ensure path starts with /
    if not dropbox_path.startswith('/'):
        dropbox_path = '/' + dropbox_path
    
    print(f"📤 Uploading {len(data)} bytes to {dropbox_path}...", file=sys.stderr)
    
    # Upload
    req = urllib.request.Request(
        'https://content.dropboxapi.com/2/files/upload',
        data=data,
        headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/octet-stream',
            'Dropbox-API-Arg': json.dumps({
                'path': dropbox_path,
                'mode': 'overwrite',
                'autorename': False
            })
        }
    )
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read())
        print(f"✅ Uploaded: {result['path_display']} | Size: {result['size']} bytes")
        return True
    except urllib.error.HTTPError as e:
        print(f"❌ Upload failed: {e.code} {e.reason}", file=sys.stderr)
        print(e.read().decode('utf-8'), file=sys.stderr)
        return False

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: upload-to-dropbox.py <local_file> <dropbox_path>")
        print("Example: upload-to-dropbox.py ~/file.md '(Admin)/Dropbox MCP/file.md'")
        sys.exit(1)
    
    success = upload_file(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
