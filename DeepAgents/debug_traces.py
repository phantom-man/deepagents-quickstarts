import datetime

from dotenv import load_dotenv
from langsmith import Client

load_dotenv("DeepAgents/.env")


def inspect_traces():
    print("🔍 Inspecting LangSmith Traces for recent success...")
    try:
        client = Client()
        # List runs from the last 24 hours
        start_time = datetime.datetime.now() - datetime.timedelta(hours=24)
        runs = list(
            client.list_runs(
                project_name="DeepAgents",
                start_time=start_time,
                limit=5,
                execution_order=1,  # Descending
            )
        )

        print(f"Found {len(runs)} recent runs.")

        for run in runs:
            print(f"\n--- Run: {run.name} ({run.status}) ---")
            print(f"Time: {run.start_time}")
            print(f"Type: {run.run_type}")
            if run.inputs:
                print(f"Inputs keys: {list(run.inputs.keys())}")
            # Try to see if any prompt information is in the run extras or tags
            if run.tags:
                print(f"Tags: {run.tags}")

    except Exception as e:
        print(f"❌ Failed to inspect traces: {e}")


if __name__ == "__main__":
    inspect_traces()
