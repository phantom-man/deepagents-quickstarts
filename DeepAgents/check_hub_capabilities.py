from langsmith import Client

try:
    print("Checking langsmith Client attributes...")
    client = Client()
    # Filter for methods starting with 'delete'
    deletes = [m for m in dir(client) if "delete" in m]
    print(deletes)
except Exception as e:
    print(e)
