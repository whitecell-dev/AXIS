#!/usr/bin/env python3
"""
HTTP adapter - controlled network I/O boundary
Simple REST client using urllib (no external dependencies)
"""

import json
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional

class HTTPAdapter:
    """Simple HTTP client adapter - pure Python stdlib"""
    
    def __init__(self, base_url: str, default_headers: Dict[str, str] = None):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {
            'Content-Type': 'application/json',
            'User-Agent': 'AXIS-HTTPAdapter/1.0'
        }
    
    def get(self, endpoint: str, params: Dict[str, Any] = None) -> Dict[str, Any]:
        """GET request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        if params:
            query_string = urllib.parse.urlencode(params)
            url = f"{url}?{query_string}"
        
        req = urllib.request.Request(url, headers=self.default_headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")
    
    def post(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """POST request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        json_data = json.dumps(data or {}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=self.default_headers)
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")
    
    def put(self, endpoint: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
        """PUT request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        json_data = json.dumps(data or {}).encode('utf-8')
        req = urllib.request.Request(url, data=json_data, headers=self.default_headers)
        req.get_method = lambda: 'PUT'
        
        try:
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode())
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")
    
    def delete(self, endpoint: str) -> bool:
        """DELETE request"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        req = urllib.request.Request(url, headers=self.default_headers)
        req.get_method = lambda: 'DELETE'
        
        try:
            with urllib.request.urlopen(req) as response:
                return response.status < 400
        except urllib.error.HTTPError as e:
            raise Exception(f"HTTP {e.code}: {e.reason}")
