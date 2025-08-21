#!/usr/bin/env python3
"""
AXIS: React for Deterministic Reasoning
Setup script for backward compatibility and development

This setup.py exists for:
1. Backward compatibility with older pip versions
2. Development installation (pip install -e .)
3. CI/CD systems that expect setup.py

The canonical build configuration is in pyproject.toml
"""

import sys
from pathlib import Path
from setuptools import setup

# Ensure Python 3.8+
if sys.version_info < (3, 8):
    sys.exit("AXIS requires Python 3.8 or higher")

# Read long description from README
HERE = Path(__file__).parent
long_description = (HERE / "README.md").read_text(encoding="utf-8")

# Core package info
PACKAGE_INFO = {
    "name": "axis-py",
    "version": "1.0.0",
    "description": "React for Deterministic Reasoning - Unix pipes for structured data",
    "long_description": long_description,
    "long_description_content_type": "text/markdown",
    "author": "AXIS Team",
    "author_email": "team@axis.dev",
    "url": "https://github.com/your-org/axis",
    "project_urls": {
        "Documentation": "https://axis-docs.example.com",
        "Source": "https://github.com/your-org/axis",
        "Bug Reports": "https://github.com/your-org/axis/issues",
        "Changelog": "https://github.com/your-org/axis/blob/main/CHANGELOG.md",
    },
    "license": "MIT",
    "classifiers": [
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Utilities",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
        "Environment :: Console",
    ],
    "keywords": [
        "terminal", "pipes", "json", "yaml", "functional-programming",
        "lambda-calculus", "deterministic", "hash-verification",
        "unix-tools", "structured-data", "business-logic"
    ],
    "python_requires": ">=3.8",
    "py_modules": [
        "axis_pipes",
        "axis_rules", 
        "axis_adapters",
        "demo_pipeline"
    ],
    "install_requires": [
        # Core has zero dependencies - pure Python stdlib only
        # This is a key principle of AXIS-PY philosophy
    ],
    "extras_require": {
        "yaml": [
            "pyyaml>=6.0",
        ],
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0", 
            "black>=23.0",
            "mypy>=1.0",
            "ruff>=0.1.0",
        ],
        "test": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pyyaml>=6.0",
        ],
        "docs": [
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
            "mkdocstrings[python]>=0.24.0",
        ],
        "all": [
            "pyyaml>=6.0",
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "black>=23.0", 
            "mypy>=1.0",
            "ruff>=0.1.0",
            "mkdocs>=1.5.0",
            "mkdocs-material>=9.0.0",
        ]
    },
    "entry_points": {
        "console_scripts": [
            "axis-pipes=axis_pipes:cli",
            "axis-rules=axis_rules:cli",
            "axis-adapters=axis_adapters:cli",
        ],
    },
    "package_data": {
        "": ["*.yaml", "*.yml", "*.json", "*.md"],
    },
    "include_package_data": True,
    "zip_safe": False,  # Allow inspection of installed files
}

def validate_axis_philosophy():
    """
    Validate that the package follows AXIS-PY philosophy
    - Each component should be ~150 LOC
    - Zero core dependencies
    - Pure Python stdlib only
    """
    import ast
    
    components = ["axis_pipes.py", "axis_rules.py", "axis_adapters.py"]
    
    for component in components:
        if not Path(component).exists():
            continue
            
        # Count lines of code (excluding comments and blank lines)
        with open(component, 'r') as f:
            lines = f.readlines()
        
        loc = 0
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith('#'):
                loc += 1
        
        print(f"📊 {component}: {loc} LOC")
        
        if loc > 200:
            print(f"⚠️  {component} exceeds 200 LOC limit (AXIS-PY philosophy)")
    
    # Verify zero core dependencies
    if PACKAGE_INFO["install_requires"]:
        print(f"⚠️  Core has dependencies (violates AXIS-PY philosophy)")
    else:
        print(f"✅ Zero core dependencies (follows AXIS-PY philosophy)")

def main():
    """Main setup function"""
    
    # Show AXIS philosophy info during installation
    print("🚀 AXIS: React for Deterministic Reasoning")
    print("📏 AXIS-PY Philosophy: Every line of code is a liability until proven otherwise")
    print("")
    
    # Validate philosophy compliance during development
    if "--validate" in sys.argv:
        sys.argv.remove("--validate")
        validate_axis_philosophy()
        return
    
    # Run setup
    setup(**PACKAGE_INFO)
    
    # Show post-install info
    if "install" in sys.argv:
        print("")
        print("✅ AXIS installation complete!")
        print("")
        print("🔗 Quick start:")
        print("   echo '{\"name\": \"Alice\", \"age\": \"25\"}' | axis-pipes run config.yaml")
        print("   echo '{\"age\": 25, \"role\": \"admin\"}' | axis-rules apply logic.yaml")
        print("   echo '{\"user\": \"alice\"}' | axis-adapters exec save.yaml")
        print("")
        print("📚 Documentation: https://axis-docs.example.com")
        print("🐛 Issues: https://github.com/your-org/axis/issues")
        print("")
        print("🎯 The terminal just got a nervous system for structured data!")

if __name__ == "__main__":
    main()
