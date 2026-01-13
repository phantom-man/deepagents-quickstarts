try:
    from DeepAgents.CommercialAgents.composer_agent import agent
    print("Syntax Check Passed: Module Loaded Successfully.")
except ImportError as e:
    print(f"Import Error: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
except Exception as e:
    print(f"General Error during import: {e}")
