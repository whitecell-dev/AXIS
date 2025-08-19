# calyx_fastapi.py
"""FastAPI integration for CALYX rules"""
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from calyx import RuleEngine
from typing import Dict, Any
import json

class CalyxMiddleware:
    def __init__(self, yaml_path: str):
        self.engine = RuleEngine(yaml_path)
    
    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        result = self.engine.run(data)
        if result.get('errors'):
            raise HTTPException(status_code=400, detail=result['errors'])
        return result

def create_calyx_dependency(yaml_path: str):
    """Create a FastAPI dependency for CALYX rule validation"""
    middleware = CalyxMiddleware(yaml_path)
    
    def calyx_validator(data: dict) -> dict:
        return middleware.validate(data)
    
    return calyx_validator

# Example FastAPI usage:
"""
from calyx_fastapi import create_calyx_dependency

user_validator = create_calyx_dependency('user_rules.yaml')

@app.post("/users")
async def create_user(user_data: dict, validated: dict = Depends(user_validator)):
    return {"user": validated, "status": "created"}
"""

