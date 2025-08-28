#!/usr/bin/env python3
"""
AXIS-RA: Enhanced Relational Algebra Primitives for JSON
Added semi-join (exists_in) and anti-join (not_exists_in) operations

Key Updates:
- exists_in: σ-like filter based on set membership 
- not_exists_in: anti-join flavor
- Unified join handling for 'with' vs 'using'
- Better error messages and validation
"""

import json
import hashlib
import math
from typing import Any, Dict, List, Union, Set, Tuple, Optional
from collections import defaultdict
import re
import ast

# Import shared core functionality
try:
    from .axis_core import canonicalize, sha3_256_hex, safe_eval_predicate, uses_structure
    HAS_CORE = True
except ImportError:
    print("Warning: axis_core.py not found. Using local implementations.", file=sys.stderr)
    HAS_CORE = False

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

    def safe_eval_predicate(predicate: str, context: dict) -> bool:
        try:
            parsed = ast.parse(predicate, mode='eval')
            return _eval_ast_node(parsed.body, context)
        except Exception:
            return False

    def _eval_ast_node(node, context: dict) -> Any:
        if isinstance(node, ast.BoolOp):
            op_name = node.op.__class__.__name__.lower()
            if op_name == 'and':
                return all(_eval_ast_node(v, context) for v in node.values)
            elif op_name == 'or':
                return any(_eval_ast_node(v, context) for v in node.values)
        
        elif isinstance(node, ast.Compare):
            left = _eval_ast_node(node.left, context)
            right = _eval_ast_node(node.comparators[0], context)
            op = node.ops[0].__class__.__name__.lower()
            
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
        
        elif isinstance(node, ast.UnaryOp):
            if node.op.__class__.__name__.lower() == 'not':
                return not _eval_ast_node(node.operand, context)
        
        elif isinstance(node, ast.Name):
            return context.get(node.id)
        
        elif isinstance(node, ast.Attribute):
            obj = _eval_ast_node(node.value, context)
            if isinstance(obj, dict):
                return obj.get(node.attr)
            return None
        
        elif isinstance(node, ast.Constant):
            return node.value
        
        return None

    def uses_structure(config: dict) -> bool:
        return any(op in config and 'using' in config[op] 
                  for op in ['join', 'difference', 'union', 'exists_in', 'not_exists_in'])

# ============================================================================
# ENHANCED RELATIONAL ALGEBRA PRIMITIVES
# ============================================================================

class RelationalAlgebra:
    """Enhanced RA operations for JSON data with semi/anti-join support"""
    
    @staticmethod
    def select(data: Union[dict, List[dict]], predicate: str) -> Union[dict, List[dict]]:
        """σ (sigma) - Filter operation like SQL WHERE"""
        if isinstance(data, dict):
            if safe_eval_predicate(predicate, data):
                return data
            else:
                return {}
        
        elif isinstance(data, list):
            return [record for record in data if safe_eval_predicate(predicate, record)]
        
        return data
    
    @staticmethod
    def project(data: Union[dict, List[dict]], attributes: List[str]) -> Union[dict, List[dict]]:
        """π (pi) - Projection operation like SQL SELECT columns"""
        def _project_record(record: dict) -> dict:
            return {attr: record.get(attr) for attr in attributes if attr in record}
        
        if isinstance(data, dict):
            return _project_record(data)
        elif isinstance(data, list):
            return [_project_record(record) for record in data]
        return data
    
    @staticmethod
    def join(left_data: Union[dict, List[dict]], right_data: Union[dict, List[dict]], 
             on_field: str, join_type: str = "inner") -> List[dict]:
        """⨝ (bowtie) - Join operation like SQL JOIN"""
        
        # Normalize to lists
        left_records = [left_data] if isinstance(left_data, dict) else left_data or []
        right_records = [right_data] if isinstance(right_data, dict) else right_data or []
        
        if not isinstance(left_records, list) or not isinstance(right_records, list):
            return []
        
        # Build index for right side
        right_index = defaultdict(list)
        for record in right_records:
            if on_field in record:
                right_index[record[on_field]].append(record)
        
        # Perform join
        results = []
        for left_record in left_records:
            if on_field not in left_record:
                if join_type == "left":
                    # Include left record with no right match
                    joined = {f"left_{k}": v for k, v in left_record.items()}
                    results.append(joined)
                continue
            
            join_value = left_record[on_field]
            matching_right = right_index.get(join_value, [])
            
            if matching_right:
                # Join each left with each matching right
                for right_record in matching_right:
                    joined = {}
                    # Add left fields with left_ prefix
                    for k, v in left_record.items():
                        joined[f"left_{k}"] = v
                    # Add right fields with right_ prefix
                    for k, v in right_record.items():
                        joined[f"right_{k}"] = v
                    results.append(joined)
            elif join_type == "left":
                # Left join: include left record with no match
                joined = {f"left_{k}": v for k, v in left_record.items()}
                results.append(joined)
        
        return results
    
    @staticmethod
    def exists_in(data: Union[dict, List[dict]], field: str, 
                  reference_set: Union[List[dict], Set[Any]]) -> Union[dict, List[dict]]:
        """Semi-join: keep records where field value exists in reference set"""
        
        # Build reference values set
        if isinstance(reference_set, (list, tuple)):
            ref_values = set()
            for item in reference_set:
                if isinstance(item, dict) and field in item:
                    ref_values.add(item[field])
                else:
                    ref_values.add(item)
        else:
            ref_values = reference_set
        
        # Filter data
        if isinstance(data, dict):
            if field in data and data[field] in ref_values:
                return data
            return {}
        
        elif isinstance(data, list):
            return [record for record in data 
                   if field in record and record[field] in ref_values]
        
        return data
    
    @staticmethod
    def not_exists_in(data: Union[dict, List[dict]], field: str,
                      reference_set: Union[List[dict], Set[Any]]) -> Union[dict, List[dict]]:
        """Anti-join: keep records where field value NOT in reference set"""
        
        # Build reference values set  
        if isinstance(reference_set, (list, tuple)):
            ref_values = set()
            for item in reference_set:
                if isinstance(item, dict) and field in item:
                    ref_values.add(item[field])
                else:
                    ref_values.add(item)
        else:
            ref_values = reference_set
        
        # Filter data
        if isinstance(data, dict):
            if field not in data or data[field] not in ref_values:
                return data
            return {}
        
        elif isinstance(data, list):
            return [record for record in data 
                   if field not in record or record[field] not in ref_values]
        
        return data
    
    @staticmethod
    def aggregate(data: Union[dict, List[dict]], group_by: Union[str, List[str]], 
                  operation: str, target_field: Optional[str] = None) -> List[dict]:
        """GROUP BY + aggregation like SQL"""
        
        records = [data] if isinstance(data, dict) else data or []
        if not isinstance(records, list):
            return []
        
        group_fields = [group_by] if isinstance(group_by, str) else group_by
        
        # Group records
        groups = defaultdict(list)
        for record in records:
            group_key = tuple(record.get(field) for field in group_fields)
            groups[group_key].append(record)
        
        # Apply aggregation
        results = []
        for group_key, group_records in groups.items():
            result = {}
            for i, field in enumerate(group_fields):
                result[field] = group_key[i]
            
            if operation == "count":
                result["count"] = len(group_records)
            elif operation in ["sum", "avg", "min", "max"] and target_field:
                values = [r.get(target_field, 0) for r in group_records if target_field in r]
                if values:
                    if operation == "sum":
                        result[f"sum_{target_field}"] = sum(values)
                    elif operation == "avg":
                        result[f"avg_{target_field}"] = sum(values) / len(values)
                    elif operation == "min":
                        result[f"min_{target_field}"] = min(values)
                    elif operation == "max":
                        result[f"max_{target_field}"] = max(values)
            
            results.append(result)
        
        return sorted(results, key=lambda x: json.dumps(canonicalize(x), sort_keys=True))

    @staticmethod
    def union(left_data: Union[dict, List[dict]], right_data: Union[dict, List[dict]]) -> List[dict]:
        """∪ - Union operation like SQL UNION"""
        left_records = [left_data] if isinstance(left_data, dict) else left_data or []
        right_records = [right_data] if isinstance(right_data, dict) else right_data or []
        
        # Use set to eliminate duplicates
        all_records = []
        seen_hashes = set()
        
        for record in (left_records + right_records):
            if isinstance(record, dict):
                record_hash = sha3_256_hex(json.dumps(canonicalize(record), sort_keys=True))
                if record_hash not in seen_hashes:
                    seen_hashes.add(record_hash)
                    all_records.append(record)
        
        return sorted(all_records, key=lambda x: json.dumps(canonicalize(x), sort_keys=True))
    
    @staticmethod
    def difference(left_data: Union[dict, List[dict]], right_data: Union[dict, List[dict]]) -> List[dict]:
        """− - Difference operation like SQL EXCEPT"""
        left_records = [left_data] if isinstance(left_data, dict) else left_data or []
        right_records = [right_data] if isinstance(right_data, dict) else right_data or []
        
        # Build set of right record hashes
        right_hashes = set()
        for record in right_records:
            if isinstance(record, dict):
                record_hash = sha3_256_hex(json.dumps(canonicalize(record), sort_keys=True))
                right_hashes.add(record_hash)
        
        # Return left records not in right
        results = []
        for record in left_records:
            if isinstance(record, dict):
                record_hash = sha3_256_hex(json.dumps(canonicalize(record), sort_keys=True))
                if record_hash not in right_hashes:
                    results.append(record)
        
        return sorted(results, key=lambda x: json.dumps(canonicalize(x), sort_keys=True))

# ============================================================================
# ENHANCED RA OPERATION DISPATCHER
# ============================================================================

def apply_ra_operation(data: Union[dict, List[dict]], operation: Dict[str, Any]) -> Union[dict, List[dict]]:
    """Apply a single RA operation to data with enhanced semi/anti-join support"""
    ra = RelationalAlgebra()
    
    if 'select' in operation:
        return ra.select(data, operation['select'])
    
    elif 'project' in operation:
        return ra.project(data, operation['project'])
    
    elif 'join' in operation:
        join_config = operation['join']
        # Support both 'with' (inline) and 'using' (structure registry) patterns
        if 'with' in join_config:
            right_data = join_config['with']
            on_field = join_config['on']
            join_type = join_config.get('type', 'inner')
            return ra.join(data, right_data, on_field, join_type)
        elif 'using' in join_config:
            # Structure-backed join - will be handled by calling code
            raise ValueError("Structure-backed join requires registry context")
        else:
            raise ValueError("Join operation requires either 'with' (inline data) or 'using' (structure)")
    
    elif 'exists_in' in operation:
        exists_config = operation['exists_in']
        field = exists_config['field']
        if 'with' in exists_config:
            reference_set = exists_config['with']
            return ra.exists_in(data, field, reference_set)
        elif 'using' in exists_config:
            # Structure-backed exists_in - will be handled by calling code
            raise ValueError("Structure-backed exists_in requires registry context")
        else:
            raise ValueError("exists_in operation requires either 'with' or 'using'")
    
    elif 'not_exists_in' in operation:
        not_exists_config = operation['not_exists_in']
        field = not_exists_config['field']
        if 'with' in not_exists_config:
            reference_set = not_exists_config['with']
            return ra.not_exists_in(data, field, reference_set)
        elif 'using' in not_exists_config:
            # Structure-backed not_exists_in - will be handled by calling code  
            raise ValueError("Structure-backed not_exists_in requires registry context")
        else:
            raise ValueError("not_exists_in operation requires either 'with' or 'using'")
    
    elif 'aggregate' in operation:
        agg_config = operation['aggregate']
        group_by = agg_config.get('by', [])
        op = agg_config.get('op', 'count')
        target = agg_config.get('field')
        return ra.aggregate(data, group_by, op, target)
    
    elif 'union' in operation:
        union_config = operation['union']
        if 'with' in union_config:
            return ra.union(data, union_config['with'])
        else:
            raise ValueError("Union operation requires 'with' parameter")
    
    elif 'difference' in operation:
        diff_config = operation['difference']
        if 'with' in diff_config:
            return ra.difference(data, diff_config['with'])
        elif 'using' in diff_config:
            # Structure-backed difference - will be handled by calling code
            raise ValueError("Structure-backed difference requires registry context")
        else:
            raise ValueError("Difference operation requires either 'with' or 'using'")
    
    else:
        raise ValueError(f"Unknown RA operation: {list(operation.keys())}")

def is_ra_operation(step: Dict[str, Any]) -> bool:
    """Check if a step contains RA operations"""
    ra_operations = {'select', 'project', 'join', 'aggregate', 'union', 'difference', 'exists_in', 'not_exists_in'}
    return any(op in step for op in ra_operations)

def extract_ra_operations(step: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract RA operations from a step"""
    ra_operations = {'select', 'project', 'join', 'aggregate', 'union', 'difference', 'exists_in', 'not_exists_in'}
    operations = []
    
    for op in ra_operations:
        if op in step:
            operations.append({op: step[op]})
    
    return operations

def apply_ra_pipeline(data: Union[dict, List[dict]], operations: List[Dict[str, Any]]) -> Union[dict, List[dict]]:
    """Apply a sequence of RA operations"""
    current_data = data
    
    for operation in operations:
        current_data = apply_ra_operation(current_data, operation)
    
    return current_data

def validate_ra_operation(operation: Dict[str, Any], registry=None) -> List[str]:
    """Validate RA operation configuration and return error messages"""
    errors = []
    
    if 'join' in operation:
        join_config = operation['join']
        if 'using' in join_config:
            if not registry:
                errors.append("Join with 'using' requires structure registry")
            else:
                structure_name = join_config['using']
                if not registry.exists(structure_name):
                    errors.append(f"Join references unknown structure: {structure_name}")
                else:
                    structure = registry.get(structure_name)
                    if structure.to_dict()['type'] != 'hashmap':
                        errors.append(f"Join requires hashmap, but {structure_name} is {structure.to_dict()['type']}")
                    elif 'on' in join_config:
                        expected_key = getattr(structure, 'key_field', None)
                        if expected_key and join_config['on'] != expected_key:
                            errors.append(f"Join key mismatch: using '{join_config['on']}' but structure expects '{expected_key}'")
        elif 'with' not in join_config:
            errors.append("Join requires either 'with' (inline data) or 'using' (structure)")
        
        if 'on' not in join_config:
            errors.append("Join requires 'on' field specification")
    
    # Add similar validation for other operations that support 'using'
    for op_name in ['exists_in', 'not_exists_in', 'difference']:
        if op_name in operation:
            op_config = operation[op_name]
            if 'using' in op_config:
                if not registry:
                    errors.append(f"{op_name} with 'using' requires structure registry")
                else:
                    structure_name = op_config['using']
                    if not registry.exists(structure_name):
                        errors.append(f"{op_name} references unknown structure: {structure_name}")
                    else:
                        structure = registry.get(structure_name)
                        if structure.to_dict()['type'] != 'set':
                            errors.append(f"{op_name} requires set, but {structure_name} is {structure.to_dict()['type']}")
            elif 'with' not in op_config:
                errors.append(f"{op_name} requires either 'with' or 'using'")
            
            if 'field' not in op_config:
                errors.append(f"{op_name} requires 'field' specification")
    
    return errors

# ============================================================================
# RA AUDIT HELPERS
# ============================================================================

def generate_ra_audit(input_data: Union[dict, List[dict]], 
                      operations: List[Dict[str, Any]], 
                      output_data: Union[dict, List[dict]]) -> Dict[str, Any]:
    """Generate audit trail for RA operations"""
    
    input_canonical = canonicalize(input_data)
    output_canonical = canonicalize(output_data)
    operations_canonical = canonicalize(operations)
    
    return {
        'ra_operations': operations,
        'operations_count': len(operations),
        'input_hash': sha3_256_hex(json.dumps(input_canonical, sort_keys=True)),
        'output_hash': sha3_256_hex(json.dumps(output_canonical, sort_keys=True)),
        'operations_hash': sha3_256_hex(json.dumps(operations_canonical, sort_keys=True))
    }

# ============================================================================
# DEMO AND TESTING
# ============================================================================

if __name__ == "__main__":
    print("🔍 AXIS-RA: Enhanced Relational Algebra for JSON")
    print("Added semi-join (exists_in) and anti-join (not_exists_in)\n")
    
    # Sample data
    users = [
        {"user_id": "u1", "name": "Alice", "age": 25, "dept": "eng", "active": True},
        {"user_id": "u2", "name": "Bob", "age": 17, "dept": "sales", "active": False},
        {"user_id": "u3", "name": "Charlie", "age": 30, "dept": "eng", "active": True}
    ]
    
    admin_list = [
        {"user_id": "u1", "approved": True},
        {"user_id": "u3", "approved": True}
    ]
    
    blocked_users = ["u2", "u4"]
    
    print(f"Input users: {json.dumps(users, indent=2)}")
    print(f"Admin list: {json.dumps(admin_list, indent=2)}")
    print(f"Blocked users: {blocked_users}\n")
    
    ra = RelationalAlgebra()
    
    # Demo new semi-join operation
    print("🔍 Semi-join (exists_in): Keep users in admin list")
    admins = ra.exists_in(users, "user_id", admin_list)
    print(f"{json.dumps(admins, indent=2)}\n")
    
    # Demo new anti-join operation
    print("🚫 Anti-join (not_exists_in): Keep users NOT in blocked list")
    non_blocked = ra.not_exists_in(users, "user_id", blocked_users)
    print(f"{json.dumps(non_blocked, indent=2)}\n")
    
    # Demo complex pipeline with new operations
    print("🔄 Complex pipeline: active AND admin AND not blocked")
    pipeline_ops = [
        {"select": "active == True"},
        {"exists_in": {"field": "user_id", "with": admin_list}},
        {"not_exists_in": {"field": "user_id", "with": blocked_users}},
        {"project": ["name", "dept"]}
    ]
    
    pipeline_result = apply_ra_pipeline(users, pipeline_ops)
    print(f"{json.dumps(pipeline_result, indent=2)}")
    
    # Generate audit
    audit = generate_ra_audit(users, pipeline_ops, pipeline_result)
    print(f"\nAudit: {json.dumps(audit, indent=2)}")
