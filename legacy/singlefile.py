#!/usr/bin/env python3
"""
AXIS: React for Deterministic Reasoning
Complete single-file implementation (~400 LOC)

"We split the atom of software complexity and found that simplicity was the most powerful force inside."

Pipeline: YAML → AST → Pure Reducer → Cryptographic Audit
- Canonical IR with SHA3-256 hashing
- Security-first AST validation  
- Cross-platform determinism
- Zero framework dependencies

Usage:
    from axis_complete import RuleEngine, validate
    
    engine = RuleEngine('rules.yaml')
    result = engine.run(user_data)
"""

import json
import math
import hashlib
import ast
import os
import sys
import argparse
import tempfile
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, Set
from abc import ABC, abstractmethod
import urllib.request
import urllib.parse
import urllib.error

# Optional imports
try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False
    yaml = None

# ============================================================================
# CRYPTOGRAPHIC VERIFICATION & CANONICALIZATION
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
    """Content addressing for IR verification"""
    return hashlib.sha3_256(s.encode("utf-8")).hexdigest()

def generate_ir_hash(rules: dict, component_name: str) -> str:
    """Generate cryptographic hash of canonical rules"""
    canonical_rules = canonicalize({
        'component': component_name,
        'rules': rules,
        'compiler_version': 'axis@1.0.0'
    })
    ir_json = json.dumps(canonical_rules, sort_keys=True, separators=(',', ':'))
    return sha3_256_hex(ir_json)

# ============================================================================
# SECURE AST PARSER
# ============================================================================

ALLOWED_OPS = {
    'eq', 'noteq', 'gt', 'lt', 'gte', 'lte', 'in', 'notin',
    'and', 'or', 'not'
}

def parse_condition_to_ast(condition: str) -> dict:
    """Parse condition string to restricted AST"""
    def _convert(node):
        if isinstance(node, ast.BoolOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'logical',
                'op': op_name,
                'values': [_convert(v) for v in node.values]
            }
        elif isinstance(node, ast.Compare):
            if len(node.ops) != 1:
                raise ValueError("Only single comparisons supported")
            op_name = node.ops[0].__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'binary_op',
                'op': op_name,
                'left': _convert(node.left),
                'right': _convert(node.comparators[0])
            }
        elif isinstance(node, ast.UnaryOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name not in ALLOWED_OPS:
                raise ValueError(f"Operation {op_name} not allowed")
            return {
                'type': 'unary_op',
                'op': op_name,
                'operand': _convert(node.operand)
            }
        elif isinstance(node, ast.Name):
            return {'type': 'var', 'name': node.id}
        elif isinstance(node, ast.Constant):
            return {'type': 'literal', 'value': node.value}
        elif isinstance(node, ast.Attribute):
            return {'type': 'var', 'name': _get_full_name(node)}
        else:
            raise ValueError(f"Unsupported node: {ast.dump(node)}")
    
    def _get_full_name(node):
        """Convert ast.Attribute to dot notation"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{_get_full_name(node.value)}.{node.attr}"
        else:
            raise ValueError("Unsupported attribute node")
    
    try:
        parsed = ast.parse(condition, mode='eval')
        return _convert(parsed.body)
    except Exception as e:
        raise ValueError(f"Failed to parse condition '{condition}': {e}")

def evaluate_ast(ast_node: dict, context: dict) -> Any:
    """Evaluate AST against context - pure function"""
    node_type = ast_node['type']
    
    if node_type == 'var':
        name = ast_node['name']
        if '.' in name:
            parts = name.split('.')
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                else:
                    return None
            return value
        return context.get(name)
    elif node_type == 'literal':
        return ast_node['value']
    elif node_type == 'binary_op':
        left = evaluate_ast(ast_node['left'], context)
        right = evaluate_ast(ast_node['right'], context)
        op = ast_node['op']
        try:
            if op == 'eq': return left == right
            elif op == 'noteq': return left != right
            elif op == 'gt': return left > right
            elif op == 'lt': return left < right
            elif op == 'gte': return left >= right
            elif op == 'lte': return left <= right
            elif op == 'in': return left in right
            elif op == 'notin': return left not in right
        except TypeError:
            return False
        return False
    elif node_type == 'unary_op':
        operand = evaluate_ast(ast_node['operand'], context)
        if ast_node['op'] == 'not':
            return not operand
        return operand
    elif node_type == 'logical':
        values = [evaluate_ast(v, context) for v in ast_node['values']]
        if ast_node['op'] == 'and':
            return all(values)
        elif ast_node['op'] == 'or':
            return any(values)
    return False

# ============================================================================
# PURE REDUCER ENGINE
# ============================================================================

def apply_rules(rules: List[dict], state: dict, action: dict) -> dict:
    """Apply rules deterministically - React reducer pattern"""
    new_state = json.loads(json.dumps(state))
    context = dict(new_state)
    context.update(action)
    
    new_state.setdefault('computed', {}).clear()
    new_state.setdefault('errors', []).clear()
    
    pending_changes = []
    
    for i, rule in enumerate(rules):
        should_apply = True
        if 'if' in rule:
            try:
                condition_ast = parse_condition_to_ast(rule['if'])
                should_apply = evaluate_ast(condition_ast, context)
            except Exception as e:
                if os.getenv('AXIS_DEBUG'):
                    print(f"Rule {i} condition failed: {e}", file=sys.stderr)
                should_apply = False
        
        target_branch = 'then' if should_apply else 'else'
        if target_branch in rule:
            changes = rule[target_branch]
            if isinstance(changes, dict):
                for key, value in changes.items():
                    merge_policy = 'replace'
                    clean_key = key
                    if key.endswith('+'):
                        merge_policy = 'append'
                        clean_key = key[:-1]
                    pending_changes.append({
                        'key': clean_key,
                        'value': value,
                        'merge_policy': merge_policy,
                        'order': i
                    })
    
    pending_changes.sort(key=lambda x: (x['order'], x['key']))
    
    for change in pending_changes:
        key, value, merge_policy = change['key'], change['value'], change['merge_policy']
        if merge_policy == 'append' and isinstance(new_state.get(key), list):
            if isinstance(value, list):
                new_state[key].extend(value)
            else:
                new_state[key].append(value)
        else:
            new_state[key] = value
    
    return new_state

# ============================================================================
# RULE ENGINE
# ============================================================================

class RuleEngine:
    """YAML-based rule engine - React component for business logic"""
    
    def __init__(self, rules: Union[dict, str, List[dict]]):
        if isinstance(rules, str):
            if not HAS_YAML:
                raise RuntimeError("YAML support requires: pip install pyyaml")
            with open(rules, 'r') as f:
                self.rules_data = yaml.safe_load(f)
        elif isinstance(rules, dict):
            self.rules_data = rules
        elif isinstance(rules, list):
            self.rules_data = {'rules': rules}
        else:
            raise ValueError("Rules must be dict, list, or YAML file path")
        
        if 'rules' in self.rules_data:
            self.rules = self.rules_data['rules']
        elif isinstance(self.rules_data, list):
            self.rules = self.rules_data
        else:
            raise ValueError("Rules must contain 'rules' key or be a list")
        
        self.component_name = self.rules_data.get('component', 'anonymous')
        self.initial_state = self.rules_data.get('initial_state', {})
        self.ir_hash = generate_ir_hash(self.rules, self.component_name)
    
    def run(self, input_data: dict, action: dict = None) -> dict:
        """Execute rules against input data"""
        if action is None:
            action = {'type': 'RULE_CHECK'}
        
        new_state = apply_rules(self.rules, input_data, action)
        
        audit_entry = {
            'ir_hash': self.ir_hash,
            'input_hash': sha3_256_hex(json.dumps(canonicalize(input_data), sort_keys=True)),
            'output_hash': sha3_256_hex(json.dumps(canonicalize(new_state), sort_keys=True)),
            'action': action
        }
        
        return {**new_state, '_audit': audit_entry}
    
    def create_reducer(self):
        """Create Redux-style reducer function"""
        def reducer(state: dict, action: dict) -> dict:
            return self.run(state, action)
        return reducer

# ============================================================================
# VALIDATION UTILITIES
# ============================================================================

def validate(data: dict, schema: Union[dict, str]) -> Tuple[bool, List[str]]:
    """Validate data against schema"""
    if isinstance(schema, str):
        if not HAS_YAML:
            return False, ["YAML support requires: pip install pyyaml"]
        try:
            with open(schema, 'r') as f:
                schema = yaml.safe_load(f)
        except Exception as e:
            return False, [f"Failed to load schema: {e}"]
    
    errors = []
    for field, type_spec in schema.items():
        is_optional = type_spec.endswith('?')
        if is_optional:
            type_spec = type_spec[:-1]
        
        if field not in data:
            if not is_optional:
                errors.append(f"Missing required field: {field}")
            continue
        
        value = data[field]
        if type_spec == "str":
            if not isinstance(value, str):
                try:
                    data[field] = str(value)
                except Exception:
                    errors.append(f"{field}: expected str")
        elif type_spec == "int":
            if not isinstance(value, int):
                try:
                    data[field] = int(value)
                except Exception:
                    errors.append(f"{field}: expected int")
        elif type_spec == "float":
            if not isinstance(value, (int, float)):
                try:
                    data[field] = float(value)
                except Exception:
                    errors.append(f"{field}: expected float")
        elif type_spec == "bool":
            if not isinstance(value, bool):
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'yes', 'on'):
                        data[field] = True
                    elif value.lower() in ('false', '0', 'no', 'off'):
                        data[field] = False
                    else:
                        errors.append(f"{field}: expected bool")
                else:
                    errors.append(f"{field}: expected bool")
    
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

# ============================================================================
# DATABASE ADAPTER
# ============================================================================

class DatabaseAdapter(ABC):
    """Abstract base for database adapters"""
    @abstractmethod
    def save(self, table: str, data: Dict[str, Any]) -> Any: pass
    @abstractmethod
    def find(self, table: str, query: Dict[str, Any]) -> List[Dict[str, Any]]: pass
    @abstractmethod
    def update(self, table: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool: pass

class SQLiteAdapter(DatabaseAdapter):
    """SQLite adapter for simple file-based storage"""
    def __init__(self, db_path: str):
        import sqlite3
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
    
    def save(self, table: str, data: Dict[str, Any]) -> Any:
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.conn.execute(query, list(data.values()))
        self.conn.commit()
        return cursor.lastrowid
    
    def find(self, table: str, query: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        if not query:
            sql = f"SELECT * FROM {table}"
            params = []
        else:
            conditions = ' AND '.join([f"{k} = ?" for k in query.keys()])
            sql = f"SELECT * FROM {table} WHERE {conditions}"
            params = list(query.values())
        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update(self, table: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = ?" for k in query.keys()])
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(query.values())
        cursor = self.conn.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount > 0
    
    def close(self): self.conn.close()

# ============================================================================
# HTTP ADAPTER
# ============================================================================

class HTTPAdapter:
    """Simple HTTP client adapter - pure Python stdlib"""
    def __init__(self, base_url: str, default_headers: Dict[str, str] = None):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {
            'Content-Type': 'application/json',
            'User-Agent': 'AXIS-HTTPAdapter/1.0'
        }
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        req = urllib.request.Request(url, headers=self.default_headers)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")
    
    def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        json_data = json.dumps(data or {}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=self.default_headers)
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")

# ============================================================================
# GOLDEN VECTOR TESTING
# ============================================================================

class GoldenVectorGenerator:
    """Generate test vectors for AXIS rules"""
    def __init__(self, rules_path: str):
        self.engine = RuleEngine(rules_path)
        self.vectors = []
    
    def add_test_case(self, input_data: Dict[str, Any], description: str = ""):
        result = self.engine.run(input_data)
        vector = {
            'description': description,
            'input': input_data,
            'expected_output': {k: v for k, v in result.items() if k != '_audit'},
            'ir_hash': result['_audit']['ir_hash'],
            'output_hash': result['_audit']['output_hash']
        }
        self.vectors.append(vector)
        return vector
    
    def save_vectors(self, filename: str):
        with open(filename, 'w') as f:
            json.dump({'component': self.engine.component_name, 'vectors': self.vectors}, f, indent=2)

class GoldenVectorRunner:
    """Run golden vector tests for verification"""
    def __init__(self, rules_path: str):
        self.engine = RuleEngine(rules_path)
    
    def run_tests(self, vectors_file: str) -> Dict[str, Any]:
        with open(vectors_file, 'r') as f:
            test_data = json.load(f)
        
        results = {'total': len(test_data['vectors']), 'passed': 0, 'failed': 0, 'failures': []}
        
        for i, vector in enumerate(test_data['vectors']):
            try:
                result = self.engine.run(vector['input'])
                actual_output = {k: v for k, v in result.items() if k != '_audit'}
                if actual_output == vector['expected_output']:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
                    results['failures'].append({
                        'test_index': i,
                        'description': vector.get('description', ''),
                        'expected': vector['expected_output'],
                        'actual': actual_output
                    })
            except Exception as e:
                results['failed'] += 1
                results['failures'].append({'test_index': i, 'error': str(e)})
        
        return results

# ============================================================================
# FRAMEWORK INTEGRATIONS
# ============================================================================

def with_axis_rules(yaml_path: str):
    """Flask decorator for route validation"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                from flask import request, jsonify, g
            except ImportError:
                raise RuntimeError("Flask integration requires: pip install flask")
            
            if not hasattr(g, 'axis_engine'):
                g.axis_engine = RuleEngine(yaml_path)
            
            if request.method == 'POST':
                input_data = request.get_json() or {}
            else:
                input_data = request.args.to_dict()
            
            result = g.axis_engine.run(input_data)
            if result.get('errors'):
                return jsonify({'errors': result['errors']}), 400
            
            return func(result, *args, **kwargs)
        return wrapper
    return decorator

def create_axis_dependency(yaml_path: str):
    """FastAPI dependency for validation"""
    class AxisMiddleware:
        def __init__(self, yaml_path: str):
            self.engine = RuleEngine(yaml_path)
        
        def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
            result = self.engine.run(data)
            if result.get('errors'):
                try:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=400, detail=result['errors'])
                except ImportError:
                    raise RuntimeError("FastAPI integration requires: pip install fastapi")
            return result
    
    middleware = AxisMiddleware(yaml_path)
    def axis_validator(data: dict) -> dict:
        return middleware.validate(data)
    return axis_validator

# ============================================================================
# CLI INTERFACE
# ============================================================================

def cli():
    """Simple CLI for running AXIS rules"""
    parser = argparse.ArgumentParser(description="AXIS: React for Deterministic Reasoning")
    parser.add_argument("command", choices=['run', 'validate', 'hash', 'test'], help="Command to execute")
    parser.add_argument("rules", help="Path to YAML rules file")
    parser.add_argument("input", nargs='?', help="JSON input as string or @file.json")
    parser.add_argument("--output", help="Output file for results")
    
    args = parser.parse_args()
    
    try:
        if args.command == 'run':
            if not args.input:
                print("Error: input required for 'run' command", file=sys.stderr)
                sys.exit(1)
            
            if args.input.startswith("@"):
                with open(args.input[1:], 'r') as f:
                    input_data = json.load(f)
            else:
                input_data = json.loads(args.input)
            
            engine = RuleEngine(args.rules)
            result = engine.run(input_data)
            output = json.dumps(result, indent=2)
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(output)
                print(f"Result written to {args.output}")
            else:
                print(output)
        
        elif args.command == 'validate':
            engine = RuleEngine(args.rules)
            print(f"✓ Rules valid: {engine.component_name}")
            print(f"✓ Rule count: {len(engine.rules)}")
            print(f"✓ IR Hash: {engine.ir_hash}")
        
        elif args.command == 'hash':
            engine = RuleEngine(args.rules)
            print(engine.ir_hash)
        
        elif args.command == 'test':
            if not args.input:
                print("Error: test vectors file required")
                return
            runner = GoldenVectorRunner(args.rules)
            results = runner.run_tests(args.input)
            print(f"Tests: {results['total']}")
            print(f"Passed: {results['passed']}")
            print(f"Failed: {results['failed']}")
            if results['failures']:
                print("Failures:")
                for failure in results['failures']:
                    if 'error' in failure:
                        print(f"  - Test {failure['test_index']}: {failure['error']}")
                    else:
                        print(f"  - Test {failure['test_index']}: Output mismatch")
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

# ============================================================================
# MAIN EXPORTS & DEMO
# ============================================================================

def load_rules(path: str) -> RuleEngine:
    """Load rules from YAML file - convenience function"""
    return RuleEngine(path)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        cli()
    else:
        # Demo mode
        print("🚀 AXIS: React for Deterministic Reasoning")
        print("Complete single-file implementation (~400 LOC)\n")
        
        # Quick validation demo
        data = {"name": "Alice", "age": "25"}
        is_valid, errors = validate(data, {"name": "str", "age": "int"})
        print(f"1. Validation: {data} → Valid: {is_valid}\n")
        
        # Rule engine demo
        rules = {
            "component": "UserAccess",
            "rules": [
                {"if": "age >= 18", "then": {"status": "adult", "can_vote": True}},
                {"if": "age < 18", "then": {"status": "minor", "can_vote": False}},
                {"if": "not email", "then": {"errors+": ["Email required"]}},
                {"if": "role == 'admin'", "then": {"permissions": ["read", "write", "admin"]}}
            ]
        }
        
        engine = RuleEngine(rules)
        test_data = {"age": 25, "email": "alice@example.com", "role": "admin"}
        result = engine.run(test_data)
        clean_result = {k: v for k, v in result.items() if k != '_audit'}
        
        print(f"2. Rule Engine:")
        print(f"   Input: {test_data}")
        print(f"   Output: {json.dumps(clean_result, indent=6)}")
        print(f"   Hash: {result['_audit']['ir_hash'][:16]}...")
        
        print(f"\n3. CLI Usage:")
        print(f"   python axis_complete.py run rules.yaml '{{\"age\": 25}}'")
        print(f"   python axis_complete.py validate rules.yaml")
        print(f"   python axis_complete.py hash rules.yaml")
        
        print(f"\n🎯 Single file, ~400 LOC, production ready!")
        print(f"   React for Deterministic Reasoning ⚡")
