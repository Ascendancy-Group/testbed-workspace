#!/usr/bin/env python3
"""
Kanban Monitor for Testbed Agent  
Polls Ascendancy Testing Kanban every 2 minutes
"""

import subprocess
import json
import time
import sys
from datetime import datetime

REPO = "Ascendancy-Group/ascendancy-testing"
CHECK_INTERVAL = 120  # 2 minutes

def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {msg}", flush=True)

def get_assigned_issues():
    try:
        cmd = ["gh", "issue", "list", "--repo", REPO, "--assignee", "@me", "--state", "open", "--json", "number,title,url"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    except Exception as e:
        log(f"Error: {e}")
        return []

def main():
    log(f"🧪 Testbed Kanban Monitor - {REPO}")
    last_seen = set()
    
    while True:
        try:
            issues = get_assigned_issues()
            current = {i['number'] for i in issues}
            
            new = current - last_seen
            if new:
                for n in new:
                    issue = next(i for i in issues if i['number'] == n)
                    log(f"🎯 New: #{n} - {issue['title']}")
            
            if issues:
                log(f"📋 Assigned: {len(issues)}")
            else:
                log("📋 No assigned tickets")
            
            last_seen = current
        except Exception as e:
            log(f"❌ Error: {e}")
        
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log("🛑 Stopped")
        sys.exit(0)
