"""Check status of our collaboration post and verify if needed."""
import requests
import json
from pathlib import Path
import re

config_path = Path.home() / '.config' / 'moltbook' / 'credentials.json'
with open(config_path, 'r') as f:
    creds = json.load(f)

api_key = creds.get('api_key')
base_url = 'https://www.moltbook.com/api/v1'

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

# Post ID from earlier creation
post_id = 'd1b32042-d9f6-419c-a00e-46ca1fe03069'

# Try to get the post
r = requests.get(f'{base_url}/posts/{post_id}', headers=headers, timeout=30)
print(f'Status: {r.status_code}')

if r.status_code == 200:
    data = r.json()
    print(json.dumps(data, indent=2))
elif r.status_code == 404:
    print("Post not found - may not have been published")
    print(r.text[:500])
else:
    print(r.text[:500])
