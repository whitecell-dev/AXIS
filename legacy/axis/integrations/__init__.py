"""
Framework integrations for popular web frameworks
Simple decorator/dependency patterns
"""

# Lazy imports to avoid requiring frameworks
__all__ = ["with_axis_rules", "create_axis_dependency"]

def with_axis_rules(yaml_path: str):
    """Flask decorator - lazy import"""
    from .flask import with_axis_rules as _impl
    return _impl(yaml_path)

def create_axis_dependency(yaml_path: str):
    """FastAPI dependency - lazy import"""
    from .fastapi import create_axis_dependency as _impl
    return _impl(yaml_path)
