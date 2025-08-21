#!/usr/bin/env python3
"""
Test command - run golden vector tests for verification
"""

import json
from ...testing.test_runner import GoldenVectorRunner

def test_command(args):
    """Execute axis test command"""
    if not args.input:
        print("Error: test vectors file required")
        return
    
    # Run golden vector tests
    runner = GoldenVectorRunner(args.rules)
    results = runner.run_tests(args.input)
    
    print(f"Tests: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    if results['failures']:
        print("\nFailures:")
        for failure in results['failures']:
            if 'error' in failure:
                print(f"  - Test {failure['test_index']}: {failure['error']}")
            else:
                print(f"  - Test {failure['test_index']}: Output mismatch")
                if 'description' in failure:
                    print(f"    Description: {failure['description']}")
    
    if results['failed'] > 0:
        exit(1)
