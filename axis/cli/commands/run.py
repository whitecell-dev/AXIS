#!/usr/bin/env python3
"""
Run command - execute rules against input data
"""

import json
import sys
from ...engine.rule_engine import RuleEngine

def run_command(args):
    """Execute axis run command"""
    if not args.input:
        print("Error: input required for 'run' command", file=sys.stderr)
        sys.exit(1)
    
    # Load input data
    if args.input.startswith("@"):
        # Load from file
        with open(args.input[1:], 'r') as f:
            input_data = json.load(f)
    else:
        # Parse JSON string
        input_data = json.loads(args.input)
    
    # Run rules
    engine = RuleEngine(args.rules)
    result = engine.run(input_data)
    
    # Format output
    output = json.dumps(result, indent=2)
    
    # Write result
    if args.output:
        with open(args.output, 'w') as f:
            f.write(output)
        print(f"Result written to {args.output}")
    else:
        print(output)
