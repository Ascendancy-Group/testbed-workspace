#!/usr/bin/env python3
"""
Honcho Client for OpenClaw Agent Integration (SDK v2.2.0+)
Connects agents to centralized Honcho server at http://100.77.0.47:8000

NOTE: SDK v2.2.0 changed significantly. This client provides minimal
health check and context verification. Full write integration TBD.
"""

import sys
import json
from datetime import datetime, timezone
from honcho import Honcho

HONCHO_API_URL = "http://100.77.0.47:8000"
HONCHO_WORKSPACE = "ascendancy"  # Shared workspace for all agents

def get_peer_name():
    """Determine peer name from hostname or default to 'pieter'"""
    import socket
    hostname = socket.gethostname()
    
    # Map machine hostnames to peer names
    hostname_map = {
        "testbed-m1": "testbed",
        "bobwebdev-m1": "bob",
        "mason-m1": "mason",
        "forge-m1": "forge"
    }
    
    return hostname_map.get(hostname.lower(), "pieter")

def health_check():
    """Check Honcho server health and return status"""
    try:
        client = Honcho(
            api_key="ignored",
            base_url=HONCHO_API_URL,
            workspace_id=HONCHO_WORKSPACE
        )
        peer_name = get_peer_name()
        
        # Try to list peers as health check
        peers = list(client.peers())
        sessions = list(client.sessions())
        
        print(json.dumps({
            "status": "ok",
            "workspace": HONCHO_WORKSPACE,
            "peer": peer_name,
            "server": HONCHO_API_URL,
            "peers_count": len(peers),
            "sessions_count": len(sessions)
        }, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2))
        return 1

def get_context():
    """Fetch context from Honcho for current peer"""
    try:
        client = Honcho(
            api_key="ignored",
            base_url=HONCHO_API_URL,
            workspace_id=HONCHO_WORKSPACE
        )
        peer_name = get_peer_name()
        
        # SDK v2.2.0: search for existing sessions for this peer
        sessions = list(client.sessions())
        peer_sessions = [s for s in sessions if peer_name.lower() in (s.name or "").lower()]
        
        has_context = len(peer_sessions) > 0
        
        print(json.dumps({
            "status": "ok",
            "has_context": has_context,
            "peer": peer_name,
            "session_count": len(peer_sessions),
            "total_sessions": len(sessions),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2))
        return 1

def write_session(session_summary):
    """Write session summary to Honcho (placeholder - SDK v2.2.0 API TBD)"""
    try:
        # SDK v2.2.0 session write API is unclear from current testing
        # Need to investigate proper session creation pattern
        # For now, return success but flag as not implemented
        
        peer_name = get_peer_name()
        
        print(json.dumps({
            "status": "partial",
            "peer": peer_name,
            "note": "SDK v2.2.0 session write API needs investigation",
            "summary_length": len(session_summary),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, indent=2))
        return 0
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "error": str(e)
        }, indent=2))
        return 1

def main():
    if len(sys.argv) < 2:
        print("Usage: honcho_client.py <command> [args]", file=sys.stderr)
        print("Commands:", file=sys.stderr)
        print("  health                    - Check server health", file=sys.stderr)
        print("  get-context               - Fetch peer context", file=sys.stderr)
        print("  write-session '<summary>' - Write session summary (partial)", file=sys.stderr)
        return 1
    
    command = sys.argv[1]
    
    if command == "health":
        return health_check()
    elif command == "get-context":
        return get_context()
    elif command == "write-session":
        if len(sys.argv) < 3:
            print("Error: write-session requires a summary argument", file=sys.stderr)
            return 1
        return write_session(sys.argv[2])
    else:
        print(f"Error: Unknown command '{command}'", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
