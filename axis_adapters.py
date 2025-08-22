#!/usr/bin/env python3
"""
AXIS-ADAPTERS: Monadic effects for JSON
Controlled side effects and external system integration

Pipeline: JSON → Effects → JSON + Side Effects
- Template-based command execution with security filters
- Safe parameter substitution with injection protection
- Command allowlist and resource limits
- Full audit trail of all effects

Usage:
    echo '{"user": "alice", "email": "alice@example.com"}' | python axis_adapters.py exec save.yaml
"""

import json
import sys
import argparse
import hashlib
import math
import subprocess
import os
import re
import shlex
import resource
from typing import Any, Dict, List, Union
from datetime import datetime

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# RFC 8785 COMPLIANT CANONICALIZATION (shared)
# ============================================================================

def canonicalize(obj: Any) -> Any:
    """RFC 8785 compliant JSON canonicalization"""
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        return [canonicalize(v) for v in obj]
    elif isinstance(obj, bool):
        return obj
    elif isinstance(obj, int):
        return obj
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Non-finite numbers not allowed")
        return obj
    elif obj is None:
        return obj
    else:
        return str(obj)

def payload_view(data: dict) -> dict:
    """Extract payload view (exclude audit keys starting with _)"""
    if isinstance(data, dict):
        return {k: payload_view(v) if isinstance(v, dict) else v
                for k, v in data.items() 
                if not (isinstance(k, str) and k.startswith("_"))}
    return data

def sha3_256_hex(s: str) -> str:
    """Content addressing with strict canonicalization"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

def compute_hash(obj: Any) -> str:
    """Compute canonical hash of object"""
    canonical = canonicalize(obj)
    json_str = json.dumps(canonical, sort_keys=True, separators=(',', ':'))
    return sha3_256_hex(json_str)

# ============================================================================
# SECURITY CONFIGURATION
# ============================================================================

# Default allowlist of safe commands
DEFAULT_COMMAND_ALLOWLIST = {
    'echo', 'cat', 'date', 'wc', 'head', 'tail', 'sort', 'uniq',
    'sqlite3', 'psql', 'mysql', 'curl', 'wget', 'mail', 'sendmail',
    'jq', 'grep', 'sed', 'awk', 'tr', 'cut', 'base64'
}

# Dangerous characters that require filtering
UNSAFE_CHARS = set(';&|`$(){}[]<>*?~')

# Template filters for safe substitution
TEMPLATE_FILTERS = {
    'json': lambda x: json.dumps(x, separators=(',', ':')),
    'sharg': lambda x: shlex.quote(str(x)),
    'sql': lambda x: str(x).replace("'", "''"),  # SQL single quote escape
    'url': lambda x: __import__('urllib.parse').quote(str(x)),
    'b64': lambda x: __import__('base64').b64encode(str(x).encode()).decode()
}

# ============================================================================
# SECURE TEMPLATE SUBSTITUTION
# ============================================================================

def secure_substitute(template: str, data: dict, command: str = '') -> str:
    """Secure template substitution with injection protection"""
    
    def replace_var(match):
        var_expr = match.group(1).strip()
        
        # Parse variable and optional filter: {{var|filter}}
        if '|' in var_expr:
            var_path, filter_name = var_expr.split('|', 1)
            var_path = var_path.strip()
            filter_name = filter_name.strip()
        else:
            var_path = var_expr
            filter_name = None
        
        # Resolve variable value
        parts = var_path.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return f"{{{{UNDEFINED:{var_path}}}}}"
        
        if value is None:
            return f"{{{{UNDEFINED:{var_path}}}}}"
        
        # Apply filter if specified
        if filter_name:
            if filter_name not in TEMPLATE_FILTERS:
                raise ValueError(f"Unknown template filter: {filter_name}")
            try:
                value = TEMPLATE_FILTERS[filter_name](value)
            except Exception as e:
                raise ValueError(f"Filter {filter_name} failed: {e}")
        else:
            # No filter - check for unsafe characters in sensitive commands
            str_value = str(value)
            if _is_sensitive_command(command) and any(c in str_value for c in UNSAFE_CHARS):
                raise ValueError(f"Unsafe characters in unfiltered substitution for {command}: {str_value}")
            value = str_value
        
        return str(value)
    
    return re.sub(r'\{\{([^}]+)\}\}', replace_var, template)

def _is_sensitive_command(command: str) -> bool:
    """Check if command is sensitive to injection"""
    sensitive_commands = {'sqlite3', 'psql', 'mysql', 'curl', 'sh', 'bash'}
    return command in sensitive_commands

# ============================================================================
# ADAPTER ENGINE (Monadic Effects)
# ============================================================================

class AdapterEngine:
    """Execute controlled side effects with security and audit trail"""
    
    def __init__(self, config: Union[dict, str], unsafe_mode: bool = False):
        if isinstance(config, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.adapters = self.config.get('adapters', [])
        self.command_allowlist = set(self.config.get('allowed_commands', DEFAULT_COMMAND_ALLOWLIST))
        self.unsafe_mode = unsafe_mode
        self.config_hash = compute_hash(self.config)
        self.execution_log = []
        
        # Validate adapters
        self._validate_adapters()
    
    def _validate_adapters(self):
        """Validate adapter configuration for security"""
        for i, adapter in enumerate(self.adapters):
            if not isinstance(adapter, dict):
                raise ValueError(f"Adapter {i}: must be a dict")
            
            if 'command' not in adapter:
                raise ValueError(f"Adapter {i}: missing 'command'")
            
            command = adapter['command']
            if not isinstance(command, str):
                raise ValueError(f"Adapter {i}: 'command' must be string")
            
            # Security checks
            if not self.unsafe_mode:
                # Check command allowlist
                if command not in self.command_allowlist:
                    raise ValueError(f"Adapter {i}: command '{command}' not in allowlist")
                
                # Reject absolute paths
                if command.startswith('/'):
                    raise ValueError(f"Adapter {i}: absolute paths not allowed: {command}")
                
                # Reject shell metacharacters in command
                if any(c in command for c in UNSAFE_CHARS):
                    raise ValueError(f"Adapter {i}: unsafe characters in command: {command}")
            
            # Validate args if present
            args = adapter.get('args', [])
            if not isinstance(args, list):
                raise ValueError(f"Adapter {i}: 'args' must be list")
            
            # Validate timeout if present
            timeout = adapter.get('timeout', 30)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValueError(f"Adapter {i}: 'timeout' must be positive number")
    
    def exec(self, input_data: dict) -> dict:
        """Execute all adapters with input data"""
        results = []
        
        for i, adapter in enumerate(self.adapters):
            try:
                result = self._execute_adapter(adapter, input_data, i)
                results.append(result)
            except Exception as e:
                error_result = {
                    'adapter_index': i,
                    'adapter_name': adapter.get('name', f'adapter_{i}'),
                    'status': 'error',
                    'error': str(e)
                }
                results.append(error_result)
                self.execution_log.append(error_result)
        
        # Add adapter audit
        audit = {
            'config_hash': self.config_hash,
            'input_hash': compute_hash(payload_view(input_data)),
            'adapters_executed': len(results),
            'execution_log': self.execution_log,
            'unsafe_mode': self.unsafe_mode,
            'version': 'axis-adapters@1.0.0'
        }
        
        return {
            'results': results,
            'input_data': input_data,
            '_adapter_audit': audit
        }
    
    def _execute_adapter(self, adapter: dict, data: dict, index: int) -> dict:
        """Execute a single adapter with security controls"""
        adapter_name = adapter.get('name', f'adapter_{index}')
        command = adapter['command']
        args = adapter.get('args', [])
        input_template = adapter.get('input', '')
        timeout = adapter.get('timeout', 30)
        cwd = adapter.get('cwd')
        env_allowlist = adapter.get('env_allowlist', [])
        
        # Substitute templates securely
        try:
            substituted_command = secure_substitute(command, data, command)
            substituted_args = [secure_substitute(arg, data, command) for arg in args]
            substituted_input = secure_substitute(input_template, data, command) if input_template else ''
        except Exception as e:
            raise ValueError(f"Template substitution failed: {e}")
        
        # Prepare environment (restrictive by default)
        env = {'PATH': os.environ.get('PATH', '/usr/bin:/bin')}
        for env_var in env_allowlist:
            if env_var in os.environ:
                env[env_var] = os.environ[env_var]
        
        # Log execution attempt
        log_entry = {
            'adapter_name': adapter_name,
            'command': substituted_command,
            'args': substituted_args,
            'input_length': len(substituted_input),
            'timestamp': datetime.now().isoformat(),
            'timeout': timeout
        }
        
        try:
            # Set resource limits (Linux/Unix only)
            def set_limits():
                try:
                    # CPU time limit (seconds)
                    resource.setrlimit(resource.RLIMIT_CPU, (timeout * 2, timeout * 2))
                    # Memory limit (256MB)
                    resource.setrlimit(resource.RLIMIT_AS, (256 * 1024 * 1024, 256 * 1024 * 1024))
                    # File size limit (100MB)
                    resource.setrlimit(resource.RLIMIT_FSIZE, (100 * 1024 * 1024, 100 * 1024 * 1024))
                    # Number of processes
                    resource.setrlimit(resource.RLIMIT_NPROC, (100, 100))
                except (ImportError, OSError):
                    # Resource limits not available on this platform
                    pass
            
            # Execute command
            cmd_args = [substituted_command] + substituted_args
            
            if substituted_input:
                result = subprocess.run(
                    cmd_args,
                    input=substituted_input,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    env=env,
                    cwd=cwd,
                    preexec_fn=set_limits if os.name != 'nt' else None
                )
            else:
                result = subprocess.run(
                    cmd_args,
                    text=True,
                    capture_output=True,
                    timeout=timeout,
                    env=env,
                    cwd=cwd,
                    preexec_fn=set_limits if os.name != 'nt' else None
                )
            
            # Process result
            log_entry.update({
                'status': 'success' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout_length': len(result.stdout),
                'stderr_length': len(result.stderr)
            })
            
            self.execution_log.append(log_entry)
            
            # Try to parse stdout as JSON, fallback to text
            try:
                stdout_data = json.loads(result.stdout) if result.stdout.strip() else {}
            except json.JSONDecodeError:
                stdout_data = {'output': result.stdout}
            
            return {
                'adapter_name': adapter_name,
                'status': 'success' if result.returncode == 0 else 'failed',
                'return_code': result.returncode,
                'stdout': stdout_data,
                'stderr': result.stderr,
                'command_executed': f"{substituted_command} {' '.join(substituted_args)}"
            }
            
        except subprocess.TimeoutExpired:
            log_entry.update({'status': 'timeout'})
            self.execution_log.append(log_entry)
            raise ValueError(f"Adapter {adapter_name}: command timed out after {timeout}s")
        
        except FileNotFoundError:
            log_entry.update({'status': 'not_found'})
            self.execution_log.append(log_entry)
            raise ValueError(f"Adapter {adapter_name}: command not found: {substituted_command}")
        
        except PermissionError:
            log_entry.update({'status': 'permission_denied'})
            self.execution_log.append(log_entry)
            raise ValueError(f"Adapter {adapter_name}: permission denied: {substituted_command}")

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for AXIS-ADAPTERS"""
    parser = argparse.ArgumentParser(description="AXIS-ADAPTERS: Controlled side effects")
    parser.add_argument("command", choices=['exec', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("config", help="Adapter configuration file")
    parser.add_argument("--input", help="Input JSON file (use '-' for stdin)")
    parser.add_argument("--output", help="Output file (use '-' for stdout)")
    parser.add_argument("--dry-run", action='store_true', help="Show what would be executed without running")
    parser.add_argument("--unsafe", action='store_true', help="Disable security restrictions (dangerous)")
    parser.add_argument("--strict", action='store_true', help="Strict validation mode")
    parser.add_argument("--quiet", "-q", action='store_true', help="Suppress non-essential output")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'exec':
            # Load input data
            if args.input == '-' or args.input is None:
                input_data = json.load(sys.stdin)
            else:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            
            # Execute adapters
            engine = AdapterEngine(args.config, unsafe_mode=args.unsafe)
            
            if args.dry_run:
                # Show what would be executed
                if not args.quiet:
                    print("🔍 DRY RUN - Commands that would be executed:")
                for i, adapter in enumerate(engine.adapters):
                    name = adapter.get('name', f'adapter_{i}')
                    try:
                        command = secure_substitute(adapter.get('command', ''), input_data, adapter.get('command', ''))
                        args_list = [secure_substitute(arg, input_data, adapter.get('command', '')) 
                                   for arg in adapter.get('args', [])]
                        if not args.quiet:
                            print(f"  {name}: {command} {' '.join(args_list)}")
                    except Exception as e:
                        if not args.quiet:
                            print(f"  {name}: ERROR - {e}")
                return
            
            result = engine.exec(input_data)
            
            # Check for failures in strict mode
            if args.strict:
                failed_adapters = [r for r in result['results'] if r['status'] != 'success']
                if failed_adapters:
                    print(f"Adapters failed: {[a['adapter_name'] for a in failed_adapters]}", file=sys.stderr)
                    sys.exit(1)
            
            # Output result
            output = json.dumps(result, indent=None if args.quiet else 2, separators=(',', ':'))
            if args.output == '-' or args.output is None:
                print(output)
            else:
                with open(args.output, 'w') as f:
                    f.write(output)
        
        elif args.command == 'validate':
            engine = AdapterEngine(args.config, unsafe_mode=args.unsafe)
            if not args.quiet:
                print(f"✅ Adapters valid")
                print(f"✅ Adapter count: {len(engine.adapters)}")
                print(f"✅ Config Hash: {engine.config_hash}")
                print(f"✅ Security mode: {'UNSAFE' if args.unsafe else 'SAFE'}")
        
        elif args.command == 'hash':
            engine = AdapterEngine(args.config, unsafe_mode=args.unsafe)
            print(engine.config_hash)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli()
