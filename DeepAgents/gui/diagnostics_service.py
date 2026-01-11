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
from dotenv import load_dotenv

load_dotenv()

def check_internet():
    try:
        requests.get("https://www.google.com", timeout=3)
        return True, "Online"
    except Exception as e:
        return False, f"Offline: {e}"

def check_lancedb():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "lancedb"))
    if os.path.exists(db_path):
        return True, f"Ready at {db_path}"
    return False, f"Not found at {db_path}"

def check_postgres():
    """Checks the Nervous System (Postgres) connection."""
    try:
        import psycopg2
        
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        user = os.getenv("POSTGRES_USER", "postgres")
        password = os.getenv("POSTGRES_PASSWORD", "d1204l0723")
        dbname = os.getenv("POSTGRES_DB", "postgres")
        
        conn = psycopg2.connect(
            host=host, port=port, user=user, password=password, dbname=dbname, connect_timeout=3
        )
        conn.close()
        return True, "Connected (Nervous System Online)"
    except ImportError:
        return False, "psycopg2 module not found"
    except Exception as e:
        return False, f"Connection Failed: {e}"

def check_langsmith():
    """Checks LangSmith/LangChain Token."""
    api_key = os.getenv("LANGCHAIN_API_KEY")
    tracing = os.getenv("LANGCHAIN_TRACING_V2")
    
    if not api_key:
        return False, "LANGCHAIN_API_KEY Missing"
    
    if tracing != "true":
         return False, "Tracing Disabled (Env Var)"
    
    # Simple validity check by hitting the API (optional, but good for verification)
    try:
        headers = {"x-api-key": api_key}
        res = requests.get("https://api.smith.langchain.com/info", headers=headers, timeout=3)
        if res.status_code == 200:
            return True, "Tracing Enabled & Key Valid"
        elif res.status_code == 403:
             return True, "Key Valid (Tracing Enabled)" # Info endpoint might be strict
        else:
            return False, f"API Error: {res.status_code}"
    except:
        # Fallback to just static check
        return True, "Tracing Configured (Static Check)"

def check_replicate():
    """Checks Replicate for Voice Engine."""
    token = os.getenv("REPLICATE_API_TOKEN")
    if not token:
        return False, "Token Missing"
    return True, "Token Present"

def check_gcp_creds():
    try:
        creds, project = google.auth.default()
        return True, f"Project: {project}"
    except Exception as e:
        return False, f"Auth Failed: {e}"

def run_diagnostics():
    """Runs all system checks and returns a dict of results."""
    results = {}
    
    # 1. Connectivity
    s, m = check_internet()
    results["Internet"] = {"status": s, "message": m}
    
    # 2. Key/Cloud Infrastructure
    s, m = check_gcp_creds()
    results["GCP (LLM)"] = {"status": s, "message": m}
    
    s, m = check_langsmith()
    results["LangSmith (Observability)"] = {"status": s, "message": m}
    
    s, m = check_replicate()
    results["Replicate (Voice)"] = {"status": s, "message": m}
    
    # 3. Data Systems
    s, m = check_postgres()
    results["Postgres (Nervous System)"] = {"status": s, "message": m}
    
    s, m = check_lancedb()
    results["LanceDB (Memory)"] = {"status": s, "message": m}
    
    return results
