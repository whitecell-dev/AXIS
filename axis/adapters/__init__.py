"""
Adapter layer - controlled I/O boundaries
Keeps side effects isolated from pure rule logic
"""

from .database import DatabaseAdapter, SQLiteAdapter
from .http import HTTPAdapter

__all__ = [
    "DatabaseAdapter",
    "SQLiteAdapter", 
    "HTTPAdapter"
]
