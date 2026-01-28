import json
import os

import google.auth
from google import genai

# Hardcoded details
PROJECT_ID = "crafty-hook-483415-b3"
LOCATION = "us-central1"
MODEL_ID = "veo-3.1-fast-generate-001"

# The path the user mentioned
ADC_PATH = os.path.expanduser(
    "~\\AppData\\Roaming\\gcloud\\application_default_credentials.json"
)

print("--- Credential & Quota Diagnostics ---")

# 1. Check Environment Variable
env_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
print(
    f"1. GOOGLE_APPLICATION_CREDENTIALS env var: {env_creds if env_creds else 'Not Set (Correct for ADC)'}"
)

# 2. Check ADC File existence and content
print(f"2. Checking ADC File at: {ADC_PATH}")
if os.path.exists(ADC_PATH):
    print("   [OK] File exists.")
    try:
        with open(ADC_PATH, "r") as f:
            data = json.load(f)
            print(f"   [INFO] Client Email: {data.get('client_email', 'N/A')}")
            print(
                f"   [INFO] Quota Project in JSON: {data.get('quota_project_id', 'N/A')}"
            )
            # Do not print private key or refresh token
    except Exception as e:
        print(f"   [ERROR] Could not read file: {e}")
else:
    print("   [WARNING] ADC File not found at default location.")

# 3. Authenticate using google.auth.default()
print("\n3. Testing google.auth.default() Resolution...")
try:
    credentials, project = google.auth.default()
    print(f"   [OK] Credentials Object: {type(credentials)}")
    print(f"   [OK] Resolved Project: {project}")

    # Check if these credentials match the file
    if hasattr(credentials, "info"):  # Service Account
        print(f"   [INFO] Service Account Email: {credentials.service_account_email}")
    elif hasattr(credentials, "client_id"):  # User Credentials
        print(
            f"   [INFO] User Client ID matches ADC? {'Yes' if data.get('client_id') == credentials.client_id else 'No'}"
        )

except Exception as e:
    print(f"   [ERROR] Auth failed: {e}")

# 4. Attempt Generation
print(f"\n4. Attempting Generation with Project: {PROJECT_ID}")
try:
    # Explicitly forcing the project ID to ensure we use the one with (hoped) quota
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    response = client.models.generate_content(
        model=MODEL_ID,
        contents="A simple red ball bouncing on a white floor",
        config={"response_mime_type": "video/mp4"},
    )
    print("✅ SUCCESS! Video content generated.")

except Exception as e:
    print(f"❌ GENERATION FAILED: {e}")
