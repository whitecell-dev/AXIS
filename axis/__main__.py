"""
AXIS CLI entry point

Provides unified access to all AXIS components.
"""

import sys
import argparse


def main():
   """Main CLI entry point"""
   parser = argparse.ArgumentParser(
       prog="axis",
       description="AXIS: Deterministic JSON Math Engine"
   )
   
   subparsers = parser.add_subparsers(dest="command", help="Available commands")
   
   # Add subcommands
   subparsers.add_parser("pipes", help="Run pipeline engine (axis-pipes)")
   subparsers.add_parser("rules", help="Run rule engine (axis-rules)")
   subparsers.add_parser("adapters", help="Run adapter engine (axis-adapters)")
   subparsers.add_parser("structures", help="Manage structure registry (axis-structures)")
   
   args, remaining = parser.parse_known_args()
   
   if not args.command:
       print("AXIS: Deterministic JSON Math Engine")
       print('"LLMs guess; AXIS proves."\n')
       print("Available components:")
       print("  axis pipes      - Data transformation pipelines with RA operations")
       print("  axis rules      - Logical rule engine with fixpoint iteration")  
       print("  axis adapters   - Controlled side effects with audit trails")
       print("  axis structures - Prebuilt data structure registry")
       print("")
       print("Direct usage:")
       print("  axis-pipes run config.yaml")
       print("  axis-rules apply rules.yaml")
       print("  axis-adapters exec adapters.yaml")
       print("  axis-structures materialize config.yaml")
       print("")
       print("Use 'axis <component> --help' for component-specific options.")
       return
   
   # Dispatch to appropriate module
   if args.command == "pipes":
       sys.argv = ["axis-pipes"] + remaining
       from .axis_pipes import cli
       cli()
   elif args.command == "rules":
       sys.argv = ["axis-rules"] + remaining  
       from .axis_rules import cli
       cli()
   elif args.command == "adapters":
       sys.argv = ["axis-adapters"] + remaining
       from .axis_adapters import cli
       cli()
   elif args.command == "structures":
       sys.argv = ["axis-structures"] + remaining
       from .axis_structures import cli
       cli()
   else:
       parser.print_help()
       sys.exit(1)


if __name__ == "__main__":
   main()
