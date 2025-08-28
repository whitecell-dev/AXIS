#!/usr/bin/env python3
"""
AXIS-ADAPTERS: Monadic effects for JSON
Controlled side effects and external system integration

Pipeline: JSON → Effects → JSON + Side Effects
- Template-based command execution
- Safe parameter substitution
- Audit trail of all effects
- Unix tool integration

Usage:
    echo '{"user": "alice", "email": "alice@example.com"}' | python axis_adapters.py exec save.yaml
"""

import json
import sys
import argparse
import hashlib
import math
import subprocess
import tempfile
import os
import re
from typing import Any, Dict, List, Union

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# CANONICALIZATION & HASHING (from AXIS core)
# ============================================================================

def canonicalize(obj: Any) -> Any:
    """Cross-target deterministic canonicalization"""
    if isinstance(obj, dict):
        return {k: canonicalize(obj[k]) for k in sorted(obj.keys())}
    elif isinstance(obj, list):
        return [canonicalize(v) for v in obj]
    elif isinstance(obj, (int, float)):
        f = float(obj)
        if not math.isfinite(f):
            raise ValueError("Non-finite numbers not allowed")
        return f
    else:
        return obj

def sha3_256_hex(s: str) -> str:
    """Content addressing for adapter verification"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

# ============================================================================
# TEMPLATE SUBSTITUTION
# ============================================================================

def safe_substitute(template: str, data: dict) -> str:
    """Safely substitute template variables with data"""
    def replace_var(match):
        var_name = match.group(1)
        
        # Handle nested access like user.email
        if '.' in var_name:
            parts = var_name.split('.')
            value = data
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return f"{{{{UNDEFINED:{var_name}}}}}"
        else:
            value = data.get(var_name)
        
        if value is None:
            return f"{{{{UNDEFINED:{var_name}}}}}"
        
        # Handle different types
        if isinstance(value, (dict, list)):
            return json.dumps(value)
        else:
            return str(value)
    
    # Replace {{variable}} patterns
    return re.sub(r'\{\{([^}]+)\}\}', replace_var, template)

# ============================================================================
# ADAPTER ENGINE (Monadic Effects)
# ============================================================================

class AdapterEngine:
    """Execute controlled side effects with audit trail"""
    
    def __init__(self, config: Union[dict, str]):
        if isinstance(config, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.adapters = self.config.get('adapters', [])
        self.config_hash = self._generate_config_hash()
        self.execution_log = []
    
    def _generate_config_hash(self) -> str:
        """Generate hash of adapter configuration"""
        canonical_config = canonicalize(self.config)
        config_json = json.dumps(canonical_config, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(config_json)
    
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
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'adapters_executed': len(results),
            'execution_log': self.execution_log
        }
        
        return {
            'results': results,
            'input_data': input_data,
            '_adapter_audit': audit
        }
    
    def _execute_adapter(self, adapter: dict, data: dict, index: int) -> dict:
        """Execute a single adapter"""
        adapter_name = adapter.get('name', f'adapter_{index}')
        command = adapter.get('command')
        args = adapter.get('args', [])
        input_template = adapter.get('input', '')
        
        if not command:
            raise ValueError(f"Adapter {adapter_name}: missing 'command'")
        
        # Substitute templates
        substituted_command = safe_substitute(command, data)
        substituted_args = [safe_substitute(arg, data) for arg in args]
        substituted_input = safe_substitute(input_template, data)
        
        # Log execution attempt
        log_entry = {
            'adapter_name': adapter_name,
            'command': substituted_command,
            'args': substituted_args,
            'input_length': len(substituted_input),
            'timestamp': self._get_timestamp()
        }
        
        try:
            # Execute command
            if substituted_input:
                # Command expects stdin
                result = subprocess.run(
                    [substituted_command] + substituted_args,
                    input=substituted_input,
                    text=True,
                    capture_output=True,
                    timeout=30  # 30 second timeout
                )
            else:
                # Command with no stdin
                result = subprocess.run(
                    [substituted_command] + substituted_args,
                    text=True,
                    capture_output=True,
                    timeout=30
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
            raise ValueError(f"Adapter {adapter_name}: command timed out")
        
        except FileNotFoundError:
            log_entry.update({'status': 'not_found'})
            self.execution_log.append(log_entry)
            raise ValueError(f"Adapter {adapter_name}: command not found: {substituted_command}")
    
    def _get_timestamp(self):
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for AXIS-ADAPTERS"""
    parser = argparse.ArgumentParser(description="AXIS-ADAPTERS: Controlled side effects")
    parser.add_argument("command", choices=['exec', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("config", help="Adapter configuration file")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--dry-run", action='store_true', help="Show what would be executed without running")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'exec':
            # Load input data
            if args.input:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = json.load(sys.stdin)
            
            # Execute adapters
            engine = AdapterEngine(args.config)
            
            if args.dry_run:
                # Show what would be executed
                print("🔍 DRY RUN - Commands that would be executed:")
                for i, adapter in enumerate(engine.adapters):
                    name = adapter.get('name', f'adapter_{i}')
                    command = safe_substitute(adapter.get('command', ''), input_data)
                    args_list = [safe_substitute(arg, input_data) for arg in adapter.get('args', [])]
                    print(f"  {name}: {command} {' '.join(args_list)}")
                return
            
            result = engine.exec(input_data)
            
            # Output result
            output = json.dumps(result, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
        
        elif args.command == 'validate':
            engine = AdapterEngine(args.config)
            print(f"✓ Adapters valid")
            print(f"✓ Adapter count: {len(engine.adapters)}")
            print(f"✓ Config Hash: {engine.config_hash}")
        
        elif args.command == 'hash':
            engine = AdapterEngine(args.config)
            print(engine.config_hash)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# ============================================================================
# DEMO & EXAMPLES
# ============================================================================

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        print("🔌 AXIS-ADAPTERS: Monadic effects for JSON")
        print("Controlled side effects and external system integration\n")
        
        # Demo adapters
        sample_data = {"user": "alice", "email": "alice@example.com", "status": "active"}
        sample_config = {
            "adapters": [
                {
                    "name": "log_user",
                    "command": "echo",
                    "args": ["User {{user}} ({{email}}) is {{status}}"]
                },
                {
                    "name": "save_json",
                    "command": "cat",
                    "input": "{{input_data|tojson}}"
                },
                {
                    "name": "timestamp",
                    "command": "date",
                    "args": ["+%Y-%m-%d %H:%M:%S"]
                }
            ]
        }
        
        engine = AdapterEngine(sample_config)
        
        print(f"Input:  {sample_data}")
        print(f"Config: {len(engine.adapters)} adapters")
        print(f"Hash:   {engine.config_hash[:16]}...")
        
        print(f"\nDry run:")
        for i, adapter in enumerate(engine.adapters):
            name = adapter.get('name', f'adapter_{i}')
            command = safe_substitute(adapter.get('command', ''), sample_data)
            args_list = [safe_substitute(arg, sample_data) for arg in adapter.get('args', [])]
            print(f"  {name}: {command} {' '.join(args_list)}")
        
        print(f"\nUsage:")
        print(f"  echo '{json.dumps(sample_data)}' | python axis_adapters.py exec config.yaml")
        print(f"  python axis_adapters.py validate config.yaml")
        print(f"  python axis_adapters.py hash config.yaml")
        print(f"  python axis_adapters.py exec config.yaml --dry-run")
