import requests
import base64
import json
import hashlib
import logging
import os
from typing import Dict, Any
from src.config import Config
from src.models.registration import Registration

logger = logging.getLogger(__name__)

def get_api_url() -> str:
    """Get the Shufti Pro API URL from config"""
    return Config.SHUFTI_API_URL or 'https://api.shuftipro.com/'

def get_auth_headers() -> Dict[str, str]:
    """Get the authorization headers for Shufti Pro API"""
    # Get credentials from config
    client_id = Config.SHUFTI_CLIENT_ID
    client_secret = Config.SHUFTI_CLIENT_SECRET
    
    if not client_id or not client_secret:
        raise ValueError("Shufti Pro credentials not configured")
    
    # Create basic auth header
    auth = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth.encode()).decode()
    
    return {
        "Authorization": f"Basic {b64_auth}", 
        "Content-Type": "application/json"
    }

def calculate_signature(response_content: str) -> str:
    """Calculate signature for verification"""
    secret_key = Config.SHUFTI_CLIENT_SECRET
    if not secret_key:
        raise ValueError("Shufti Pro secret key not configured")
        
    return hashlib.sha256(f'{response_content}{secret_key}'.encode()).hexdigest()

def call_shufti_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make an API call to Shufti Pro"""
    url = get_api_url()
    headers = get_auth_headers()
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30  # 30 second timeout
        )
        
        # Log response for debugging
        logger.debug(f"Shufti API response: {response.status_code}")
        
        # Parse and return the response
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Shufti API error: {response.status_code} - {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.exception(f"Exception making Shufti API call: {e}")
        return {"error": str(e)}