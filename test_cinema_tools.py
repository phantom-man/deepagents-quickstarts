import os
import sys

# Ensure path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../")))

from DeepAgents.CommercialAgents.cinematographer_agent.agent import run_cinematographer_task

def test_cinema_react():
    print("Testing Cinematographer ReAct Loop...")
    
    # Request that requires audio AND video
    request = "I need a storyboard image of a cyberpunk city, and please also ask the Composer for some synthwave music to go with it."
    
    result = run_cinematographer_task(request)
    print("\n--- FINAL RESULT ---\n")
    print(result)

if __name__ == "__main__":
    test_cinema_react()
