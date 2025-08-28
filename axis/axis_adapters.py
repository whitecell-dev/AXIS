#!/usr/bin/env python3
"""
AXIS-ADAPTERS: Monadic effects for JSON + Relational Algebra + Structure Registry
Controlled side effects and external system integration with RA filtering and prebuilt structures

Pipeline: JSON → Effects → JSON + Side Effects (+ RA pre/post filtering + O(1) structure operations)
- Template-based command execution
- Safe parameter substitution
- Audit trail of all effects
- Unix tool integration
- NEW: σ (select), π (project) for pre/post filtering
- NEW: Structure registry integration for fast filtering
- NEW: exists_in/not_exists_in for semi/anti-joins
- RA operations can filter inputs or transform outputs

Usage:
    echo '{"user": "alice", "email": "alice@example.com"}' | python axis_adapters.py exec save.yaml
"""

import json
import sys
import argparse
import subprocess
import os
import re
from typing import Any, Dict, List, Union

# Import shared core functionality
try:
    from .axis_core import canonicalize, sha3_256_hex, uses_structure
    HAS_CORE = True
except ImportError:
    print("Warning: axis_core.py not found. Using local implementations.", file=sys.stderr)
    HAS_CORE = False

# Import RA primitives
try:
    from .axis_ra import apply_ra_operation, is_ra_operation, extract_ra_operations, apply_ra_pipeline, generate_ra_audit
    HAS_RA = True
except ImportError:
    print("Warning: axis_ra.py not found. RA operations disabled.", file=sys.stderr)
    HAS_RA = False

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# FALLBACK IMPLEMENTATIONS (if axis_core.py unavailable)
# ============================================================================

if not HAS_CORE:
    import hashlib
    import math
    
    def canonicalize(obj: Any) -> Any:
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
        return hashlib.sha3_256(s.encode("utf-8")).hexdigest()
    
    def uses_structure(config: dict) -> bool:
        if 'join' in config and 'using' in config['join']:
            return True
        if 'difference' in config and 'using' in config['difference']:
            return True
        if 'union' in config and 'using' in config['union']:
            return True
        if 'exists_in' in config and 'using' in config['exists_in']:
            return True
        if 'not_exists_in' in config and 'using' in config['not_exists_in']:
            return True
        return False

# ============================================================================
# STRUCTURE REGISTRY INTEGRATION HELPERS
# ============================================================================

def _apply_structure_enhanced_ra(data, config, registry, structures_used_log):
    """Apply RA operation using structure registry"""
    
    if 'join' in config and 'using' in config['join']:
        # Enhanced join
        try:
            from .axis_structures import enhanced_join_with_structure
            result = enhanced_join_with_structure(data, config['join'], registry)
            structures_used_log.append(config['join']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'difference' in config and 'using' in config['difference']:
        # Enhanced difference
        try:
            from .axis_structures import enhanced_difference_with_structure
            result = enhanced_difference_with_structure(data, config['difference'], registry)
            structures_used_log.append(config['difference']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'exists_in' in config:
        # NEW: Semi-join operation
        try:
            from .axis_structures import enhanced_exists_in_with_structure
            result = enhanced_exists_in_with_structure(data, config['exists_in'], registry)
            if 'using' in config['exists_in']:
                structures_used_log.append(config['exists_in']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'not_exists_in' in config:
        # NEW: Anti-join operation
        try:
            from .axis_structures import enhanced_not_exists_in_with_structure
            result = enhanced_not_exists_in_with_structure(data, config['not_exists_in'], registry)
            if 'using' in config['not_exists_in']:
                structures_used_log.append(config['not_exists_in']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    else:
        # Fallback to standard RA
        return apply_ra_operation(data, config)

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
# ENHANCED ADAPTER ENGINE (Monadic Effects + RA + Structures)
# ============================================================================

class AdapterEngine:
    """Execute controlled side effects with RA filtering and structure registry support"""
    
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
        
        # Structure registry integration  
        self.registry = None
        if 'structures' in self.config:
            try:
                from .axis_structures import StructureRegistry
                self.registry = StructureRegistry(self.config)
            except ImportError:
                pass
    
    def _generate_config_hash(self) -> str:
        """Generate hash of adapter configuration"""
        canonical_config = canonicalize(self.config)
        config_json = json.dumps(canonical_config, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(config_json)
    
    def exec(self, input_data: dict) -> dict:
        """Execute all adapters with RA pre/post filtering and structure support"""
        results = []
        ra_operations_applied = []
        structures_used = []
        
        for i, adapter in enumerate(self.adapters):
            try:
                result = self._execute_adapter(adapter, input_data, i, structures_used)
                results.append(result)
                
                # Track RA operations if any were applied
                if 'ra_operations' in result:
                    ra_operations_applied.extend(result['ra_operations'])
                    
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
        
        # Add structure registry audit
        if self.registry:
            try:
                from .axis_structures import get_structure_audit_info
                structure_audit = get_structure_audit_info(self.registry)
                audit['structure_registry'] = structure_audit
                audit['structures_used'] = structures_used
            except ImportError:
                pass
        
        # Add RA audit if operations were applied
        if HAS_RA and ra_operations_applied:
            ra_audit = generate_ra_audit(input_data, ra_operations_applied, results)
            audit['ra_audit'] = ra_audit
        
        return {
            'results': results,
            'input_data': input_data,
            '_adapter_audit': audit
        }
    
    def _execute_adapter(self, adapter: dict, data: dict, index: int, structures_used_log: List[str]) -> dict:
        """Execute a single adapter with optional RA and structure filtering"""
        adapter_name = adapter.get('name', f'adapter_{index}')
        command = adapter.get('command')
        args = adapter.get('args', [])
        input_template = adapter.get('input', '')
        
        # Check for RA pre-filtering with structure registry support
        filtered_data = data
        ra_operations = []
        
        if HAS_RA:
            # Enhanced adapter filtering with structure registry
            if self.registry and uses_structure(adapter):
                filtered_data = _apply_structure_enhanced_ra(filtered_data, adapter, self.registry, structures_used_log)
                ra_operations.append({'structure_enhanced': True})
            else:
                # Standard RA filtering - support select as alias for filter
                if 'filter' in adapter or 'select' in adapter:  
                    predicate = adapter.get('filter', adapter.get('select'))
                    filter_op = {'select': predicate}
                    filtered_data = apply_ra_operation(filtered_data, filter_op)
                    ra_operations.append(filter_op)
                
                if 'project' in adapter:  # π operation
                    project_op = {'project': adapter['project']}
                    filtered_data = apply_ra_operation(filtered_data, project_op)
                    ra_operations.append(project_op)
        
        # Check if adapter should execute based on filtering
        if isinstance(filtered_data, list) and len(filtered_data) == 0:
            return {
                'adapter_name': adapter_name,
                'status': 'skipped',
                'reason': 'filtered_out',
                'ra_operations': ra_operations,
                'command_executed': 'none'
            }
        
        if isinstance(filtered_data, dict) and len(filtered_data) == 0:
            return {
                'adapter_name': adapter_name,
                'status': 'skipped', 
                'reason': 'filtered_out',
                'ra_operations': ra_operations,
                'command_executed': 'none'
            }
        
        if not command:
            raise ValueError(f"Adapter {adapter_name}: missing 'command'")
        
        # Use filtered data for template substitution
        substituted_command = safe_substitute(command, filtered_data)
        substituted_args = [safe_substitute(arg, filtered_data) for arg in args]
        substituted_input = safe_substitute(input_template, filtered_data)
        
        # Log execution attempt
        log_entry = {
            'adapter_name': adapter_name,
            'command': substituted_command,
            'args': substituted_args,
            'input_length': len(substituted_input),
            'ra_operations': ra_operations,
            'timestamp': self._get_timestamp()
        }
        
        try:
            # Execute command (prefer array form for security)
            cmd_array = [substituted_command] + substituted_args
            
            if substituted_input:
                result = subprocess.run(
                    cmd_array,
                    input=substituted_input,
                    text=True,
                    capture_output=True,
                    timeout=30,
                    shell=False  # Safer execution
                )
            else:
                result = subprocess.run(
                    cmd_array,
                    text=True,
                    capture_output=True,
                    timeout=30,
                    shell=False
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
                'ra_operations': ra_operations,
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
# CLI INTERFACE (FIXED)
# ============================================================================

def cli():
    """CLI for AXIS-ADAPTERS"""
    parser = argparse.ArgumentParser(description="AXIS-ADAPTERS: Controlled side effects + RA operations + Structure Registry")
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
                print("DRY RUN - Commands that would be executed:")
                for i, adapter in enumerate(engine.adapters):
                    name = adapter.get('name', f'adapter_{i}')
                    command = safe_substitute(adapter.get('command', ''), input_data)
                    args_list = [safe_substitute(arg, input_data) for arg in adapter.get('args', [])]
                    
                    # Show RA filtering info and structure usage
                    if HAS_RA:
                        ra_filters = []
                        if 'filter' in adapter or 'select' in adapter:
                            predicate = adapter.get('filter', adapter.get('select'))
                            ra_filters.append(f"filter: {predicate}")
                        if 'project' in adapter:
                            ra_filters.append(f"project: {adapter['project']}")
                        if 'join' in adapter and 'using' in adapter['join']:
                            ra_filters.append(f"join using {adapter['join']['using']}")
                        if 'exists_in' in adapter and 'using' in adapter['exists_in']:
                            ra_filters.append(f"exists_in using {adapter['exists_in']['using']}")
                        if 'not_exists_in' in adapter and 'using' in adapter['not_exists_in']:
                            ra_filters.append(f"not_exists_in using {adapter['not_exists_in']['using']}")
                        
                        if ra_filters:
                            print(f"  {name}: [{', '.join(ra_filters)}] → {command} {' '.join(args_list)}")
                        else:
                            print(f"  {name}: {command} {' '.join(args_list)}")
                    else:
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
            print(f"Adapters valid")
            print(f"Adapter count: {len(engine.adapters)}")
            if engine.registry:
                print(f"Structures: {len(engine.registry.list_structures())}")
            print(f"Config Hash: {engine.config_hash}")
        
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
        print("AXIS-ADAPTERS: Monadic effects for JSON + Relational Algebra + Structure Registry")
        print("Controlled side effects with RA filtering and prebuilt structures\n")
        
        # Demo adapters with RA filtering and structures including new operations
        sample_data = [
            {"user": "alice", "email": "alice@example.com", "role": "admin", "active": True, "dept_id": "eng"},
            {"user": "bob", "email": "bob@example.com", "role": "user", "active": False, "dept_id": "sales"},
            {"user": "charlie", "email": "charlie@example.com", "role": "admin", "active": True, "dept_id": "eng"}
        ]
        
        sample_config = {
            "structures": {
                "admin_whitelist": {
                    "type": "set",
                    "materialize": "from_data", 
                    "data": [
                        {"user": "alice", "approved": True},
                        {"user": "charlie", "approved": True}
                    ]
                },
                "departments": {
                    "type": "hashmap",
                    "key": "dept_id",
                    "materialize": "from_data",
                    "data": [
                        {"dept_id": "eng", "dept_name": "Engineering", "alert_channel": "#eng-alerts"},
                        {"dept_id": "sales", "dept_name": "Sales", "alert_channel": "#sales-alerts"}
                    ]
                },
                "blocked_users": {
                    "type": "set",
                    "materialize": "from_data",
                    "data": [
                        {"user": "blocked1"},
                        {"user": "blocked2"}
                    ]
                }
            },
            "adapters": [
                {
                    "name": "log_active_users",
                    "select": "active == True",  # RA: Only process active users
                    "command": "echo",
                    "args": ["Active user: {{user}} ({{email}})"]
                },
                {
                    "name": "notify_approved_admins",
                    "select": "role == 'admin'",  # RA: Only admins
                    "exists_in": {                # NEW: Semi-join with whitelist
                        "field": "user", 
                        "using": "admin_whitelist"
                    },
                    "join": {                     # RA: Join with dept structure
                        "on": "dept_id",
                        "using": "departments"
                    },
                    "project": ["left_user", "left_email", "right_alert_channel"],
                    "command": "echo", 
                    "args": ["Admin alert to {{right_alert_channel}}: {{left_user}} at {{left_email}}"]
                },
                {
                    "name": "save_non_blocked_users",
                    "not_exists_in": {           # NEW: Anti-join to exclude blocked users
                        "field": "user",
                        "using": "blocked_users"
                    },
                    "command": "echo",
                    "args": ["Saving non-blocked user: {{user}}"],
                    "input": "{{input_data}}"
                }
            ]
        }
        
        engine = AdapterEngine(sample_config)
        
        print(f"Input:  {json.dumps(sample_data, indent=2)}")
        print(f"Config: {len(engine.adapters)} adapters (with RA filtering + structures)")
        if engine.registry:
            print(f"Structures: {len(engine.registry.list_structures())} materialized")
        print(f"Hash:   {engine.config_hash[:16]}...")
        
        print(f"\nDry run (showing RA filtering + structure usage including new ops):")
        for i, adapter in enumerate(engine.adapters):
            name = adapter.get('name', f'adapter_{i}')
            command = safe_substitute(adapter.get('command', ''), sample_data[0] if sample_data else {})
            args_list = [safe_substitute(arg, sample_data[0] if sample_data else {}) for arg in adapter.get('args', [])]
            
            # Show RA filtering and structure usage including new operations
            if HAS_RA:
                ra_filters = []
                if 'filter' in adapter or 'select' in adapter:
                    predicate = adapter.get('filter', adapter.get('select'))
                    ra_filters.append(f"select: {predicate}")
                if 'project' in adapter:
                    ra_filters.append(f"project: {adapter['project']}")
                if 'join' in adapter and 'using' in adapter['join']:
                    ra_filters.append(f"join using {adapter['join']['using']}")
                if 'exists_in' in adapter and 'using' in adapter['exists_in']:
                    ra_filters.append(f"exists_in using {adapter['exists_in']['using']}")
                if 'not_exists_in' in adapter and 'using' in adapter['not_exists_in']:
                    ra_filters.append(f"not_exists_in using {adapter['not_exists_in']['using']}")
                
                if ra_filters:
                    print(f"  {name}: [{', '.join(ra_filters)}] → {command} {' '.join(args_list)}")
                else:
                    print(f"  {name}: {command} {' '.join(args_list)}")
            else:
                print(f"  {name}: {command} {' '.join(args_list)}")
        
        print(f"\nNew RA Operations Demonstrated:")
        print(f"  exists_in: Semi-join to filter by set membership")
        print(f"  not_exists_in: Anti-join to exclude set members")
        print(f"  Unified filter/select: Both keywords work identically")
        
        print(f"\nUsage:")
        print(f"  echo '{json.dumps(sample_data)}' | python axis_adapters.py exec config.yaml")
        print(f"  python axis_adapters.py validate config.yaml")
        print(f"  python axis_adapters.py hash config.yaml")
        print(f"  python axis_adapters.py exec config.yaml --dry-run")
