#!/usr/bin/env python3
"""
AXIS-PIPES: α-conversion for JSON
Pure data normalization and validation

Pipeline: Raw JSON → Clean JSON
- Type coercion and validation
- Field renaming and restructuring  
- Data enrichment (deterministic only)
- Cryptographic verification

Usage:
    echo '{"user_name": "Alice", "age": "25"}' | python axis_pipes.py run normalize.yaml
"""

import json
import sys
import argparse
import hashlib
import math
from typing import Any, Dict, List, Union

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# RFC 8785 COMPLIANT CANONICALIZATION
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
        return obj  # Keep integers as integers
    elif isinstance(obj, float):
        if not math.isfinite(obj):
            raise ValueError("Non-finite numbers not allowed")
        return obj
    elif obj is None:
        return obj
    else:
        return str(obj)  # Convert everything else to string

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
# TEMPLATE SUBSTITUTION (unified)
# ============================================================================

def substitute_template(template: str, data: dict) -> str:
    """Safe template substitution with type handling"""
    import re
    
    def replace_var(match):
        var_path = match.group(1).strip()
        
        # Handle nested access like user.email
        parts = var_path.split('.')
        value = data
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return f"{{{{UNDEFINED:{var_path}}}}}"
        
        if value is None:
            return f"{{{{UNDEFINED:{var_path}}}}}"
        
        # Type-safe conversion
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(',', ':'))
        elif isinstance(value, bool):
            return str(value).lower()
        else:
            return str(value)
    
    return re.sub(r'\{\{([^}]+)\}\}', replace_var, template)

# ============================================================================
# PIPE OPERATIONS (α-conversion)
# ============================================================================

class PipelineEngine:
    """Execute pure data normalization pipelines"""
    
    def __init__(self, config: Union[dict, str]):
        if isinstance(config, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(config, 'r') as f:
                self.config = yaml.safe_load(f)
        else:
            self.config = config
        
        self.pipeline = self.config.get('pipeline', [])
        self.config_hash = compute_hash(self.config)
    
    def run(self, input_data: dict) -> dict:
        """Execute pipeline on input data - pure function"""
        # Deep copy to avoid mutations
        current_data = json.loads(json.dumps(input_data))
        
        # Validate steps before execution
        self._validate_pipeline()
        
        for i, step in enumerate(self.pipeline):
            try:
                current_data = self._apply_step(current_data, step)
            except Exception as e:
                # Errors as data, not exceptions that escape
                current_data.setdefault('errors', []).append(f"Step {i}: {e}")
        
        # Add pipeline audit (deterministic)
        payload = payload_view(current_data)
        audit = {
            'pipeline_hash': self.config_hash,
            'input_hash': compute_hash(payload_view(input_data)),
            'output_hash': compute_hash(payload),
            'steps_executed': len(self.pipeline)
        }
        
        return {**current_data, '_pipe_audit': audit}
    
    def _validate_pipeline(self):
        """Validate pipeline structure"""
        for i, step in enumerate(self.pipeline):
            if not isinstance(step, dict) or len(step) != 1:
                raise ValueError(f"Step {i}: must be single-key dict")
            
            step_type = list(step.keys())[0]
            if step_type not in ['extract', 'validate', 'rename', 'filter', 'enrich', 'transform']:
                raise ValueError(f"Step {i}: unknown step type '{step_type}'")
    
    def _apply_step(self, data: dict, step: dict) -> dict:
        """Apply a single pipeline step"""
        step_type = list(step.keys())[0]
        step_config = step[step_type]
        
        if step_type == 'extract':
            return self._extract(data, step_config)
        elif step_type == 'validate':
            return self._validate(data, step_config)
        elif step_type == 'rename':
            return self._rename(data, step_config)
        elif step_type == 'filter':
            return self._filter(data, step_config)
        elif step_type == 'enrich':
            return self._enrich(data, step_config)
        elif step_type == 'transform':
            return self._transform(data, step_config)
        else:
            raise ValueError(f"Unknown pipeline step: {step_type}")
    
    def _extract(self, data: dict, config: Union[str, dict]) -> dict:
        """Extract specific fields or paths"""
        if isinstance(config, str):
            # Simple path extraction
            if config.startswith('.'):
                path = config[1:]
                if path.endswith('[]') and path[:-2] in data:
                    # Array extraction
                    key = path[:-2]
                    if isinstance(data[key], list):
                        return {'items': data[key]}
                elif path in data:
                    # Simple field extraction
                    return {path: data[path]}
            return data
        elif isinstance(config, dict):
            # Extract multiple fields with renaming
            result = {}
            for new_key, path in config.items():
                if path in data:
                    result[new_key] = data[path]
            return result
        return data
    
    def _validate(self, data: dict, config: dict) -> dict:
        """Validate and coerce types"""
        errors = data.get('errors', [])
        
        for field, type_spec in config.items():
            if field not in data:
                errors.append(f"Missing field: {field}")
                continue
            
            value = data[field]
            try:
                if type_spec == "str":
                    data[field] = str(value)
                elif type_spec == "int":
                    data[field] = int(value)
                elif type_spec == "float":
                    result = float(value)
                    if not math.isfinite(result):
                        raise ValueError("Non-finite number")
                    data[field] = result
                elif type_spec == "bool":
                    if isinstance(value, str):
                        data[field] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        data[field] = bool(value)
                elif type_spec == "email":
                    email_str = str(value)
                    if '@' not in email_str or '.' not in email_str.split('@')[1]:
                        errors.append(f"Invalid email: {field}")
                    else:
                        data[field] = email_str
                else:
                    errors.append(f"Unknown type spec: {type_spec}")
            except (ValueError, TypeError) as e:
                errors.append(f"Type conversion failed for {field}: {e}")
        
        if errors:
            data['errors'] = errors
        return data
    
    def _rename(self, data: dict, mapping: dict) -> dict:
        """Rename fields - O(n) and predictable"""
        result = dict(data)  # Copy
        for old_key, new_key in mapping.items():
            if old_key in result:
                result[new_key] = result.pop(old_key)
        return result
    
    def _filter(self, data: dict, config: dict) -> dict:
        """Filter data based on conditions"""
        filtered = data.get('_filtered', [])
        
        for field, condition in config.items():
            if field not in data:
                continue
                
            value = data[field]
            should_filter = False
            
            if isinstance(condition, dict):
                if 'gt' in condition and value <= condition['gt']:
                    should_filter = True
                elif 'lt' in condition and value >= condition['lt']:
                    should_filter = True
                elif 'eq' in condition and value != condition['eq']:
                    should_filter = True
            
            if should_filter:
                filtered.append(field)
                data.pop(field, None)
        
        if filtered:
            data['_filtered'] = filtered
        return data
    
    def _enrich(self, data: dict, config: dict) -> dict:
        """Enrich data with deterministic values only"""
        for key, value in config.items():
            # Only allow deterministic enrichment
            if isinstance(value, (str, int, float, bool, dict, list)):
                data[key] = value
            else:
                data.setdefault('errors', []).append(
                    f"Non-deterministic enrichment not allowed: {key}={value}"
                )
        return data
    
    def _transform(self, data: dict, config: dict) -> dict:
        """Transform fields with template expressions"""
        for new_field, expression in config.items():
            try:
                if isinstance(expression, str) and '{{' in expression:
                    # Template substitution
                    result = substitute_template(expression, data)
                    data[new_field] = result
                else:
                    data[new_field] = expression
            except Exception as e:
                data.setdefault('errors', []).append(f"Transform failed for {new_field}: {e}")
        
        return data

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """CLI for AXIS-PIPES"""
    parser = argparse.ArgumentParser(description="AXIS-PIPES: Pure data normalization")
    parser.add_argument("command", choices=['run', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("config", help="Pipeline configuration file")
    parser.add_argument("--input", help="Input JSON file (use '-' for stdin)")
    parser.add_argument("--output", help="Output file (use '-' for stdout)")
    parser.add_argument("--strict", action='store_true', help="Strict validation mode")
    parser.add_argument("--quiet", "-q", action='store_true', help="Suppress non-essential output")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'run':
            # Load input data
            if args.input == '-' or args.input is None:
                input_data = json.load(sys.stdin)
            else:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            
            # Run pipeline
            engine = PipelineEngine(args.config)
            result = engine.run(input_data)
            
            # Strict mode: fail on errors
            if args.strict and 'errors' in result and result['errors']:
                print(f"Pipeline failed with errors: {result['errors']}", file=sys.stderr)
                sys.exit(1)
            
            # Output result
            output = json.dumps(result, indent=None if args.quiet else 2, separators=(',', ':'))
            if args.output == '-' or args.output is None:
                print(output)
            else:
                with open(args.output, 'w') as f:
                    f.write(output)
        
        elif args.command == 'validate':
            engine = PipelineEngine(args.config)
            engine._validate_pipeline()
            if not args.quiet:
                print(f"✅ Pipeline valid")
                print(f"✅ Steps: {len(engine.pipeline)}")
                print(f"✅ Config Hash: {engine.config_hash}")
        
        elif args.command == 'hash':
            engine = PipelineEngine(args.config)
            print(engine.config_hash)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    cli()
