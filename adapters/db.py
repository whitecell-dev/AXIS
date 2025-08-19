# AXIS_adapters/database.py
"""Database adapter patterns for AXIS"""
import json
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod

class DatabaseAdapter(ABC):
    """Abstract base for database adapters"""
    
    @abstractmethod
    def save(self, table: str, data: Dict[str, Any]) -> Any:
        pass
    
    @abstractmethod
    def find(self, table: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def update(self, table: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        pass

class SQLiteAdapter(DatabaseAdapter):
    """SQLite adapter implementation"""
    
    def __init__(self, db_path: str):
        import sqlite3
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # Dict-like rows
    
    def save(self, table: str, data: Dict[str, Any]) -> Any:
        """Insert data into table"""
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        
        query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
        cursor = self.conn.execute(query, list(data.values()))
        self.conn.commit()
        return cursor.lastrowid
    
    def find(self, table: str, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find records matching query"""
        if not query:
            sql = f"SELECT * FROM {table}"
            params = []
        else:
            conditions = ' AND '.join([f"{k} = ?" for k in query.keys()])
            sql = f"SELECT * FROM {table} WHERE {conditions}"
            params = list(query.values())
        
        cursor = self.conn.execute(sql, params)
        return [dict(row) for row in cursor.fetchall()]
    
    def update(self, table: str, query: Dict[str, Any], data: Dict[str, Any]) -> bool:
        """Update records matching query"""
        set_clause = ', '.join([f"{k} = ?" for k in data.keys()])
        where_clause = ' AND '.join([f"{k} = ?" for k in query.keys()])
        
        sql = f"UPDATE {table} SET {set_clause} WHERE {where_clause}"
        params = list(data.values()) + list(query.values())
        
        cursor = self.conn.execute(sql, params)
        self.conn.commit()
        return cursor.rowcount > 0
