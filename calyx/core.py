#!/usr/bin/env python3
"""
CALYX-PY: Zero-boilerplate Python reasoning library
Replaces Pydantic, FastAPI, LangChain, and Mypy with YAML + rules + optional AI
"""

import json
import os
import sys
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

# Optional imports
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False
    requests = None


def validate(data: dict, schema: Union[dict, str]) -> Tuple[bool, List[str]]:
    """
    Validate data against schema (dict or YAML path).
    
    Schema format:
        {"name": "str", "age": "int", "email": "str?"}
    
    Returns:
        (is_valid, list_of_errors)
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
        
        elif type_spec == "list":
            if not isinstance(value, list):
                errors.append(f"{field}: expected list, got {type(value).__name__}")
        
        elif type_spec == "dict":
            if not isinstance(value, dict):
                errors.append(f"{field}: expected dict, got {type(value).__name__}")
        
        else:
            errors.append(f"{field}: unknown type {type_spec}")
    
    return len(errors) == 0, errors


def typecheck(schema: dict):
    """
    Decorator that validates function arguments against schema.
    Raises TypeError on validation failure.
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(data: dict, *args, **kwargs):
            is_valid, errors = validate(data, schema)
            if not is_valid:
                raise TypeError(f"Validation failed: {'; '.join(errors)}")
            return func(data, *args, **kwargs)
        return wrapper
    return decorator


def fallback(fn: Callable, llm: str = "gpt-4", prompt: str = "Fix this: {input}") -> Callable:
    """
    Wrap function with LLM fallback. If fn fails or returns None, call LLM.
    
    Note: Requires OPENAI_API_KEY environment variable.
    """
    @wraps(fn)
    def wrapper(input_data: Any) -> Any:
        # Try the original function
        try:
            result = fn(input_data)
            if result is not None:
                return result
        except Exception as e:
            # Log the error if debug mode
            if os.getenv('CALYX_DEBUG'):
                print(f"Function {fn.__name__} failed: {e}", file=sys.stderr)
        
        # Fallback to LLM
        if not HAS_REQUESTS:
            raise RuntimeError("LLM fallback requires: pip install requests")
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise RuntimeError("LLM fallback requires OPENAI_API_KEY environment variable")
        
        # Format the prompt
        formatted_prompt = prompt.format(input=json.dumps(input_data))
        
        # Call OpenAI API
        try:
            response = requests.post(
                'https://api.openai.com/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': llm,
                    'messages': [{'role': 'user', 'content': formatted_prompt}],
                    'temperature': 0.7
                }
            )
            response.raise_for_status()
            
            # Extract the response
            content = response.json()['choices'][0]['message']['content']
            
            # Try to parse as JSON if it looks like JSON
            if content.strip().startswith('{') or content.strip().startswith('['):
                try:
                    return json.loads(content)
                except json.JSONDecodeError:
                    pass
            
            return content
            
        except Exception as e:
            raise RuntimeError(f"LLM fallback failed: {e}")
    
    return wrapper


class RuleEngine:
    """
    YAML-based rule engine with if/then/else logic.
    """
    
    def __init__(self, rules: Union[dict, str]):
        """
        Initialize with rules dict or YAML file path.
        """
        if isinstance(rules, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(rules, 'r') as f:
                self.rules = yaml.safe_load(f)
        else:
            self.rules = rules
        
        # Normalize rules structure
        if 'rules' in self.rules:
            self.rule_list = self.rules['rules']
        elif isinstance(self.rules, list):
            self.rule_list = self.rules
        else:
            raise ValueError("Rules must be a list or dict with 'rules' key")
    
    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """
        Safely evaluate a condition string against context.
        """
        # Basic safety check
        dangerous = ['import', 'exec', 'eval', '__', 'open', 'file']
        for d in dangerous:
            if d in condition:
                raise ValueError(f"Unsafe condition: {condition}")
        
        try:
            # Create safe evaluation context
            safe_context = dict(context)
            safe_context.update({
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool,
                'True': True,
                'False': False,
                'None': None,
            })
            
            # Evaluate the condition
            return eval(condition, {"__builtins__": {}}, safe_context)
        except Exception as e:
            if os.getenv('CALYX_DEBUG'):
                print(f"Condition evaluation failed: {condition} - {e}", file=sys.stderr)
            return False
    
    def run(self, input_data: dict) -> dict:
        """
        Execute rules against input data, return merged result.
        """
        result = {}
        
        for rule in self.rule_list:
            # Handle if/then rules
            if 'if' in rule:
                condition = rule['if']
                if self._evaluate_condition(condition, input_data):
                    if 'then' in rule:
                        result.update(rule['then'])
                    break
            
            # Handle else rules (no condition)
            elif 'else' in rule:
                result.update(rule.get('then', {}))
                break
        
        return result
    
    def serve(self, port: int = 8000, host: str = '0.0.0.0'):
        """
        Start HTTP server for rules (uses stdlib http.server).
        """
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json
        
        engine = self
        
        class RuleHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                # Read request body
                content_length = int(self.headers.get('Content-Length', 0))
                body = self.rfile.read(content_length)
                
                try:
                    # Parse JSON input
                    input_data = json.loads(body.decode('utf-8'))
                    
                    # Run rules
                    result = engine.run(input_data)
                    
                    # Send response
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(result).encode('utf-8'))
                    
                except json.JSONDecodeError:
                    self.send_error(400, 'Invalid JSON')
                except Exception as e:
                    self.send_error(500, str(e))
            
            def do_GET(self):
                # Simple health check
                self.send_response(200)
                self.send_header('Content-Type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'CALYX Rule Engine Running\n')
            
            def log_message(self, format, *args):
                # Suppress default logging unless debug mode
                if os.getenv('CALYX_DEBUG'):
                    super().log_message(format, *args)
        
        # Start server
        server = HTTPServer((host, port), RuleHandler)
        print(f"CALYX Rule Engine serving at http://{host}:{port}")
        print("POST JSON to / to execute rules")
        print("Press Ctrl+C to stop")
        
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down...")
            server.shutdown()


# Convenience functions for common patterns
def load_rules(path: str) -> RuleEngine:
    """Load rules from YAML file."""
    return RuleEngine(path)


def quick_validate(data: dict, **types) -> dict:
    """
    Quick validation with keyword arguments.
    Example: quick_validate(data, name="str", age="int", email="str?")
    """
    is_valid, errors = validate(data, types)
    if not is_valid:
        raise ValueError(f"Validation failed: {'; '.join(errors)}")
    return data


# Example usage patterns
if __name__ == "__main__":
    # Example 1: Validation
    data = {"name": "Alice", "age": "25"}
    is_valid, errors = validate(data, {"name": "str", "age": "int"})
    print(f"Valid: {is_valid}, Data: {data}")
    
    # Example 2: Typecheck decorator
    @typecheck({"x": "int", "y": "int"})
    def add(data):
        return data["x"] + data["y"]
    
    print(f"Sum: {add({'x': 10, 'y': 20})}")
    
    # Example 3: Rules
    rules = {
        "rules": [
            {"if": "age >= 18", "then": {"status": "adult"}},
            {"else": None, "then": {"status": "minor"}}
        ]
    }
    
    engine = RuleEngine(rules)
    print(f"Rule result: {engine.run({'age': 25})}")
