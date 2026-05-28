#!/home/pieter/.openclaw/workspace/.venv-dropbox/bin/python3
"""
Simple Dropbox MCP client for uploading files
Uses the Dropbox MCP server at http://100.77.0.47:3001
"""
import sys
import json
import base64
from pathlib import Path

def upload_file(local_path: str, dropbox_path: str):
    """
    Upload a file to Dropbox via the MCP server
    
    Args:
        local_path: Path to local file
        dropbox_path: Destination path in Dropbox (e.g., "(Admin)/Dropbox MCP/file.md")
    """
    # Read the file
    file_path = Path(local_path).expanduser()
    if not file_path.exists():
        print(f"Error: File not found: {local_path}", file=sys.stderr)
        return False
    
    content = file_path.read_text()
    
    # Use the Dropbox SDK directly (simpler than MCP protocol)
    import dropbox
    
    # Get token from 1Password
    import subprocess
    result = subprocess.run(
        ['op', 'read', 'op://AgentStack/Dropbox - Testbed Access/credential'],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        print("Error: Could not get Dropbox token from 1Password", file=sys.stderr)
        return False
    
    token = result.stdout.strip()
    
    # Upload to Dropbox
    dbx = dropbox.Dropbox(token)
    
    # Ensure path starts with /
    if not dropbox_path.startswith('/'):
        dropbox_path = '/' + dropbox_path
    
    try:
        dbx.files_upload(
            content.encode('utf-8'),
            dropbox_path,
            mode=dropbox.files.WriteMode.overwrite
        )
        print(f"✅ Uploaded: {local_path} → {dropbox_path}")
        return True
    except Exception as e:
        print(f"❌ Upload failed: {e}", file=sys.stderr)
        return False


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print("Usage: dropbox-upload.py <local_file> <dropbox_path>")
        print("Example: dropbox-upload.py ~/file.md '(Admin)/Dropbox MCP/file.md'")
        sys.exit(1)
    
    success = upload_file(sys.argv[1], sys.argv[2])
    sys.exit(0 if success else 1)
