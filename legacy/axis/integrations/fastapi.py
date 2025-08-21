#!/usr/bin/env python3
"""
FastAPI integration for AXIS rules
Dependency injection pattern for validation
"""

from typing import Dict, Any
from ..engine.rule_engine import RuleEngine

class AxisMiddleware:
    """FastAPI middleware for AXIS rule validation"""
    
    def __init__(self, yaml_path: str):
        self.engine = RuleEngine(yaml_path)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate data against rules"""
        result = self.engine.run(data)
        
        if result.get('errors'):
            try:
                from fastapi import HTTPException
                raise HTTPException(status_code=400, detail=result['errors'])
            except ImportError:
                raise RuntimeError("FastAPI integration requires: pip install fastapi")
        
        return result

def create_axis_dependency(yaml_path: str):
    """Create a FastAPI dependency for AXIS rule validation"""
    middleware = AxisMiddleware(yaml_path)
    
    def axis_validator(data: dict) -> dict:
        return middleware.validate(data)
    
    return axis_validator

# Example usage:
"""
from axis.integrations.fastapi import create_axis_dependency

user_validator = create_axis_dependency('user_rules.yaml')

@app.post("/users")
async def create_user(data: dict, validated: dict = Depends(user_validator)):
    return {"user": validated, "status": "created"}
"""
