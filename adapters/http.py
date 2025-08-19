# calyx_adapters/http.py
"""HTTP adapter patterns for CALYX"""
import json
from typing import Dict, Any, Optional
import urllib.request
import urllib.parse
import urllib.error

class HTTPAdapter:
    """Simple HTTP client adapter"""
    
    def __init__(self, base_url: str, default_headers: Dict[str, str] = None):
        self.base_url = base_url.rstrip('/')
        self.default_headers = default_headers or {
            'Content-Type': 'application/json',
            'User-Agent': 'CALYX-HTTPAdapter/1.0'
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
