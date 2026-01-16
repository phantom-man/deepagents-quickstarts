
import sys
import os

sys.path.insert(0, os.path.dirname(os.getcwd())) # Assuming run from DeepAgents
print(f"Path: {sys.path[0]}")

try:
    print("Importing Confidence Agent...")
    from DeepAgents.CommercialAgents.confidence_agent import agent
    print("Success importing Confidence Agent")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
