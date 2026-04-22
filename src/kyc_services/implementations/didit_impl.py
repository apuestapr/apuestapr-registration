import requests
import json
import logging
from typing import Dict, Any
from src.config import Config

logger = logging.getLogger(__name__)

def get_api_key() -> str:
    """Get the Didit API key from config"""
    api_key = Config.DIDIT_API_KEY
    if not api_key:
        raise ValueError("Didit API key not configured")
    return api_key

def call_didit_api(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Make an API call to Didit"""
    url = 'https://verification.didit.me/v3/session/'
    
    headers = {
        "x-api-key": get_api_key(),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30  # 30 second timeout
        )
        
        # Log response for debugging
        logger.debug(f"Didit API response: {response.status_code}")
        
        # Parse and return the response
        if response.status_code in (200, 201):
            return response.json()
        else:
            logger.error(f"Didit API error: {response.status_code} - {response.text}")
            return {"error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        logger.exception(f"Exception making Didit API call: {e}")
        return {"error": str(e)}
