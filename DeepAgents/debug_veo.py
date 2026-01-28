import google.auth
from google import genai

# Hardcoded details from our findings
PROJECT_ID = "crafty-hook-483415-b3"
LOCATION = "us-central1"
MODEL_ID = "veo-3.1-fast-generate-001"

print("--- Debugging Veo Generation ---")
print(f"Target Project: {PROJECT_ID}")
print(f"Target Location: {LOCATION}")

# 1. Verify Credentials
try:
    credentials, project = google.auth.default()
    print(f"Credentials obtained: {type(credentials)}")
    print(f"Default Project from Auth: {project}")
    print(
        f"Quota Project in Creds: {getattr(credentials, 'quota_project_id', 'Not Set')}"
    )
except Exception as e:
    print(f"Credential Error: {e}")

# 2. Try Generation
try:
    client = genai.Client(vertexai=True, project=PROJECT_ID, location=LOCATION)

    print(f"Requesting video from {MODEL_ID}...")
    response = client.models.generate_content(
        model=MODEL_ID,
        contents="A simple red ball bouncing on a white floor",
        config={"response_mime_type": "video/mp4"},
    )
    print("Response received!")
    if response.candidates:
        print("Candidate found.")
    else:
        print("No candidates.")

except Exception as e:
    print(f"GENERATION ERROR: {e}")
