import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
load_dotenv('.env')

from src.config import Config

session_id = "14af62b8-7528-42a6-a0e5-0ba5efa7a871" # from my previous test
url = f"https://verification.didit.me/v3/sessions/{session_id}/"

headers = {
    "x-api-key": Config.DIDIT_API_KEY,
    "Content-Type": "application/json"
}

print(f"Checking session {session_id}...")
res = requests.get(url, headers=headers)
print(f"Status Code: {res.status_code}")
if res.status_code == 200:
    print(json.dumps(res.json(), indent=2))
else:
    print(res.text)
