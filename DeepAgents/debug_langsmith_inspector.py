"""
LangSmith Data Inspector.
Allows inspection of Threads, Runs, and LLM Inputs/Outputs directly from the console.
Adheres strictly to the user's LangSmith environment.
"""

import os
import argparse
from datetime import datetime, timedelta
from typing import Optional

from langsmith import Client
from dotenv import load_dotenv

# Load Env for API KEY (Robust Pathing)
from pathlib import Path
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv() # Fallback

def inspect_langsmith(limit: int = 10, filter_runs: bool = True):
    """
    Lists recent threads and inspects their runs.
    """
    client = Client()
    
    print(f"\n🔍 Inspecting LangSmith (Project: {os.getenv('LANGCHAIN_PROJECT', 'default')})")
    print(f"   Listing last {limit} threads...")

    try:
        # List runs (most recent first by default) instead of threads
        # We filter for root runs (Traces) to avoid noise
        root_runs = list(client.list_runs(limit=limit, is_root=True, project_name=os.getenv('LANGCHAIN_PROJECT', 'default')))
        if not root_runs:
            print("⚠️ No runs found.")
            return

        for i, root_run in enumerate(root_runs):
            print(f"\n{'='*60}")
            print(f"TRACE [{i+1}/{len(root_runs)}]: {root_run.id}")
            print(f"Name: {root_run.name}")
            print(f"Start Time: {root_run.start_time}")
            print(f"Tags: {root_run.tags}")
            print(f"{'='*60}")

            # Print details of the root run
            print(f"  Status: {root_run.status}")
            if root_run.error:
                print(f"  ❌ ERROR: {root_run.error}")

            duration = "N/A"
            if root_run.end_time and root_run.start_time:
                duration = f"{(root_run.end_time - root_run.start_time).total_seconds():.2f}s"
            print(f"  Duration: {duration}")
            
            if root_run.inputs:
                print(f"  📥 Inputs: {str(root_run.inputs)[:200]}..." if len(str(root_run.inputs)) > 200 else f"  📥 Inputs: {root_run.inputs}")
            
            if root_run.outputs:
                out_str = str(root_run.outputs)
                display_out = out_str[:300] + "..." if len(out_str) > 300 else out_str
                print(f"  📤 Outputs: {display_out}")

    except Exception as e:
        print(f"❌ Error Inspecting LangSmith: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LangSmith Inspector")
    parser.add_argument("--limit", type=int, default=5, help="Number of threads to list")
    parser.add_argument("--all", action="store_true", help="Show all run types (not just LLM/Chain)")
    
    args = parser.parse_args()
    
    inspect_langsmith(limit=args.limit, filter_runs=not args.all)
