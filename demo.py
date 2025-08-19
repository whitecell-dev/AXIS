#!/usr/bin/env python3
"""
AXIS Demo - React for Deterministic Reasoning
Shows core functionality in ~50 lines
"""

import json
from axis import RuleEngine, validate, quick_validate

def main():
    print("🚀 AXIS: React for Deterministic Reasoning\n")
    
    # 1. Simple validation
    print("1. Type Validation:")
    data = {"name": "Alice", "age": "25"}  # age as string
    is_valid, errors = validate(data, {"name": "str", "age": "int"})
    print(f"   Before: {data}")
    print(f"   Valid: {is_valid}, After: {data}\n")  # age coerced to int
    
    # 2. Rule engine with business logic
    print("2. Rule Engine:")
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
    
    # Test cases
    test_cases = [
        {"age": 25, "email": "alice@example.com", "role": "admin"},
        {"age": 17, "email": "bob@example.com", "role": "user"},
        {"age": 30, "role": "editor"}  # missing email
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        result = engine.run(test_data)
        clean_result = {k: v for k, v in result.items() if k != '_audit'}
        
        print(f"   Test {i}: {test_data}")
        print(f"   Result: {json.dumps(clean_result, indent=10)}")
        print(f"   Hash: {result['_audit']['ir_hash'][:16]}...\n")
    
    # 3. Show cryptographic verification
    print("3. Cryptographic Verification:")
    print(f"   Component: {engine.component_name}")
    print(f"   Rules: {len(engine.rules)}")
    print(f"   IR Hash: {engine.ir_hash}")
    print("   ✓ Same input + same rules = identical hash across all platforms\n")
    
    # 4. CLI usage
    print("4. CLI Usage:")
    print("   axis run user_rules.yaml '{\"age\": 25, \"email\": \"test@example.com\"}'")
    print("   axis validate user_rules.yaml")
    print("   axis hash user_rules.yaml")
    print("   axis test user_rules.yaml test_vectors.json\n")
    
    print("🎯 AXIS makes computational trust as simple as `git commit`")

if __name__ == "__main__":
    main()
