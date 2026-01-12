
import sys
import os
import traceback
import logging

# Configure logging to see HubManager output
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

print("Current CWD:", os.getcwd())
# Simulate the fix
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    print("⏳ Importing graph_app...")
    import graph_app
    print("\nSUCCESS: Graph imported successfully!")
    print("Graph object:", graph_app.graph)
except Exception:
    print("\nFAILURE: Could not import graph.")
    traceback.print_exc()
