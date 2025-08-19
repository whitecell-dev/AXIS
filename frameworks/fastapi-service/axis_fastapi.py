# AXIS_fastapi.py
"""FastAPI integration for AXIS rules"""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from AXIS import RuleEngine
from typing import Dict, Any
import json

class AXISMiddleware:
    def __init__(self, yaml_path: str):
        self.engine = RuleEngine(yaml_path)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.engine.run(data)
        if result.get('errors'):
            raise HTTPException(status_code=400, detail=result['errors'])
        return result

def create_AXIS_dependency(yaml_path: str):
    """Create a FastAPI dependency for AXIS rule validation"""
    middleware = AXISMiddleware(yaml_path)
    
    def AXIS_validator(data: dict) -> dict:
        return middleware.validate(data)
    
    return AXIS_validator

# Example FastAPI usage:
"""
from AXIS_fastapi import create_AXIS_dependency

user_validator = create_AXIS_dependency('user_rules.yaml')

@app.post("/users")
async def create_user(user_data: dict, validated: dict = Depends(user_validator)):
    return {"user": validated, "status": "created"}
"""

