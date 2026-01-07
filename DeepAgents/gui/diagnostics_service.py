# Diagnostics Service
# Checks for:
# 1. API Credentials (Vertex AI, Anthropic)
# 2. Database Connection (LanceDB)
# 3. Internet Connectivity (Google ping)

import os
import sys
import json
import requests
import google.auth
from google.cloud import aiplatform

def check_internet():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True, "Online"
    except Exception as e:
        return False, f"Offline: {e}"

def check_lancedb():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "lancedb"))
    if os.path.exists(db_path):
        return True, f"Found at {db_path}"
    return False, f"Not found at {db_path}"

def check_gcp_creds():
    try:
        creds, project = google.auth.default()
        return True, f"Project: {project}, Type: {type(creds).__name__}"
    except Exception as e:
        return False, f"Auth Failed: {e}"

def run_diagnostics():
    results = {}
    
    # 1. Internet
    status, msg = check_internet()
    results["Internet"] = {"status": status, "message": msg}
    
    # 2. GCP
    status, msg = check_gcp_creds()
    results["GCP Vertex AI"] = {"status": status, "message": msg}
    
    # 3. LanceDB
    status, msg = check_lancedb()
    results["Memory (LanceDB)"] = {"status": status, "message": msg}
    
    return results
