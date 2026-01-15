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

# Load Env for API KEY
load_dotenv()

def inspect_langsmith(limit: int = 10, filter_runs: bool = True):
    """
    Lists recent threads and inspects their runs.
    """
    client = Client()
    
    print(f"\n🔍 Inspecting LangSmith (Project: {os.getenv('LANGCHAIN_PROJECT', 'default')})")
    print(f"   Listing last {limit} threads...")

    try:
        # List threads (most recent first by default)
        threads = list(client.list_threads(limit=limit))
        if not threads:
            print("⚠️ No threads found.")
            return

        for i, thread in enumerate(threads):
            print(f"\n{'='*60}")
            print(f"THREAD [{i+1}/{len(threads)}]: {thread.id}")
            print(f"Created: {thread.created_at}")
            print(f"Metadata: {thread.metadata}")
            print(f"{'='*60}")

            # Fetch runs for this thread
            runs = list(client.list_runs(thread_id=thread.id))
            if not runs:
                print("  (No runs in this thread)")
                continue

            # Sort runs by time (oldest first to tell the story, or newest?)
            # Usually list_runs returns newest first. Let's reverse for chronological replay.
            runs.reverse()

            for run in runs:
                # If we only want LLM runs and this isn't one, skip?
                # The user asked to see "sub detail of each run".
                
                print(f"\n  ⏱️  Run: {run.name} ({run.run_type})")
                print(f"      ID: {run.id}")
                print(f"      Status: {run.status}")
                
                if run.error:
                    print(f"      ❌ ERROR: {run.error}")

                duration = "N/A"
                if run.end_time and run.start_time:
                    duration = f"{(run.end_time - run.start_time).total_seconds():.2f}s"
                print(f"      Duration: {duration}")
                
                # Show Inputs/Outputs for interesting types
                if filter_runs and run.run_type not in ["llm", "chain", "tool"]:
                    continue

                if run.inputs:
                    print(f"      📥 Inputs: {str(run.inputs)[:200]}..." if len(str(run.inputs)) > 200 else f"      📥 Inputs: {run.inputs}")
                
                if run.outputs:
                    # Truncate large outputs for readability
                    out_str = str(run.outputs)
                    display_out = out_str[:300] + "..." if len(out_str) > 300 else out_str
                    print(f"      📤 Outputs: {display_out}")
                
                # If LLM, try to get more detail?
                # client.list_runs returns Run objects which usually have inputs/outputs populated.
                # read_run might get more, but usually list_runs is enough.

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
