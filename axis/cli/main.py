#!/usr/bin/env python3
"""
AXIS CLI - React for Deterministic Reasoning
Simple commands: run, validate, hash, test, compose
"""

import argparse
import json
import sys
from pathlib import Path

# Import commands
from .commands.run import run_command
from .commands.validate import validate_command
from .commands.test import test_command
from .commands.compose import compose_command

def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="AXIS: React for Deterministic Reasoning",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  axis run rules.yaml '{"age": 25, "email": "test@example.com"}'
  axis validate rules.yaml
  axis hash rules.yaml
  axis test rules.yaml test_vectors.json
  axis compose main.yaml --output composed.yaml
        """
    )
    
    parser.add_argument("command", 
                       choices=['run', 'validate', 'hash', 'test', 'compose'], 
                       help="Command to execute")
    parser.add_argument("rules", help="Path to YAML rules file")
    parser.add_argument("input", nargs='?', help="JSON input or second file")
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--debug", action='store_true', help="Enable debug output")
    
    args = parser.parse_args()
    
    # Set debug mode
    if args.debug:
        import os
        os.environ['AXIS_DEBUG'] = '1'
    
    try:
        if args.command == 'run':
            run_command(args)
        elif args.command == 'validate':
            validate_command(args)
        elif args.command == 'hash':
            from ..engine.rule_engine import RuleEngine
            engine = RuleEngine(args.rules)
            print(engine.ir_hash)
        elif args.command == 'test':
            test_command(args)
        elif args.command == 'compose':
            compose_command(args)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
