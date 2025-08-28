#!/usr/bin/env python3
"""
AXIS-STRUCTURES: Enhanced Data Structure Registry for RA Operations
Prebuilt, hash-audited indexes, sets, queues, and maps for relational algebra

Enhanced with:
- Semi-join (exists_in) operations via AxisSet
- Anti-join (not_exists_in) operations via AxisSet  
- Better validation and error handling
- Field-based set membership checking
- Adapter integration stubs

Usage:
    from axis_structures import StructureRegistry
    registry = StructureRegistry("config.yaml")
    users_index = registry.get("users_by_id")  # Returns prebuilt hashmap
"""

import json
import os
import sys
import hashlib
import math
from typing import Any, Dict, List, Union, Optional, Set
from collections import defaultdict, deque
from datetime import datetime
import tempfile

# Import shared core functionality
try:
    from .axis_core import canonicalize, sha3_256_hex, get_timestamp
    HAS_CORE = True
except ImportError:
    print("Warning: axis_core.py not found. Using local implementations.", file=sys.stderr)
    HAS_CORE = False

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# Fallback implementations if axis_core not available
if not HAS_CORE:
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

    def get_timestamp():
        return datetime.now().isoformat()

# ============================================================================
# ENHANCED DATA STRUCTURE IMPLEMENTATIONS
# ============================================================================

class AxisHashMap:
    """Deterministic hashmap for fast joins and lookups"""
    
    def __init__(self, data: List[dict], key_field: str, name: str = "anonymous"):
        self.name = name
        self.key_field = key_field
        self.data = data
        self._index = {}
        self._build_index()
        self.structure_hash = self._generate_hash()
    
    def _build_index(self):
        """Build internal hash index"""
        for record in self.data:
            if self.key_field in record:
                key = record[self.key_field]
                if key not in self._index:
                    self._index[key] = []
                self._index[key].append(record)
    
    def _generate_hash(self) -> str:
        """Generate deterministic hash of structure"""
        canonical_data = canonicalize({
            'type': 'hashmap',
            'key_field': self.key_field,
            'data': self.data,
            'name': self.name
        })
        content = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(content)
    
    def get(self, key: Any) -> List[dict]:
        """Get records by key"""
        return self._index.get(key, [])
    
    def keys(self) -> List[Any]:
        """Get all keys"""
        return sorted(self._index.keys())
    
    def contains_key(self, key: Any) -> bool:
        """Check if key exists in hashmap"""
        return key in self._index
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for audit/persistence"""
        return {
            'type': 'hashmap',
            'name': self.name,
            'key_field': self.key_field,
            'data': self.data,
            'structure_hash': self.structure_hash,
            'record_count': len(self.data),
            'unique_keys': len(self._index)
        }

class AxisSet:
    """Enhanced deterministic set for union/difference/semi-join operations"""
    
    def __init__(self, data: List[dict], name: str = "anonymous"):
        self.name = name
        self.data = data
        self._canonical_hashes = set()
        self._field_indexes = defaultdict(set)  # Field -> set of values
        self._build_set()
        self.structure_hash = self._generate_hash()
    
    def _build_set(self):
        """Build internal set of record hashes and field indexes"""
        for record in self.data:
            # Full record hash for exact membership
            record_hash = sha3_256_hex(json.dumps(canonicalize(record), sort_keys=True))
            self._canonical_hashes.add(record_hash)
            
            # Build field indexes for semi/anti-joins
            for field, value in record.items():
                self._field_indexes[field].add(value)
    
    def _generate_hash(self) -> str:
        """Generate deterministic hash of structure"""
        canonical_data = canonicalize({
            'type': 'set', 
            'name': self.name,
            'hashes': sorted(list(self._canonical_hashes))
        })
        content = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(content)
    
    def contains(self, record: dict) -> bool:
        """Check if record exists in set (exact match)"""
        record_hash = sha3_256_hex(json.dumps(canonicalize(record), sort_keys=True))
        return record_hash in self._canonical_hashes
    
    def contains_field_value(self, field: str, value: Any) -> bool:
        """Check if any record has field=value (for semi/anti-joins)"""
        return value in self._field_indexes.get(field, set())
    
    def get_field_values(self, field: str) -> Set[Any]:
        """Get all unique values for a field"""
        return self._field_indexes.get(field, set())
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for audit/persistence"""
        return {
            'type': 'set',
            'name': self.name,
            'data': self.data,
            'structure_hash': self.structure_hash,
            'record_count': len(self.data),
            'unique_records': len(self._canonical_hashes),
            'indexed_fields': list(self._field_indexes.keys())
        }

class AxisQueue:
    """Deterministic queue for streaming operations"""
    
    def __init__(self, data: List[dict], name: str = "anonymous"):
        self.name = name
        self.data = data
        self._queue = deque(data)
        self.structure_hash = self._generate_hash()
    
    def _generate_hash(self) -> str:
        """Generate deterministic hash of structure"""
        canonical_data = canonicalize({
            'type': 'queue',
            'name': self.name,
            'data': self.data
        })
        content = json.dumps(canonical_data, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(content)
    
    def peek(self, count: int = 1) -> List[dict]:
        """Peek at next N items without removing"""
        return list(self._queue)[:count]
    
    def size(self) -> int:
        """Get queue size"""
        return len(self._queue)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dict for audit/persistence"""
        return {
            'type': 'queue',
            'name': self.name,
            'data': self.data,
            'structure_hash': self.structure_hash,
            'record_count': len(self.data)
        }

# ============================================================================
# STRUCTURE REGISTRY
# ============================================================================

class StructureRegistry:
    """Central registry for prebuilt data structures"""
    
    def __init__(self, config: Union[dict, str]):
        if isinstance(config, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.structures_config = self.config.get('structures', {})
        self.cache_dir = self.config.get('cache_dir', '.axis/cache')
        self._registry = {}
        self._audit_log = []
        
        # Ensure cache directory exists
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Build all declared structures
        self._materialize_all()
    
    def _materialize_all(self):
        """Materialize all structures declared in config"""
        for name, structure_config in self.structures_config.items():
            try:
                structure = self._materialize_structure(name, structure_config)
                self._registry[name] = structure
                
                # Log structure creation
                self._audit_log.append({
                    'action': 'structure_created',
                    'name': name,
                    'type': structure_config['type'],
                    'hash': structure.structure_hash,
                    'timestamp': get_timestamp()
                })
                
                # Persist if requested
                if structure_config.get('persist'):
                    self._persist_structure(name, structure, structure_config['persist'])
                    
            except Exception as e:
                self._audit_log.append({
                    'action': 'structure_failed',
                    'name': name,
                    'error': str(e),
                    'timestamp': get_timestamp()
                })
                raise ValueError(f"Failed to materialize structure '{name}': {e}")
    
    def _materialize_structure(self, name: str, config: Dict[str, Any]):
        """Materialize a single data structure"""
        structure_type = config['type']
        source_type = config.get('materialize', 'from_data')
        
        # Load source data
        if source_type == 'from_file':
            source_path = config['source']
            with open(source_path, 'r') as f:
                source_data = json.load(f)
        elif source_type == 'from_data':
            source_data = config.get('data', [])
        elif source_type == 'from_adapter':
            # Adapter-backed structure
            source_data = self._load_from_adapter(config)
        else:
            raise ValueError(f"Unknown materialize type: {source_type}")
        
        # Ensure source_data is a list
        if isinstance(source_data, dict):
            source_data = [source_data]
        elif not isinstance(source_data, list):
            source_data = []
        
        # Create appropriate structure
        if structure_type == 'hashmap':
            key_field = config['key']
            return AxisHashMap(source_data, key_field, name)
        elif structure_type == 'set':
            return AxisSet(source_data, name)
        elif structure_type == 'queue':
            return AxisQueue(source_data, name)
        else:
            raise ValueError(f"Unknown structure type: {structure_type}")
    
    def _load_from_adapter(self, config: Dict[str, Any]) -> List[dict]:
        """Load data via adapter (enhanced with error handling)"""
        adapter_config = config.get('adapter', {})
        
        # Simulate adapter execution - in production, this would call axis_adapters.py
        command = adapter_config.get('command', '')
        
        if command == 'redis_get':
            # Placeholder: would actually call Redis via adapter
            key = adapter_config.get('key', 'default')
            return [{"simulated": "redis_data", "key": key, "source": "redis"}]
        elif command == 'sqlite_query':
            # Placeholder: would actually query SQLite via adapter
            query = adapter_config.get('query', 'SELECT * FROM table')
            return [{"simulated": "sqlite_data", "query": query, "source": "sqlite"}]
        elif command == 'http_get':
            # Placeholder: would actually make HTTP request via adapter
            url = adapter_config.get('url', 'http://example.com/api/data')
            return [{"simulated": "http_data", "url": url, "source": "http"}]
        else:
            # Unknown adapter command
            self._audit_log.append({
                'action': 'adapter_unknown',
                'command': command,
                'timestamp': get_timestamp()
            })
            return []
    
    def _persist_structure(self, name: str, structure, persist_path: str):
        """Persist structure to disk"""
        full_path = os.path.join(self.cache_dir, persist_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            json.dump(structure.to_dict(), f, indent=2)
        
        self._audit_log.append({
            'action': 'structure_persisted',
            'name': name,
            'path': full_path,
            'timestamp': get_timestamp()
        })
    
    def get(self, name: str):
        """Get structure by name"""
        if name not in self._registry:
            raise KeyError(f"Structure '{name}' not found in registry")
        return self._registry[name]
    
    def exists(self, name: str) -> bool:
        """Check if structure exists"""
        return name in self._registry
    
    def list_structures(self) -> List[str]:
        """List all available structure names"""
        return list(self._registry.keys())
    
    def get_audit_log(self) -> List[Dict[str, Any]]:
        """Get structure creation/usage audit log"""
        return self._audit_log
    
    def log_structure_usage(self, name: str, operation: str, context: str = ""):
        """Log structure usage for audit trail"""
        self._audit_log.append({
            'action': 'structure_used',
            'name': name,
            'operation': operation,
            'context': context,
            'timestamp': get_timestamp()
        })
    
    def get_structure_hashes(self) -> Dict[str, str]:
        """Get hashes of all materialized structures"""
        return {name: struct.structure_hash for name, struct in self._registry.items()}
    
    def validate_structure_references(self, references: Dict[str, Any]) -> List[str]:
        """Validate structure references in operations"""
        errors = []
        
        for op_name, config in references.items():
            if 'using' in config:
                structure_name = config['using']
                if not self.exists(structure_name):
                    errors.append(f"{op_name} references unknown structure: {structure_name}")
                    continue
                
                structure = self.get(structure_name)
                structure_type = structure.to_dict()['type']
                
                # Validate structure type matches operation requirements
                if op_name == 'join':
                    if structure_type != 'hashmap':
                        errors.append(f"Join requires hashmap, but {structure_name} is {structure_type}")
                    elif 'on' in config:
                        expected_key = getattr(structure, 'key_field', None)
                        if expected_key and config['on'] != expected_key:
                            errors.append(f"Join key mismatch: using '{config['on']}' but structure expects '{expected_key}'")
                
                elif op_name in ['difference', 'exists_in', 'not_exists_in']:
                    if structure_type != 'set':
                        errors.append(f"{op_name} requires set, but {structure_name} is {structure_type}")
        
        return errors

# ============================================================================
# ENHANCED RA INTEGRATION HELPERS
# ============================================================================

def enhanced_join_with_structure(data: Union[dict, List[dict]], 
                                join_config: Dict[str, Any], 
                                registry: StructureRegistry) -> List[dict]:
    """Join operation using prebuilt structure from registry"""
    
    if 'using' not in join_config:
        raise ValueError("Structure-backed join requires 'using' parameter")
    
    structure_name = join_config['using']
    
    if not registry.exists(structure_name):
        raise ValueError(f"Structure '{structure_name}' not found in registry")
    
    structure = registry.get(structure_name)
    registry.log_structure_usage(structure_name, 'join')
    
    # Use structure for join
    if isinstance(structure, AxisHashMap):
        return _join_with_hashmap(data, structure, join_config)
    else:
        raise ValueError(f"Structure '{structure_name}' is not a hashmap (required for joins)")

def _join_with_hashmap(data: Union[dict, List[dict]], 
                       hashmap: AxisHashMap, 
                       join_config: Dict[str, Any]) -> List[dict]:
    """Perform join using prebuilt hashmap index"""
    
    # Normalize data to list
    records = [data] if isinstance(data, dict) else data or []
    if not isinstance(records, list):
        return []
    
    on_field = join_config['on']
    join_type = join_config.get('type', 'inner')
    
    results = []
    for record in records:
        if on_field not in record:
            if join_type == "left":
                # Include left record with no right match
                joined = {f"left_{k}": v for k, v in record.items()}
                results.append(joined)
            continue
        
        join_value = record[on_field]
        matching_records = hashmap.get(join_value)
        
        if matching_records:
            # Join with each matching record
            for right_record in matching_records:
                joined = {}
                # Add left fields with left_ prefix
                for k, v in record.items():
                    joined[f"left_{k}"] = v
                # Add right fields with right_ prefix
                for k, v in right_record.items():
                    joined[f"right_{k}"] = v
                results.append(joined)
        elif join_type == "left":
            # Left join: include record even with no match
            joined = {f"left_{k}": v for k, v in record.items()}
            results.append(joined)
    
    return results

def enhanced_difference_with_structure(data: Union[dict, List[dict]], 
                                     diff_config: Dict[str, Any],
                                     registry: StructureRegistry) -> List[dict]:
    """Difference operation using prebuilt structure from registry"""
    
    if 'using' not in diff_config:
        raise ValueError("Structure-backed difference requires 'using' parameter")
    
    structure_name = diff_config['using']
    
    if not registry.exists(structure_name):
        raise ValueError(f"Structure '{structure_name}' not found in registry")
    
    structure = registry.get(structure_name)
    registry.log_structure_usage(structure_name, 'difference')
    
    # Use structure for difference
    if isinstance(structure, AxisSet):
        return _difference_with_set(data, structure)
    else:
        raise ValueError(f"Structure '{structure_name}' is not a set (required for difference)")

def _difference_with_set(data: Union[dict, List[dict]], axis_set: AxisSet) -> List[dict]:
    """Perform difference using prebuilt set"""
    records = [data] if isinstance(data, dict) else data or []
    if not isinstance(records, list):
        return []
    
    results = []
    for record in records:
        if not axis_set.contains(record):
            results.append(record)
    
    return sorted(results, key=lambda x: json.dumps(canonicalize(x), sort_keys=True))

def enhanced_exists_in_with_structure(data: Union[dict, List[dict]], 
                                    exists_config: Dict[str, Any],
                                    registry: StructureRegistry) -> List[dict]:
    """Semi-join operation using prebuilt structure from registry"""
    
    if 'using' not in exists_config:
        raise ValueError("Structure-backed exists_in requires 'using' parameter")
    
    structure_name = exists_config['using']
    field = exists_config['field']
    
    if not registry.exists(structure_name):
        raise ValueError(f"Structure '{structure_name}' not found in registry")
    
    structure = registry.get(structure_name)
    registry.log_structure_usage(structure_name, 'exists_in')
    
    # Use structure for semi-join
    if isinstance(structure, AxisSet):
        return _exists_in_with_set(data, structure, field)
    else:
        raise ValueError(f"Structure '{structure_name}' is not a set (required for exists_in)")

def _exists_in_with_set(data: Union[dict, List[dict]], axis_set: AxisSet, field: str) -> List[dict]:
    """Perform semi-join using prebuilt set"""
    records = [data] if isinstance(data, dict) else data or []
    if not isinstance(records, list):
        return []
    
    results = []
    for record in records:
        if field in record and axis_set.contains_field_value(field, record[field]):
            results.append(record)
    
    return results

def enhanced_not_exists_in_with_structure(data: Union[dict, List[dict]], 
                                        not_exists_config: Dict[str, Any],
                                        registry: StructureRegistry) -> List[dict]:
    """Anti-join operation using prebuilt structure from registry"""
    
    if 'using' not in not_exists_config:
        raise ValueError("Structure-backed not_exists_in requires 'using' parameter")
    
    structure_name = not_exists_config['using']
    field = not_exists_config['field']
    
    if not registry.exists(structure_name):
        raise ValueError(f"Structure '{structure_name}' not found in registry")
    
    structure = registry.get(structure_name)
    registry.log_structure_usage(structure_name, 'not_exists_in')
    
    # Use structure for anti-join
    if isinstance(structure, AxisSet):
        return _not_exists_in_with_set(data, structure, field)
    else:
        raise ValueError(f"Structure '{structure_name}' is not a set (required for not_exists_in)")

def _not_exists_in_with_set(data: Union[dict, List[dict]], axis_set: AxisSet, field: str) -> List[dict]:
    """Perform anti-join using prebuilt set"""
    records = [data] if isinstance(data, dict) else data or []
    if not isinstance(records, list):
        return []
    
    results = []
    for record in records:
        if field not in record or not axis_set.contains_field_value(field, record[field]):
            results.append(record)
    
    return results

# ============================================================================
# INTEGRATION WITH AXIS SCRIPTS
# ============================================================================

def integrate_structures_with_ra(step_config: Dict[str, Any], 
                                registry: Optional[StructureRegistry] = None) -> Dict[str, Any]:
    """Integrate structure registry with RA operations"""
    
    if not registry:
        # No registry provided, use standard RA operations
        return step_config
    
    # Check for structure-enhanced operations
    enhanced_step = dict(step_config)
    
    structure_ops = ['join', 'difference', 'exists_in', 'not_exists_in']
    for op in structure_ops:
        if op in step_config and 'using' in step_config[op]:
            enhanced_step[f'_structure_{op}'] = True
    
    return enhanced_step

def get_structure_audit_info(registry: Optional[StructureRegistry]) -> Dict[str, Any]:
    """Get audit information for all structures"""
    if not registry:
        return {}
    
    return {
        'structures_materialized': len(registry.list_structures()),
        'structure_names': registry.list_structures(),
        'structure_hashes': registry.get_structure_hashes(),
        'audit_log': registry.get_audit_log()
    }

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for AXIS-STRUCTURES"""
    import argparse
    
    parser = argparse.ArgumentParser(description="AXIS-STRUCTURES: Enhanced data structure registry")
    parser.add_argument("command", choices=[
        'materialize', 'info', 'audit', 'hash', 'export', 'validate'
    ], help="Command to execute")
    parser.add_argument("config", help="Structure configuration file")
    parser.add_argument("--structure", help="Specific structure name")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--operations", help="Operations config file for validation")
    
    args = parser.parse_args()
    
    try:
        registry = StructureRegistry(args.config)
        
        if args.command == 'materialize':
            # Force rematerialization of all structures
            registry._materialize_all()
            print(f"Materialized {len(registry.list_structures())} structures")
            for name in registry.list_structures():
                structure = registry.get(name)
                info = structure.to_dict()
                print(f"  {name}: {info['type']} ({structure.structure_hash[:8]}...) - {info['record_count']} records")
        
        elif args.command == 'info':
            # Show structure information
            if args.structure:
                if registry.exists(args.structure):
                    structure = registry.get(args.structure)
                    info = structure.to_dict()
                    output = json.dumps(info, indent=2)
                    if args.output:
                        with open(args.output, 'w') as f:
                            f.write(output)
                    else:
                        print(output)
                else:
                    print(f"Structure '{args.structure}' not found")
            else:
                print(f"Registry: {len(registry.list_structures())} structures")
                for name in registry.list_structures():
                    structure = registry.get(name)
                    info = structure.to_dict()
                    print(f"  {name}: {info['type']} | {info['record_count']} records | {info['structure_hash'][:8]}...")
                    if info['type'] == 'set' and 'indexed_fields' in info:
                        print(f"    Indexed fields: {', '.join(info['indexed_fields'])}")
        
        elif args.command == 'validate':
            # Validate structure references in operations config
            if not args.operations:
                print("Error: --operations required for validate command")
                sys.exit(1)
            
            with open(args.operations, 'r') as f:
                if args.operations.endswith('.yaml') or args.operations.endswith('.yml'):
                    if not HAS_YAML:
                        print("Error: YAML support requires pyyaml")
                        sys.exit(1)
                    operations_config = yaml.safe_load(f)
                else:
                    operations_config = json.load(f)
            
            # Extract operation references
            references = {}
            pipeline = operations_config.get('pipeline', [])
            for i, step in enumerate(pipeline):
                for op_name, op_config in step.items():
                    if isinstance(op_config, dict) and 'using' in op_config:
                        references[f"{op_name}_step_{i}"] = op_config
            
            validation_errors = registry.validate_structure_references(references)
            if validation_errors:
                print("Structure reference validation errors:")
                for error in validation_errors:
                    print(f"  - {error}")
                sys.exit(1)
            else:
                print("✓ All structure references are valid")
        
        elif args.command == 'audit':
            # Show audit log
            audit = registry.get_audit_log()
            output = json.dumps(audit, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
        
        elif args.command == 'hash':
            # Show structure hashes
            hashes = registry.get_structure_hashes()
            if args.structure:
                if args.structure in hashes:
                    print(hashes[args.structure])
                else:
                    print(f"Structure '{args.structure}' not found")
            else:
                for name, hash_val in hashes.items():
                    print(f"{name}: {hash_val}")
        
        elif args.command == 'export':
            # Export structure data
            if not args.structure:
                print("Error: --structure required for export")
                return
            
            if registry.exists(args.structure):
                structure = registry.get(args.structure)
                export_data = structure.to_dict()
                
                output = json.dumps(export_data, indent=2)
                if args.output:
                    with open(args.output, 'w') as f:
                        f.write(output)
                    print(f"Exported {args.structure} to {args.output}")
                else:
                    print(output)
            else:
                print(f"Structure '{args.structure}' not found")
    
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
        print("AXIS-STRUCTURES: Enhanced Data Structure Registry")
        print("Prebuilt, hash-audited structures for RA operations\n")
        
        # Demo structure configuration with enhanced features
        sample_config = {
            "cache_dir": ".axis/cache",
            "structures": {
                "users_by_id": {
                    "type": "hashmap",
                    "key": "user_id", 
                    "materialize": "from_data",
                    "data": [
                        {"user_id": "u1", "name": "Alice", "dept": "eng", "role": "admin"},
                        {"user_id": "u2", "name": "Bob", "dept": "sales", "role": "user"},
                        {"user_id": "u3", "name": "Charlie", "dept": "eng", "role": "admin"}
                    ]
                },
                "admin_whitelist": {
                    "type": "set",
                    "materialize": "from_data",
                    "data": [
                        {"user_id": "u1", "approved": True},
                        {"user_id": "u3", "approved": True},
                        {"role": "admin", "name": "Alice"},
                        {"role": "admin", "name": "Charlie"}
                    ]
                },
                "blocked_users": {
                    "type": "set",
                    "materialize": "from_data",
                    "data": [
                        {"user_id": "blocked1"},
                        {"user_id": "blocked2"},
                        {"name": "BadUser"}
                    ]
                },
                "event_stream": {
                    "type": "queue",
                    "materialize": "from_data", 
                    "data": [
                        {"event": "login", "user_id": "u1", "timestamp": "10:00"},
                        {"event": "purchase", "user_id": "u2", "amount": 150},
                        {"event": "logout", "user_id": "u1", "timestamp": "11:00"}
                    ]
                }
            }
        }
        
        # Create registry
        registry = StructureRegistry(sample_config)
        
        print(f"Materialized structures:")
        for name in registry.list_structures():
            structure = registry.get(name)
            info = structure.to_dict()
            print(f"  {name}: {info['type']} | {info['record_count']} records | {info['structure_hash'][:8]}...")
            
            # Show enhanced features for sets
            if info['type'] == 'set' and 'indexed_fields' in info:
                print(f"    Indexed fields: {', '.join(info['indexed_fields'])}")
        
        print(f"\nEnhanced RA operations supported:")
        print(f"  • Join with prebuilt hashmap for O(1) lookups")
        print(f"  • Semi-join (exists_in) with field-indexed sets")
        print(f"  • Anti-join (not_exists_in) with field-indexed sets")
        print(f"  • Set difference with exact record matching")
        
        print(f"\nExample usage in pipelines:")
        print(f"  # Fast join")
        print(f"  join: {{ on: user_id, using: users_by_id }}")
        print(f"")
        print(f"  # Semi-join: keep users in admin whitelist")
        print(f"  exists_in: {{ field: user_id, using: admin_whitelist }}")
        print(f"")
        print(f"  # Anti-join: exclude blocked users")
        print(f"  not_exists_in: {{ field: name, using: blocked_users }}")
        
        print(f"\nStructure hashes (for verification):")
        hashes = registry.get_structure_hashes()
        for name, hash_val in hashes.items():
            print(f"  {name}: {hash_val[:16]}...")
        
        print(f"\nCLI usage:")
        print(f"  python axis_structures.py materialize config.yaml")
        print(f"  python axis_structures.py info config.yaml --structure users_by_id")
        print(f"  python axis_structures.py validate config.yaml --operations pipeline.yaml")
        print(f"  python axis_structures.py audit config.yaml")
        print(f"  python axis_structures.py hash config.yaml")
