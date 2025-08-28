# setup.py
#!/usr/bin/env python3
"""
Legacy setup.py for AXIS - defers to pyproject.toml

This file exists for compatibility with tools that haven't fully adopted PEP 621.
All configuration is in pyproject.toml.
"""

from setuptools import setup

if __name__ == "__main__":
    setup()
