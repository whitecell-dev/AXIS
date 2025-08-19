# AXIS_adapters/files.py
"""File I/O adapter patterns for AXIS"""
import json
import os
from typing import Dict, Any, List
from pathlib import Path

class FileAdapter:
    """File system adapter"""
    
    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
    
    def read_json(self, filename: str) -> Dict[str, Any]:
        """Read JSON file"""
        file_path = self.base_path / filename
        with open(file_path, 'r') as f:
            return json.load(f)
    
    def write_json(self, filename: str, data: Dict[str, Any]) -> bool:
        """Write JSON file"""
        file_path = self.base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    
    def read_text(self, filename: str) -> str:
        """Read text file"""
        file_path = self.base_path / filename
        with open(file_path, 'r') as f:
            return f.read()
    
    def write_text(self, filename: str, content: str) -> bool:
        """Write text file"""
        file_path = self.base_path / filename
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    
    def list_files(self, pattern: str = "*") -> List[str]:
        """List files matching pattern"""
        return [str(f.relative_to(self.base_path)) for f in self.base_path.glob(pattern)]
