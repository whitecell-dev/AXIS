#!/usr/bin/env python3
"""
Simple validation utilities
Schema format: {"name": "str", "age": "int", "email": "str?"}
"""

from functools import wraps
from typing import Any, Callable, Dict, List, Tuple, Union

# Optional YAML support
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

def validate(data: dict, schema: Union[dict, str]) -> Tuple[bool, List[str]]:
    """
    Validate data against schema
    Returns: (is_valid, list_of_errors)
    """
    # Load schema from YAML if path provided
    if isinstance(schema, str):
        if not HAS_YAML:
            return False, ["YAML support requires: pip install pyyaml"]
        try:
            with open(schema, 'r') as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            return False, [f"Failed to load schema: {e}"]
    
    errors = []
    
    # Validate each field
    for field, type_spec in schema.items():
        # Handle optional fields (ending with ?)
        is_optional = type_spec.endswith('?')
        if is_optional:
            type_spec = type_spec[:-1]
        
        # Check if field exists
        if field not in data:
            if not is_optional:
                errors.append(f"Missing required field: {field}")
            continue
        
        value = data[field]
        
        # Type checking and coercion
        if type_spec == "str":
            if not isinstance(value, str):
                try:
                    data[field] = str(value)
                except Exception:
                    errors.append(f"{field}: expected str, got {type(value).__name__}")
        
        elif type_spec == "int":
            if not isinstance(value, int):
                try:
                    data[field] = int(value)
                except Exception:
                    errors.append(f"{field}: expected int, got {type(value).__name__}")
        
        elif type_spec == "float":
            if not isinstance(value, (int, float)):
                try:
                    data[field] = float(value)
                except Exception:
                    errors.append(f"{field}: expected float, got {type(value).__name__}")
        
        elif type_spec == "bool":
            if not isinstance(value, bool):
                # Coerce common bool representations
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes', 'on'):
                        data[field] = True
                    elif value.lower() in ('false', '0', 'no', 'off'):
                        data[field] = False
                    else:
                        errors.append(f"{field}: expected bool, got {value}")
                else:
                    errors.append(f"{field}: expected bool, got {type(value).__name__}")
        
        else:
            errors.append(f"{field}: unknown type {type_spec}")
    
    return len(errors) == 0, errors

def quick_validate(data: dict, **types) -> dict:
    """Quick validation with keyword arguments"""
    is_valid, errors = validate(data, types)
    if not is_valid:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")
    return data

def typecheck(schema: dict):
    """Decorator for function argument validation"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(data: dict, *args, **kwargs):
            is_valid, errors = validate(data, schema)
            if not is_valid:
                raise TypeError(f"Validation failed: {'; '.join(errors)}")
            return func(data, *args, **kwargs)
        return wrapper
    return decorator
