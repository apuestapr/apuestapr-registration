import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv('.env')

from src.kyc_services.implementations import didit_impl
from src.config import Config

payload = {
    "workflow_id": Config.DIDIT_WORKFLOW_ID,
    "callback": "https://staging.register.apuestapr.com/kyc/didit-callback",
    "vendor_data": "test_123"
}

print(f"Calling Didit with API Key: {Config.DIDIT_API_KEY[:5]}...")
print(f"Workflow ID: {Config.DIDIT_WORKFLOW_ID}")

res = didit_impl.call_didit_api(payload)
print(json.dumps(res, indent=2))
