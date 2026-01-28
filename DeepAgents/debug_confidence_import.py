import os
import sys

sys.path.insert(0, os.path.dirname(os.getcwd()))  # Assuming run from DeepAgents
print(f"Path: {sys.path[0]}")

try:
    print("Importing Confidence Agent...")
    print("Success importing Confidence Agent")
except Exception as e:
    print(f"Error: {e}")
    import traceback

    traceback.print_exc()
