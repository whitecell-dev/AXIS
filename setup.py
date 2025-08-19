#!/usr/bin/env python3
"""
AXIS setup script
React for Deterministic Reasoning
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="axis-py",
    version="1.0.0",
    author="AXIS Team",
    author_email="team@axis.dev",
    description="React for Deterministic Reasoning",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/whitecell-dev/axis-py",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.8",
    install_requires=[
        # Core has no dependencies - pure Python stdlib
    ],
    extras_require={
        "yaml": ["pyyaml>=6.0"],
        "web": ["flask>=2.0", "fastapi>=0.68"],
        "dev": ["pytest>=6.0", "black", "mypy"],
        "all": ["pyyaml>=6.0", "flask>=2.0", "fastapi>=0.68", "pytest>=6.0"]
    },
    entry_points={
        "console_scripts": [
            "axis=axis.cli.main:main",
        ],
    },
    keywords="rules engine, validation, business logic, functional programming, deterministic",
    project_urls={
        "Bug Reports": "https://github.com/whitecell-dev/axis-py/issues",
        "Source": "https://github.com/whitecell-dev/axis-py",
        "Documentation": "https://axis-docs.example.com",
    }
)
