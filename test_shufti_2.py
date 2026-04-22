import os
import sys
import json
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv('.env')

from src.models.registration import Registration
from src.kyc_services.shufti_service import ShuftiService

# Find the most recent registration
regs = Registration.find(sort="-started_at", limit=1)
if regs:
    reg = regs[0]
    print(f"Testing with Registration: {reg.id} - {reg.email}")
    # Force test Shufti
    reg.kyc_provider = 'shufti'
    # Clear the URL so it generates a new one
    reg.shufti_callback_payload = None
    reg.shufti_reference = ''
    svc = ShuftiService()
    url = svc.generate_client_token(reg)
    print(f"Generated Shufti URL: {url}")
else:
    print("No registrations found.")
