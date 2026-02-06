"""Debug heartbeat response shapes."""
import requests
import json
from pathlib import Path

config_path = Path.home() / ".config" / "moltbook" / "credentials.json"
with open(config_path, "r") as f:
    creds = json.load(f)

api_key = creds["api_key"]
base_url = "https://www.moltbook.com/api/v1"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

# Check agent status
r = requests.get(f"{base_url}/agents/me", headers=headers)
print("=== /agents/me ===")
print(f"Status: {r.status_code}")
print(json.dumps(r.json(), indent=2))
print()

# Check DMs
r2 = requests.get(f"{base_url}/agents/dm/requests", headers=headers)
print("=== /agents/dm/requests ===")
print(f"Status: {r2.status_code}")
if r2.status_code == 200:
    print(json.dumps(r2.json(), indent=2))
else:
    print(r2.text[:200])
