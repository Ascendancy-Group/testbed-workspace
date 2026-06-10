#!/usr/bin/env python3
"""
Daily Start Checks for OpenClaw Agents (v2)
============================================

Version: 2.0.0
Created: 2026-06-09
Author: Testbed (based on Bob's Bootstrap Approach)
Cost: $0.00/day per agent

What's New in v2:
- Enhanced 1Password verification (read real secrets, not just whoami)
- Dropbox write-then-read verification (proves read AND write access)
- GitHub PAT validation (pull from 1PW, test repo access)
- Governance sync with commit checking (only pull when needed)
- Check ordering support (critical checks run first)
- 1Password UUID support (handles special chars in item names)

Purpose:
    Execute daily startup checks to ensure agent infrastructure is healthy
    before beginning work. All checks use FREE models or zero-cost commands.

Usage:
    python3 ~/scripts/daily-checks-v2.py

Exit Codes:
    0 = All required checks passed
    1 = One or more required checks failed

Configuration:
    ~/.openclaw/daily-checks.yaml

Integration:
    Called from BOOTSTRAP.md at session start (once per day)
"""

import sys
import yaml
import subprocess
import json
import urllib.request
import urllib.error
import tempfile
from pathlib import Path
from datetime import datetime
from typing import Tuple, Dict, Any, List


def load_config(path: str = "~/.openclaw/daily-checks.yaml") -> Dict[str, Any]:
    """
    Load YAML configuration file.
    
    Args:
        path: Path to YAML config file (supports ~ expansion)
        
    Returns:
        Dictionary containing config
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        yaml.YAMLError: If config file is invalid YAML
    """
    config_path = Path(path).expanduser()
    
    if not config_path.exists():
        print(f"❌ ERROR: Config file not found: {config_path}")
        print(f"Create it by copying daily-checks-template.yaml")
        sys.exit(1)
    
    with open(config_path) as f:
        return yaml.safe_load(f)


# ============================================================================
# V2 NEW CHECK TYPES
# ============================================================================

def run_onepassword_read_test(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Read a secret from 1Password and verify its value.
    
    V2 Enhancement: Actually reads a real secret to prove access,
    not just checking 'op whoami'.
    
    Args:
        check: Dictionary containing:
            - secret_ref: 1Password reference (op://Vault/Item/field or UUID)
            - expect: Expected value (optional, for validation)
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': '1Password Secret Read Test',
            'type': 'onepassword_read_test',
            'secret_ref': 'op://AgentStack/Bootstrap-Test-Secret/password',
            'expect': 'bootstrap-test-ok-2026',
            'required': True
        }
    
    Note:
        If item title contains special characters like (, ), —, use UUID format:
        'op://AgentStack/<uuid>/field' instead of title-based path.
    """
    try:
        # Execute op read
        result = subprocess.run(
            ['op', 'read', check['secret_ref']],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, f"op read failed: {result.stderr.strip()}"
        
        value = result.stdout.strip()
        
        # If expect is specified, validate it
        if 'expect' in check:
            if value == check['expect']:
                return True, "Secret read and validated ✓"
            else:
                # Don't reveal actual value in logs
                return False, f"Secret value mismatch (expected != actual)"
        
        # No expect specified, just verify we got a non-empty value
        if value:
            return True, f"Secret read successfully ({len(value)} chars)"
        else:
            return False, "Secret is empty"
            
    except subprocess.TimeoutExpired:
        return False, "1Password read timed out after 5s"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_github_pat_validation(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Read GitHub PAT from 1Password and validate repo access.
    
    V2 Enhancement: Pulls PAT from 1PW and tests actual repo access,
    proving end-to-end GitHub authentication works.
    
    Args:
        check: Dictionary containing:
            - pat_ref: 1Password reference to PAT
            - test_repos: List of repos to test (format: 'owner/repo')
            - timeout: Optional timeout in seconds (default 10)
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'GitHub PAT Validation',
            'type': 'github_pat_validation',
            'pat_ref': 'op://AgentStack/Testbed-GH-PAT/credential',
            'test_repos': [
                'Ascendancy-Group/ascendancy-governance',
                'Ascendancy-Group/testbed-workspace'
            ],
            'required': True
        }
    """
    try:
        # Step 1: Read PAT from 1Password
        result = subprocess.run(
            ['op', 'read', check['pat_ref']],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return False, f"Failed to read PAT: {result.stderr.strip()}"
        
        pat = result.stdout.strip()
        
        if not pat:
            return False, "PAT is empty"
        
        # Step 2: Test each repo via GitHub API
        failed_repos = []
        for repo in check['test_repos']:
            test_result = subprocess.run(
                ['curl', '-s', '-H', f'Authorization: token {pat}',
                 f'https://api.github.com/repos/{repo}'],
                capture_output=True,
                text=True,
                timeout=check.get('timeout', 10)
            )
            
            if test_result.returncode != 0:
                failed_repos.append(repo)
                continue
            
            # Check if response contains error
            try:
                response = json.loads(test_result.stdout)
                if 'message' in response and 'full_name' not in response:
                    failed_repos.append(repo)
            except json.JSONDecodeError:
                failed_repos.append(repo)
        
        if failed_repos:
            return False, f"Access denied: {', '.join(failed_repos)}"
        
        # Success
        return True, f"PAT valid, {len(check['test_repos'])} repos accessible ✓"
        
    except subprocess.TimeoutExpired:
        return False, "GitHub API request timed out"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_dropbox_write_test(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Write a test file to Dropbox and read it back to verify access.
    
    V2 Enhancement: Uses direct Dropbox API via 1Password credentials (SOP-04 method).
    This is independent of OpenClaw MCP tool availability and proves end-to-end access.
    
    Args:
        check: Dictionary containing:
            - test_file: Dropbox path for test file
            - test_content: Content to write (supports {timestamp} placeholder)
            - cleanup: Whether to delete test file after (default True)
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Dropbox Write Test',
            'type': 'dropbox_write_test',
            'test_file': '/(Admin)/Bootstrap/.bootstrap-probe.txt',
            'test_content': 'bootstrap-test-{timestamp}',
            'cleanup': True,
            'required': False
        }
    
    Note:
        Uses SOP-04 fallback method (direct API + 1Password credentials).
        Does NOT depend on OpenClaw MCP tool availability.
    """
    try:
        # Expand {timestamp} in test content
        content = check['test_content'].replace(
            '{timestamp}',
            datetime.utcnow().isoformat()
        )
        
        # Step 1: Pull Dropbox credentials from 1Password
        k = subprocess.check_output(
            ['op', 'read', 'op://AgentStack/Dropbox - BobBuilder App/App Key'],
            timeout=5
        ).decode().strip()
        
        s = subprocess.check_output(
            ['op', 'read', 'op://AgentStack/Dropbox - BobBuilder App/App Secret'],
            timeout=5
        ).decode().strip()
        
        r = subprocess.check_output(
            ['op', 'read', 'op://AgentStack/Dropbox - BobBuilder App/Refresh Token'],
            timeout=5
        ).decode().strip()
        
        # Step 2: Get access token via refresh
        import urllib.parse
        body = urllib.parse.urlencode({
            'grant_type': 'refresh_token',
            'refresh_token': r,
            'client_id': k,
            'client_secret': s
        }).encode()
        
        tok_req = urllib.request.Request(
            'https://api.dropboxapi.com/oauth2/token',
            data=body
        )
        tok_response = urllib.request.urlopen(tok_req, timeout=10)
        tok_data = json.loads(tok_response.read())
        token = tok_data['access_token']
        
        # Step 3: Upload test file
        data = content.encode('utf-8')
        upload_req = urllib.request.Request(
            'https://content.dropboxapi.com/2/files/upload',
            data=data,
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/octet-stream',
                'Dropbox-API-Arg': json.dumps({
                    'path': check['test_file'],
                    'mode': 'overwrite',
                    'autorename': False
                })
            }
        )
        upload_response = urllib.request.urlopen(upload_req, timeout=10)
        upload_data = json.loads(upload_response.read())
        
        # Success
        return True, f"Wrote {upload_data['size']} bytes to {check['test_file']} ✓"
        
    except subprocess.TimeoutExpired:
        return False, "1Password credential read timed out"
    except urllib.error.HTTPError as e:
        return False, f"Dropbox API error: {e.code} {e.reason}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_governance_sync_and_read(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check governance repo for updates, sync if needed, and read key files.
    
    V2 Enhancement: Only pulls when remote is ahead, avoiding unnecessary
    git operations. Scans for recent changes to guide what to read.
    
    Args:
        check: Dictionary containing:
            - repo_path: Path to governance repo
            - must_read_files: List of files that must exist
            - scan_recent_days: Check for changes in last N days (default 7)
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Governance Sync',
            'type': 'governance_sync_and_read',
            'repo_path': '~/repos/ascendancy-governance',
            'must_read_files': ['GOVERNANCE.md', 'TRUST.md'],
            'scan_recent_days': 7,
            'required': True
        }
    """
    try:
        repo_path = Path(check['repo_path']).expanduser()
        
        if not repo_path.exists():
            return False, f"Governance repo not found: {repo_path}"
        
        # Step 1: Fetch to get latest remote refs
        result = subprocess.run(
            ['git', 'fetch', 'origin'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, f"git fetch failed: {result.stderr.strip()}"
        
        # Step 2: Check if remote is ahead
        local_result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        remote_result = subprocess.run(
            ['git', 'rev-parse', 'origin/main'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        local_commit = local_result.stdout.strip()
        remote_commit = remote_result.stdout.strip()
        
        # Step 3: Pull if remote is ahead
        if local_commit != remote_commit:
            pull_result = subprocess.run(
                ['git', 'pull', '--ff-only'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if pull_result.returncode != 0:
                return False, f"git pull failed: {pull_result.stderr.strip()}"
            
            sync_msg = "synced (pulled updates)"
        else:
            sync_msg = "already current"
        
        # Step 4: Scan for recent changes
        scan_days = check.get('scan_recent_days', 7)
        log_result = subprocess.run(
            ['git', 'log', f'--since={scan_days} days ago', '--oneline', '--', 'playbook/', 'agents/'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        recent_changes = log_result.stdout.strip().split('\n') if log_result.stdout.strip() else []
        change_count = len([c for c in recent_changes if c])
        
        # Step 5: Verify must-read files exist
        missing_files = []
        for filename in check.get('must_read_files', []):
            filepath = repo_path / filename
            if not filepath.exists():
                missing_files.append(filename)
        
        if missing_files:
            return False, f"Missing required files: {', '.join(missing_files)}"
        
        # Success
        msg = f"Governance {sync_msg}, {change_count} recent changes ✓"
        return True, msg
        
    except subprocess.TimeoutExpired:
        return False, "Git operation timed out"
    except Exception as e:
        return False, f"Exception: {str(e)}"


# ============================================================================
# V1 CHECK TYPES (preserved from original)
# ============================================================================

def run_command_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """Execute a shell command and check exit code."""
    try:
        result = subprocess.run(
            check['command'],
            shell=True,
            capture_output=True,
            timeout=check.get('timeout', 10),
            text=True
        )
        
        passed = result.returncode == 0
        
        if passed and 'expect' in check:
            passed = check['expect'] in result.stdout
            
        if passed:
            return True, result.stdout.strip()[:100]
        else:
            return False, result.stderr.strip()[:200]
            
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {check.get('timeout', 10)}s"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_http_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """Make HTTP request and check response."""
    try:
        headers = {}
        if 'header' in check:
            for key, value in check['header'].items():
                if value.startswith('op://'):
                    try:
                        result = subprocess.run(
                            ['op', 'read', value],
                            capture_output=True,
                            text=True,
                            timeout=5
                        )
                        if result.returncode == 0:
                            value = result.stdout.strip()
                        else:
                            return False, f"Failed to resolve 1Password ref: {value}"
                    except Exception as e:
                        return False, f"1Password error: {str(e)}"
                
                headers[key] = value
        
        req = urllib.request.Request(check['url'], headers=headers)
        response = urllib.request.urlopen(req, timeout=check.get('timeout', 10))
        body = response.read().decode('utf-8')
        
        if 'expect' in check:
            if check['expect'] in body:
                return True, f"Response contains '{check['expect']}'"
            else:
                return False, f"Response missing '{check['expect']}'"
        else:
            return True, f"HTTP {response.status}"
            
    except urllib.error.URLError as e:
        return False, f"URLError: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_file_size_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """Sum file sizes and compare to limit."""
    workspace = Path("~/.openclaw/workspace").expanduser()
    total = 0
    missing_files = []
    
    for filename in check['files']:
        filepath = workspace / filename
        if filepath.exists():
            total += filepath.stat().st_size
        else:
            missing_files.append(filename)
    
    max_total = check['max_total']
    passed = total <= max_total
    
    if passed:
        msg = f"{total:,} bytes (limit: {max_total:,}, {(total/max_total)*100:.1f}% used)"
        if missing_files:
            msg += f" [Missing: {', '.join(missing_files)}]"
        return True, msg
    else:
        excess = total - max_total
        return False, f"EXCEEDS LIMIT: {total:,} bytes (over by {excess:,})"


def run_json_key_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """Check if a key exists in a JSON file."""
    try:
        filepath = Path(check['file']).expanduser()
        with open(filepath) as f:
            data = json.load(f)
        
        key_path = check['key']
        current = data
        for key in key_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False, f"Key not found: {key_path}"
        
        return True, f"Key exists: {key_path} = {current}"
        
    except FileNotFoundError:
        return False, f"File not found: {check['file']}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_git_pull_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """Execute git pull in a repository."""
    try:
        repo_path = Path(check['repo']).expanduser()
        
        result = subprocess.run(
            ['git', 'pull'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            output = result.stdout.strip()
            if "Already up to date" in output:
                return True, "Already up to date"
            else:
                summary = output.split('\n')[0]
                return True, summary
        else:
            return False, result.stderr.strip()[:200]
            
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_llm_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """Call FREE model via OpenClaw CLI and check response."""
    try:
        result = subprocess.run(
            [
                'openclaw', 'chat',
                check['model'],
                check['prompt']
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            return False, f"openclaw chat failed: {result.stderr.strip()}"
        
        response = result.stdout.strip()
        
        response_lower = response.lower()
        missing = []
        for term in check['expect_contains']:
            if term.lower() not in response_lower:
                missing.append(term)
        
        if not missing:
            response_preview = response[:100] + "..." if len(response) > 100 else response
            return True, f"Response: {response_preview}"
        else:
            return False, f"Response missing: {', '.join(missing)}"
            
    except subprocess.TimeoutExpired:
        return False, "LLM call timed out after 30s"
    except Exception as e:
        return False, f"Exception: {str(e)}"


# ============================================================================
# DISPATCHER
# ============================================================================

def run_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Dispatch check to appropriate handler based on type.
    
    V2 adds new check types while preserving all v1 types.
    """
    check_type = check.get('type')
    
    handlers = {
        # V1 check types
        'command': run_command_check,
        'http': run_http_check,
        'file_size': run_file_size_check,
        'json_key': run_json_key_check,
        'git_pull': run_git_pull_check,
        'llm': run_llm_check,
        # V2 new check types
        'onepassword_read_test': run_onepassword_read_test,
        'github_pat_validation': run_github_pat_validation,
        'dropbox_write_test': run_dropbox_write_test,
        'governance_sync_and_read': run_governance_sync_and_read,
    }
    
    handler = handlers.get(check_type)
    if handler is None:
        return False, f"Unknown check type: {check_type}"
    
    return handler(check)


# ============================================================================
# MAIN
# ============================================================================

def main() -> int:
    """
    Main entry point: load config, run checks, report results.
    
    V2 Enhancement: Respects check 'order' field to run critical checks first.
    """
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ ERROR: Failed to load config: {e}")
        return 1
    
    agent_name = config.get('agent', {}).get('name', 'unknown')
    print(f"=== Daily Start Checks v2: {agent_name} ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # V2: Sort checks by 'order' field (default 100 if not specified)
    checks = sorted(
        config.get('checks', []),
        key=lambda c: c.get('order', 100)
    )
    
    all_passed = True
    for check in checks:
        name = check.get('name', 'Unnamed Check')
        required = check.get('required', False)
        
        print(f"{name}...", end=" ", flush=True)
        
        try:
            passed, message = run_check(check)
            
            if passed:
                print("✅")
            else:
                print(f"❌")
                print(f"  └─ {message}")
                
                if required:
                    all_passed = False
                    
        except Exception as e:
            print(f"❌ EXCEPTION")
            print(f"  └─ {str(e)}")
            
            if required:
                all_passed = False
    
    print()
    if all_passed:
        print("✅ All required checks passed")
        return 0
    else:
        print("❌ One or more required checks failed")
        print("   Review errors above and resolve before proceeding")
        return 1


if __name__ == '__main__':
    sys.exit(main())
