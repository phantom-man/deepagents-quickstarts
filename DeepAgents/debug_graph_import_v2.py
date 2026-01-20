
import sys
import os

# Adjust path similarly to the graphs
current_dir = os.getcwd() # Should be DeepAgents
repo_root = os.path.dirname(current_dir)
sys.path.insert(0, repo_root)

print(f"DEBUG: sys.path[0] = {sys.path[0]}")

try:
    print("DEBUG: Importing graphs.agency_graph...")
    from DeepAgents.graphs import agency_graph
    print("DEBUG: Successfully imported agency_graph")
    
    print("DEBUG: Importing graph_app...")
    print("DEBUG: Successfully imported graph_app")
    
    # Try to load the graphs
    print("DEBUG: Loading agency graph app...")
    app = agency_graph.app
    print(f"DEBUG: Agency graph loaded: {app}")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Test complete.")
