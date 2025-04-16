from dotenv import load_dotenv
import os
import sys

# Explicitly specify the .flaskenv file
load_dotenv('.flaskenv')  

print("Testing environment variables:")
print(f"APP_URL = {os.getenv('APP_URL')}")
print(f"KYC_PROVIDER = {os.getenv('KYC_PROVIDER')}")
print(f"FLASK_APP = {os.getenv('FLASK_APP')}")  # This should definitely be set

# Print command line arguments to see how the script was invoked
print("\nCommand line arguments:")
for i, arg in enumerate(sys.argv):
    print(f"  {i}: {arg}")

# Print .flaskenv file contents
try:
    print("\n.flaskenv file contents:")
    with open('.flaskenv', 'r') as f:
        print(f.read())
except Exception as e:
    print(f"Error reading .flaskenv: {e}")

print("\nTry running this script with: python -m test_env") 