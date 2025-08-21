#!/usr/bin/env python3
"""
AXIS-PIPES: α-conversion for JSON
Data normalization, validation, and reshaping

Pipeline: Raw JSON → Clean JSON
- Type coercion and validation
- Field renaming and restructuring  
- Data enrichment and filtering
- Deterministic canonicalization

Usage:
    echo '{"user_name": "Alice", "age": "25"}' | python axis_pipes.py run normalize.yaml
"""

import json
import sys
import argparse
import hashlib
import math
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
# CANONICALIZATION (from AXIS core)
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
    """Content addressing for pipeline verification"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

# ============================================================================
# PIPE OPERATIONS (α-conversion)
# ============================================================================

class PipelineEngine:
    """Execute data normalization pipelines"""
    
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
    
    def _generate_config_hash(self) -> str:
        """Generate hash of pipeline configuration"""
        canonical_config = canonicalize(self.config)
        config_json = json.dumps(canonical_config, sort_keys=True, separators=(',', ':'))
        return sha3_256_hex(config_json)
    
    def run(self, input_data: dict) -> dict:
        """Execute pipeline on input data"""
        current_data = json.loads(json.dumps(input_data))  # Deep copy
        
        for i, step in enumerate(self.pipeline):
            try:
                current_data = self._apply_step(current_data, step)
            except Exception as e:
                raise ValueError(f"Pipeline step {i} failed: {e}")
        
        # Add pipeline audit
        audit = {
            'pipeline_hash': self.config_hash,
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'output_hash': sha3_256_hex(json.dumps(canonicalize(current_data), sort_keys=True))
        }
        
        return {**current_data, '_pipe_audit': audit}
    
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
            # Simple path extraction like ".users[]"
            if config.startswith('.'):
                path = config[1:]  # Remove leading dot
                if path.endswith('[]'):
                    # Array extraction
                    key = path[:-2]
                    if key in data and isinstance(data[key], list):
                        return {'items': data[key]}
                else:
                    # Simple field extraction
                    if path in data:
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
        errors = []
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
                    data[field] = float(value)
                elif type_spec == "bool":
                    if isinstance(value, str):
                        data[field] = value.lower() in ('true', '1', 'yes', 'on')
                    else:
                        data[field] = bool(value)
                elif type_spec == "email":
                    if '@' not in str(value):
                        errors.append(f"Invalid email: {field}")
                    else:
                        data[field] = str(value)
            except (ValueError, TypeError):
                errors.append(f"Type conversion failed for {field}: expected {type_spec}")
        
        if errors:
            data.setdefault('errors', []).extend(errors)
        
        return data
    
    def _rename(self, data: dict, config: dict) -> dict:
        """Rename fields"""
        result = {}
        for old_key, new_key in config.items():
            if old_key in data:
                result[new_key] = data[old_key]
            else:
                # Keep non-renamed fields
                for k, v in data.items():
                    if k not in config:
                        result[k] = v
        return result
    
    def _filter(self, data: dict, config: dict) -> dict:
        """Filter data based on conditions"""
        # Simple filtering - extend as needed
        for field, condition in config.items():
            if field in data:
                value = data[field]
                if isinstance(condition, dict):
                    if 'gt' in condition and value <= condition['gt']:
                        data.setdefault('_filtered', []).append(field)
                    elif 'lt' in condition and value >= condition['lt']:
                        data.setdefault('_filtered', []).append(field)
                    elif 'eq' in condition and value != condition['eq']:
                        data.setdefault('_filtered', []).append(field)
        return data
    
    def _enrich(self, data: dict, config: dict) -> dict:
        """Enrich data with additional fields"""
        for key, value in config.items():
            if value == "now()":
                data[key] = datetime.now().isoformat()
            elif value == "timestamp()":
                data[key] = int(datetime.now().timestamp())
            else:
                data[key] = value
        return data
    
    def _transform(self, data: dict, config: dict) -> dict:
        """Transform fields with simple expressions"""
        for new_field, expression in config.items():
            try:
                # Simple template substitution
                if isinstance(expression, str) and '{{' in expression:
                    # Template like "{{first_name}} {{last_name}}"
                    result = expression
                    for field, value in data.items():
                        result = result.replace(f"{{{{{field}}}}}", str(value))
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
    parser = argparse.ArgumentParser(description="AXIS-PIPES: Data normalization and validation")
    parser.add_argument("command", choices=['run', 'validate', 'hash'], help="Command to execute")
    parser.add_argument("config", help="Pipeline configuration file")
    parser.add_argument("--input", help="Input JSON file (default: stdin)")
    parser.add_argument("--output", help="Output file (default: stdout)")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'run':
            # Load input data
            if args.input:
                with open(args.input, 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = json.load(sys.stdin)
            
            # Run pipeline
            engine = PipelineEngine(args.config)
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
            print(f"✓ Pipeline valid")
            print(f"✓ Steps: {len(engine.pipeline)}")
            print(f"✓ Config Hash: {engine.config_hash}")
        
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
        print("🔀 AXIS-PIPES: α-conversion for JSON")
        print("Data normalization and validation\n")
        
        # Demo pipeline
        sample_data = {"user_name": "Alice", "age": "25", "active": "true"}
        sample_config = {
            "pipeline": [
                {"rename": {"user_name": "name"}},
                {"validate": {"age": "int", "active": "bool"}},
                {"enrich": {"timestamp": "now()", "source": "demo"}}
            ]
        }
        
        engine = PipelineEngine(sample_config)
        result = engine.run(sample_data)
        clean_result = {k: v for k, v in result.items() if k != '_pipe_audit'}
        
        print(f"Input:  {sample_data}")
        print(f"Output: {clean_result}")
        print(f"Hash:   {result['_pipe_audit']['pipeline_hash'][:16]}...")
        
        print(f"\nUsage:")
        print(f"  echo '{json.dumps(sample_data)}' | python axis_pipes.py run config.yaml")
        print(f"  python axis_pipes.py validate config.yaml")
        print(f"  python axis_pipes.py hash config.yaml")
