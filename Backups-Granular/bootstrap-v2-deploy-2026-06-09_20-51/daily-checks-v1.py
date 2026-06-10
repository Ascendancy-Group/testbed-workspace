#!/usr/bin/env python3
"""
Daily Start Checks for OpenClaw Agents
======================================

Purpose:
    Execute daily startup checks to ensure agent infrastructure is healthy
    before beginning work. All checks use FREE models or zero-cost commands.

Author: Testbed
Created: 2026-05-26
Cost: $0.00/day per agent

Usage:
    python3 ~/scripts/daily-checks.py

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
        print(f"Create it by copying daily-checks.yaml template")
        sys.exit(1)
    
    with open(config_path) as f:
        return yaml.safe_load(f)


def run_command_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Execute a shell command and check exit code.
    
    Args:
        check: Dictionary containing:
            - command: Shell command to execute
            - timeout: Optional timeout in seconds (default 10)
            - expect: Optional string to search for in stdout
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'GitHub Access',
            'type': 'command',
            'command': 'gh auth status',
            'timeout': 5,
            'required': True
        }
    """
    try:
        # Execute command with timeout
        result = subprocess.run(
            check['command'],
            shell=True,
            capture_output=True,
            timeout=check.get('timeout', 10),
            text=True
        )
        
        # Check exit code first
        passed = result.returncode == 0
        
        # If 'expect' is specified, also check stdout contains it
        if passed and 'expect' in check:
            passed = check['expect'] in result.stdout
            
        # Return result with appropriate output
        if passed:
            return True, result.stdout.strip()[:100]  # Truncate long output
        else:
            return False, result.stderr.strip()[:200]
            
    except subprocess.TimeoutExpired:
        return False, f"Command timed out after {check.get('timeout', 10)}s"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_http_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Make HTTP request and check response.
    
    Args:
        check: Dictionary containing:
            - url: HTTP(S) URL to request
            - header: Optional dict of headers to send
            - expect: String to search for in response body
            - timeout: Optional timeout in seconds (default 5)
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Dropbox MCP',
            'type': 'http',
            'url': 'http://100.77.0.47:3001/sse',
            'header': {
                'x-api-key': 'op://AgentStack/Ascendancy MCP API Key/credential'
            },
            'expect': 'endpoint',
            'timeout': 5
        }
        
    Note:
        If header value starts with 'op://', it will be resolved via 1Password CLI
    """
    try:
        # Build headers, resolving 1Password references
        headers = {}
        if 'header' in check:
            for key, value in check['header'].items():
                # If value is a 1Password reference, resolve it
                if value.startswith('op://'):
                    try:
                        # Use 'op read' to get secret
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
        
        # Make HTTP request
        req = urllib.request.Request(check['url'], headers=headers)
        response = urllib.request.urlopen(req, timeout=check.get('timeout', 10))
        body = response.read().decode('utf-8')
        
        # Check if expected string is in response
        if 'expect' in check:
            if check['expect'] in body:
                return True, f"Response contains '{check['expect']}'"
            else:
                return False, f"Response missing '{check['expect']}'"
        else:
            # No expectation specified, just check 200 OK
            return True, f"HTTP {response.status}"
            
    except urllib.error.URLError as e:
        return False, f"URLError: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_file_size_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Sum file sizes and compare to limit.
    
    Args:
        check: Dictionary containing:
            - files: List of file paths (relative to agent workspace)
            - max_total: Maximum total size in bytes
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Bootstrap Size',
            'type': 'file_size',
            'files': ['SOUL.md', 'AGENTS.md', 'MEMORY.md', ...],
            'max_total': 60000
        }
        
    Note:
        Relative paths are resolved against ~/.openclaw/workspace
    """
    workspace = Path("~/.openclaw/workspace").expanduser()
    total = 0
    missing_files = []
    
    # Sum sizes of all files
    for filename in check['files']:
        filepath = workspace / filename
        if filepath.exists():
            total += filepath.stat().st_size
        else:
            missing_files.append(filename)
    
    # Check if total exceeds limit
    max_total = check['max_total']
    passed = total <= max_total
    
    # Build message
    if passed:
        msg = f"{total:,} bytes (limit: {max_total:,}, {(total/max_total)*100:.1f}% used)"
        if missing_files:
            msg += f" [Missing: {', '.join(missing_files)}]"
        return True, msg
    else:
        excess = total - max_total
        return False, f"EXCEEDS LIMIT: {total:,} bytes (over by {excess:,})"


def run_json_key_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Check if a key exists in a JSON file.
    
    Args:
        check: Dictionary containing:
            - file: Path to JSON file
            - key: Dotted path to key (e.g., "agents.defaults.bootstrapMaxChars")
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Config Limits Present',
            'type': 'json_key',
            'file': '~/.openclaw/openclaw.json',
            'key': 'agents.defaults.bootstrapMaxChars'
        }
    """
    try:
        # Load JSON file
        filepath = Path(check['file']).expanduser()
        with open(filepath) as f:
            data = json.load(f)
        
        # Navigate nested keys
        key_path = check['key']
        current = data
        for key in key_path.split('.'):
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return False, f"Key not found: {key_path}"
        
        # Key exists, return value for verification
        return True, f"Key exists: {key_path} = {current}"
        
    except FileNotFoundError:
        return False, f"File not found: {check['file']}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {str(e)}"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_git_pull_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Execute git pull in a repository.
    
    Args:
        check: Dictionary containing:
            - repo: Path to git repository
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Governance Sync',
            'type': 'git_pull',
            'repo': '~/repos/ascendancy-governance'
        }
    """
    try:
        repo_path = Path(check['repo']).expanduser()
        
        # Execute git pull
        result = subprocess.run(
            ['git', 'pull'],
            cwd=repo_path,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Extract summary from output
            output = result.stdout.strip()
            if "Already up to date" in output:
                return True, "Already up to date"
            else:
                # Get first line of output (usually summary)
                summary = output.split('\n')[0]
                return True, summary
        else:
            return False, result.stderr.strip()[:200]
            
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_llm_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Call FREE model via OpenClaw CLI and check response.
    
    Args:
        check: Dictionary containing:
            - model: Model identifier (must be FREE)
            - prompt: Prompt to send
            - expect_contains: List of strings that must appear in response
            
    Returns:
        Tuple of (passed: bool, message: str)
        
    Example check:
        {
            'name': 'Personality Self-Test',
            'type': 'llm',
            'model': 'meta-llama/llama-3.3-70b-instruct:free',
            'prompt': 'Who are you? What is your purpose?',
            'expect_contains': ['testbed', 'infrastructure', 'testing']
        }
        
    Note:
        This is the ONLY check that uses AI. Uses FREE model to ensure $0 cost.
    """
    try:
        # Call openclaw chat command
        # Syntax: openclaw chat <model> <message>
        result = subprocess.run(
            [
                'openclaw', 'chat',
                check['model'],
                check['prompt']
            ],
            capture_output=True,
            text=True,
            timeout=30  # LLM calls can take longer
        )
        
        if result.returncode != 0:
            return False, f"openclaw chat failed: {result.stderr.strip()}"
        
        response = result.stdout.strip()
        
        # Check if all expected strings are present (case-insensitive)
        response_lower = response.lower()
        missing = []
        for term in check['expect_contains']:
            if term.lower() not in response_lower:
                missing.append(term)
        
        if not missing:
            # Truncate response for readability
            response_preview = response[:100] + "..." if len(response) > 100 else response
            return True, f"Response: {response_preview}"
        else:
            return False, f"Response missing: {', '.join(missing)}"
            
    except subprocess.TimeoutExpired:
        return False, "LLM call timed out after 30s"
    except Exception as e:
        return False, f"Exception: {str(e)}"


def run_check(check: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Dispatch check to appropriate handler based on type.
    
    Args:
        check: Dictionary containing 'type' key
        
    Returns:
        Tuple of (passed: bool, message: str)
        
    Raises:
        ValueError: If check type is unknown
    """
    check_type = check.get('type')
    
    # Dispatch to appropriate handler
    handlers = {
        'command': run_command_check,
        'http': run_http_check,
        'file_size': run_file_size_check,
        'json_key': run_json_key_check,
        'git_pull': run_git_pull_check,
        'llm': run_llm_check,
    }
    
    handler = handlers.get(check_type)
    if handler is None:
        return False, f"Unknown check type: {check_type}"
    
    return handler(check)


def main() -> int:
    """
    Main entry point: load config, run checks, report results.
    
    Returns:
        0 if all required checks passed, 1 otherwise
    """
    # Load configuration
    try:
        config = load_config()
    except Exception as e:
        print(f"❌ ERROR: Failed to load config: {e}")
        return 1
    
    # Print header
    agent_name = config.get('agent', {}).get('name', 'unknown')
    print(f"=== Daily Start Checks: {agent_name} ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Run each check
    all_passed = True
    for check in config.get('checks', []):
        name = check.get('name', 'Unnamed Check')
        required = check.get('required', False)
        
        # Print check name (without newline)
        print(f"{name}...", end=" ", flush=True)
        
        try:
            # Run the check
            passed, message = run_check(check)
            
            if passed:
                # Check passed
                print("✅")
            else:
                # Check failed
                print(f"❌")
                print(f"  └─ {message}")
                
                # If required check failed, mark overall failure
                if required:
                    all_passed = False
                    
        except Exception as e:
            # Unexpected error during check execution
            print(f"❌ EXCEPTION")
            print(f"  └─ {str(e)}")
            
            if required:
                all_passed = False
    
    # Print summary
    print()
    if all_passed:
        print("✅ All required checks passed")
        return 0
    else:
        print("❌ One or more required checks failed")
        print("   Review errors above and resolve before proceeding")
        return 1


# Entry point
if __name__ == '__main__':
    sys.exit(main())
