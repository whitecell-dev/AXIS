#!/usr/bin/env python3
"""
AXIS-PIPES: Refined α-conversion for JSON + Enhanced Relational Algebra
Data normalization, validation, and RA operations with Structure Registry

Pipeline: Raw JSON → Clean JSON (+ RA filtering/projection + prebuilt structures)
- Type coercion and validation
- Field renaming and restructuring  
- Data enrichment and filtering
- Deterministic canonicalization
- Enhanced: σ (select), π (project), ⨝ (join), exists_in, not_exists_in, AGGREGATE
- Structure registry integration for O(1) operations
- Unified filter/select semantics

Usage:
    echo '{"user_name": "Alice", "age": "25"}' | python axis_pipes.py run normalize.yaml
"""

import json
import sys
import argparse
from typing import Any, Dict, List, Union
from datetime import datetime

# Import shared core functionality
try:
    from .axis_core import canonicalize, sha3_256_hex, get_timestamp
    HAS_CORE = True
except ImportError:
    print("Warning: axis_core.py not found. Using local implementations.", file=sys.stderr)
    HAS_CORE = False

# Import RA primitives
try:
    from .axis_ra import apply_ra_operation, is_ra_operation, extract_ra_operations, apply_ra_pipeline, generate_ra_audit, validate_ra_operation
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

# Fallback implementations if axis_core not available
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
    
    def get_timestamp():
        return datetime.now().isoformat()

# ============================================================================
# STRUCTURE REGISTRY INTEGRATION HELPERS
# ============================================================================

def _uses_structure(config: dict) -> bool:
    """Check if operation references a structure"""
    structure_ops = ['join', 'difference', 'union', 'exists_in', 'not_exists_in']
    return any(op in config and 'using' in config[op] for op in structure_ops)

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
    
    elif 'exists_in' in config and 'using' in config['exists_in']:
        # Enhanced exists_in (semi-join)
        try:
            from .axis_structures import enhanced_exists_in_with_structure
            result = enhanced_exists_in_with_structure(data, config['exists_in'], registry)
            structures_used_log.append(config['exists_in']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    elif 'not_exists_in' in config and 'using' in config['not_exists_in']:
        # Enhanced not_exists_in (anti-join)
        try:
            from .axis_structures import enhanced_not_exists_in_with_structure
            result = enhanced_not_exists_in_with_structure(data, config['not_exists_in'], registry)
            structures_used_log.append(config['not_exists_in']['using'])
            return result
        except ImportError:
            return apply_ra_operation(data, config)
    
    else:
        # Fallback to standard RA
        return apply_ra_operation(data, config)

# ============================================================================
# ENHANCED PIPE OPERATIONS (α-conversion + RA + Structures)
# ============================================================================

class PipelineEngine:
    """Execute data normalization pipelines with RA and structure registry support"""
    
    def __init__(self, config: Union[dict, str]):
        if isinstance(config, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.pipeline = self.config.get('pipeline', [])
        self.config_hash = self._generate_config_hash()
        
        # Structure registry integration
        self.registry = None
        if 'structures' in self.config:
            try:
                from .axis_structures import StructureRegistry
                self.registry = StructureRegistry(self.config)
            except ImportError:
                pass  # Structure registry not available
    
    def _generate_config_hash(self) -> str:
        """Generate hash of pipeline configuration"""
        canonical_config = canonicalize(self.config)
        config_json = json.dumps(canonical_config, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(config_json)
    
    def _apply_to_records(self, data, fn):
        """Helper: apply a per-record function to dict or list-of-dicts"""
        if isinstance(data, list):
            return [fn(rec) for rec in data if isinstance(rec, dict)]
        elif isinstance(data, dict):
            return fn(data)
        return data
    
    def validate(self) -> List[str]:
        """Validate pipeline configuration and return error messages"""
        errors = []
        
        for i, step in enumerate(self.pipeline):
            try:
                # Validate RA operations
                if HAS_RA and is_ra_operation(step):
                    ra_ops = extract_ra_operations(step)
                    for op in ra_ops:
                        ra_errors = validate_ra_operation(op, self.registry)
                        for error in ra_errors:
                            errors.append(f"Step {i}: {error}")
                else:
                    # Validate traditional pipe operations
                    step_type = list(step.keys())[0] if step else None
                    if step_type not in ['extract', 'validate', 'rename', 'select', 'enrich', 'transform', 'flag']:
                        if step_type == 'filter':
                            errors.append(f"Step {i}: 'filter' is deprecated, use 'select' for RA filtering or 'flag' for field flagging")
                        else:
                            errors.append(f"Step {i}: Unknown operation '{step_type}'")
            except Exception as e:
                errors.append(f"Step {i}: Validation error - {e}")
        
        return errors
    
    def run(self, input_data: dict) -> dict:
        """Execute pipeline on input data"""
        current_data = json.loads(json.dumps(input_data))  # Deep copy
        ra_operations_applied = []
        
        # Track structure usage for audit
        structures_used = []
        
        for i, step in enumerate(self.pipeline):
            try:
                # Enhanced step processing with structure registry
                if HAS_RA and is_ra_operation(step):
                    # Check if operation references structures
                    if self.registry and _uses_structure(step):
                        current_data = _apply_structure_enhanced_ra(current_data, step, self.registry, structures_used)
                    else:
                        # Standard RA operation
                        ra_ops = extract_ra_operations(step)
                        current_data = apply_ra_pipeline(current_data, ra_ops)
                    ra_operations_applied.extend(extract_ra_operations(step))
                else:
                    # Traditional pipe operations
                    current_data = self._apply_step(current_data, step)
            except Exception as e:
                raise ValueError(f"Pipeline step {i} failed: {e}")
        
        # Add pipeline audit
        audit = {
            'pipeline_hash': self.config_hash,
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'output_hash': sha3_256_hex(json.dumps(canonicalize(current_data), sort_keys=True)),
            'steps_executed': len(self.pipeline),
            'timestamp': get_timestamp()
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
            ra_audit = generate_ra_audit(input_data, ra_operations_applied, current_data)
            audit['ra_audit'] = ra_audit
            
        payload = {'data': current_data} if not isinstance(current_data, dict) else current_data
        return {**payload, '_pipe_audit': audit} 
            
    def _apply_step(self, data: dict, step: dict) -> dict:
        """Apply a single pipeline step (original AXIS functionality)"""
        step_type = list(step.keys())[0]
        step_config = step[step_type]
        
        if step_type == 'extract':
            return self._extract(data, step_config)
        elif step_type == 'validate':
            return self._validate(data, step_config)
        elif step_type == 'rename':
            return self._rename(data, step_config)
        elif step_type == 'select':
            # Unified select - can be RA filter or field selector
            if isinstance(step_config, str):
                # RA-style predicate filtering
                if HAS_RA:
                    from .axis_ra import RelationalAlgebra
                    ra = RelationalAlgebra()
                    return ra.select(data, step_config)
                else:
                    raise ValueError("RA select requires axis_ra.py")
            else:
                # Field selection (like extract)
                return self._extract(data, step_config)
        elif step_type == 'flag':
            return self._flag(data, step_config)
        elif step_type == 'filter':
            # Deprecated - warn and redirect
            print(f"Warning: 'filter' is deprecated. Use 'select' for RA filtering or 'flag' for field flagging.", file=sys.stderr)
            return self._flag(data, step_config)
        elif step_type == 'enrich':
            return self._enrich(data, step_config)
        elif step_type == 'transform':
            return self._transform(data, step_config)
        else:
            raise ValueError(f"Unknown pipeline step: {step_type}")
    
    def _extract(self, data: dict, config: Union[str, dict]) -> dict:
        """Extract specific fields or paths"""
        def extract_one(d: dict):
            if isinstance(config, str):
                # Simple path extraction like ".users[]"
                if config.startswith('.'):
                    path = config[1:]  # Remove leading dot
                    if path.endswith('[]'):
                        # Array extraction
                        key = path[:-2]
                        if key in d and isinstance(d[key], list):
                            return {'items': d[key]}
                    else:
                        # Simple field extraction
                        if path in d:
                            return {path: d[path]}
                return d
            elif isinstance(config, dict):
                # Extract multiple fields with renaming
                result = {}
                for new_key, path in config.items():
                    if path in d:
                        result[new_key] = d[path]
                return result
            return d
        
        return self._apply_to_records(data, extract_one)
    
    def _validate(self, data: dict, config: dict) -> dict:
        """Validate and coerce types"""
        def validate_one(d: dict):
            errors = []
            for field, type_spec in config.items():
                if field not in d:
                    errors.append(f"Missing field: {field}")
                    continue
                
                value = d[field]
                try:
                    if type_spec == "str":
                        d[field] = str(value)
                    elif type_spec == "int":
                        d[field] = int(value)
                    elif type_spec == "float":
                        d[field] = float(value)
                    elif type_spec == "bool":
                        if isinstance(value, bool):
                            d[field] = value
                        elif isinstance(value, str):
                            d[field] = value.strip().lower() in ("1", "true", "t", "yes", "y")
                        else:
                            d[field] = bool(value)
                    elif type_spec == "email":
                        if '@' not in str(value):
                            errors.append(f"Invalid email: {field}")
                        else:
                            d[field] = str(value)
                    else:
                        d[field] = value
                except (ValueError, TypeError):
                    errors.append(f"Type conversion failed for {field}: expected {type_spec}")
            
            if errors:
                d.setdefault('errors', []).extend(errors)
            return d
        
        return self._apply_to_records(data, validate_one)
    
    def _rename(self, data: dict, config: dict) -> dict:
        def rename_one(d: dict):
            result = dict(d)  # start with all original fields
            for old_key, new_key in config.items():
                if old_key in result:
                    result[new_key] = result.pop(old_key)
            return result
        
        return self._apply_to_records(data, rename_one)
    
    def _flag(self, data: dict, config: dict) -> dict:
        """Flag data based on conditions (renamed from filter for clarity)"""
        def flag_one(d: dict):
            for field, condition in config.items():
                if field in d and isinstance(condition, dict):
                    value = d[field]
                    if 'gt' in condition and value <= condition['gt']:
                        d.setdefault('_flagged', []).append(field)
                    elif 'lt' in condition and value >= condition['lt']:
                        d.setdefault('_flagged', []).append(field)
                    elif 'eq' in condition and value != condition['eq']:
                        d.setdefault('_flagged', []).append(field)
            return d
        
        return self._apply_to_records(data, flag_one)
    
    def _enrich(self, data: dict, config: dict) -> dict:
        """Enrich data with additional fields"""
        def enrich_one(d: dict):
            for key, value in config.items():
                if value == "now()":
                    d[key] = datetime.now().isoformat()
                elif value == "timestamp()":
                    d[key] = int(datetime.now().timestamp())
                else:
                    d[key] = value
            return d
        
        return self._apply_to_records(data, enrich_one)
    
    def _transform(self, data: dict, config: dict) -> dict:
        """Transform fields with simple expressions"""
        def transform_one(d: dict):
            for new_field, expression in config.items():
                try:
                    # Simple template substitution
                    if isinstance(expression, str) and '{{' in expression:
                        # Template like "{{first_name}} {{last_name}}"
                        result = expression
                        for field, value in d.items():
                            result = result.replace(f"{{{{{field}}}}}", str(value))
                        d[new_field] = result
                    else:
                        d[new_field] = expression
                except Exception as e:
                    d.setdefault('errors', []).append(f"Transform failed for {new_field}: {e}")
            return d
        
        return self._apply_to_records(data, transform_one)

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for AXIS-PIPES"""
    parser = argparse.ArgumentParser(description="AXIS-PIPES: Data normalization + RA operations + Structure Registry")
    parser.add_argument("command", choices=['run', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("config", help="Pipeline configuration file")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    parser.add_argument("--dry-run", action='store_true', help="Validate pipeline without processing data")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'run':
            engine = PipelineEngine(args.config)
            
            # Validate first
            validation_errors = engine.validate()
            if validation_errors:
                print("Pipeline validation errors:", file=sys.stderr)
                for error in validation_errors:
                    print(f"  - {error}", file=sys.stderr)
                if not args.dry_run:
                    sys.exit(1)
            
            if args.dry_run:
                print("Pipeline validation passed")
                print(f"Steps: {len(engine.pipeline)}")
                if engine.registry:
                    print(f"Structures: {len(engine.registry.list_structures())}")
                print(f"Config Hash: {engine.config_hash}")
                return
            
            # Load input data
            if args.input:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = json.load(sys.stdin)
            
            # Run pipeline
            result = engine.run(input_data)
            
            # Output result
            output = json.dumps(result, indent=2)
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
            else:
                print(output)
        
        elif args.command == 'validate':
            engine = PipelineEngine(args.config)
            validation_errors = engine.validate()
            
            if validation_errors:
                print("Pipeline validation errors:")
                for error in validation_errors:
                    print(f"  - {error}")
                sys.exit(1)
            else:
                print(f"Pipeline valid")
                print(f"Steps: {len(engine.pipeline)}")
                if engine.registry:
                    print(f"Structures: {len(engine.registry.list_structures())}")
                print(f"Config Hash: {engine.config_hash}")
        
        elif args.command == 'hash':
            engine = PipelineEngine(args.config)
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
        print("AXIS-PIPES: Refined α-conversion for JSON + Enhanced Relational Algebra")
        print("Data normalization and RA operations with prebuilt structures\n")
        
        # Demo pipeline with RA and structures including semi/anti-joins
        sample_data = [
            {"user_name": "Alice", "age": "25", "active": "true", "role": "admin", "dept_id": "eng"},
            {"user_name": "Bob", "age": "17", "active": "true", "role": "user", "dept_id": "sales"},
            {"user_name": "Charlie", "age": "30", "active": "false", "role": "admin", "dept_id": "eng"}
        ]
        
        sample_config = {
            "structures": {
                "departments_by_id": {
                    "type": "hashmap",
                    "key": "dept_id",
                    "materialize": "from_data",
                    "data": [
                        {"dept_id": "eng", "dept_name": "Engineering", "budget": 500000},
                        {"dept_id": "sales", "dept_name": "Sales", "budget": 300000}
                    ]
                },
                "admin_whitelist": {
                    "type": "set",
                    "materialize": "from_data",
                    "data": [
                        {"role": "admin", "user_name": "Alice"},
                        {"role": "admin", "user_name": "Charlie"}
                    ]
                }
            },
            "pipeline": [
                {"rename": {"user_name": "name"}},
                {"validate": {"age": "int", "active": "bool"}},
                {"select": "age >= 18"},  # RA: Filter adults only (unified select)
                {"exists_in": {           # RA: Semi-join with whitelist
                    "field": "name",
                    "using": "admin_whitelist"
                }},
                {"select": "active == true"},  # RA: Filter active users
                {"join": {                # RA: Join with prebuilt structure
                    "on": "dept_id",
                    "using": "departments_by_id"
                }},
                {"project": ["left_name", "right_dept_name", "right_budget"]},  # RA: Select columns
                {"enrich": {"timestamp": "now()", "source": "demo"}}
            ]
        }
        
        engine = PipelineEngine(sample_config)
        
        print(f"Input:  {json.dumps(sample_data, indent=2)}")
        print(f"Config: {len(engine.pipeline)} steps (including enhanced RA + structures)")
        if engine.registry:
            print(f"Structures: {len(engine.registry.list_structures())} materialized")
        print(f"Hash:   {engine.config_hash[:16]}...")
        
        # Validate pipeline
        validation_errors = engine.validate()
        if validation_errors:
            print(f"\nValidation errors:")
            for error in validation_errors:
                print(f"  - {error}")
        else:
            print(f"✓ Pipeline validation passed")
        
        if HAS_RA:
            result = engine.run(sample_data)
            clean_result = {k: v for k, v in result.items() if not k.startswith('_')}
            print(f"\nOutput: {json.dumps(clean_result, indent=2)}")
            
            audit = result['_pipe_audit']
            if 'ra_audit' in audit:
                print(f"RA Ops: {audit['ra_audit']['operations_count']} applied")
            if 'structures_used' in audit:
                print(f"Structures used: {audit['structures_used']}")
        else:
            print("\nRA operations disabled (axis_ra.py not available)")
        
        print(f"\nKey improvements:")
        print(f"  • Unified 'select' operation (RA filtering + field selection)")
        print(f"  • 'filter' deprecated → 'flag' for field flagging")
        print(f"  • Enhanced semi-join (exists_in) and anti-join (not_exists_in)")
        print(f"  • Pipeline validation with structure reference checking")
        print(f"  • --dry-run support for validation without execution")
        
        print(f"\nUsage:")
        print(f"  echo '{json.dumps(sample_data)}' | python axis_pipes.py run config.yaml")
        print(f"  python axis_pipes.py validate config.yaml")
        print(f"  python axis_pipes.py run config.yaml --dry-run")
        print(f"  python axis_pipes.py hash config.yaml")
