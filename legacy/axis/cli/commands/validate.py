#!/usr/bin/env python3
"""
Validate command - check rules syntax and structure
"""

from ...engine.rule_engine import RuleEngine

def validate_command(args):
    """Execute axis validate command"""
    # Load and validate rules
    engine = RuleEngine(args.rules)
    
    print(f"✓ Rules valid: {engine.component_name}")
    print(f"✓ Rule count: {len(engine.rules)}")
    print(f"✓ IR Hash: {engine.ir_hash}")
    
    # Basic rule structure check
    for i, rule in enumerate(engine.rules):
        if 'if' not in rule and 'then' not in rule and 'else' not in rule:
            print(f"⚠️  Rule {i + 1}: No condition or action found")
        elif 'then' not in rule and 'else' not in rule:
            print(f"⚠️  Rule {i + 1}: No action (then/else) specified")
    
    print("✓ Validation complete")
