import sys
import os
import threading
import time
import queue
import logging
import argparse
from dotenv import load_dotenv

# Path Setup
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from DeepAgents.atlas_link import link as atlas_link
from DeepAgents.studio import main as studio_main_logic, voice_update

# Load Env
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# Console Colors
GREEN = "\033[92m"
BLUE = "\033[94m"
RESET = "\033[0m"

def input_monitor():
    """
    Runs in a dedicated thread. 
    Continuously listens for user input in the console.
    Pushes valid input to AtlasLink.
    """
    # Give the main thread time to print headers
    time.sleep(2)
    
    print(f"\n{BLUE}ℹ️  Atlas Console: Type your command at any time and press ENTER to interrupt.{RESET}")
    print(f"{BLUE}>> {RESET}", end="", flush=True)
    
    while True:
        try:
            # Blocking Input
            user_text = sys.stdin.readline()
            if not user_text:
                break
                
            user_text = user_text.strip()
            if user_text:
                print(f"{GREEN}⚡ Sending Update to Atlas: '{user_text}'{RESET}")
                atlas_link.send_interruption(user_text)
                print(f"{BLUE}>> {RESET}", end="", flush=True)
                
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Input Error: {e}")

def run_atlas():
    """
    Wrapper for the Studio Logic.
    Injects the custom loop logic.
    """
    # Patch the check_for_injections function in studio.py 
    # to use our new singleton atlas_link
    import DeepAgents.studio as studio_module
    
    def check_link_wrapper():
        return atlas_link.check_for_interruption()
        
    # Hot-swap the function
    studio_module.check_for_injections = check_link_wrapper
    
    # Run the standard logic
    try:
        studio_module.main()
    except SystemExit:
        pass
    except Exception as e:
        print(f"Atlas Crashed: {e}")
    finally:
        print("Atlas Shutdown.")
        # Kill python process to stop input thread
        os._exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="Discuss the nature of AI Consciousness")
    args, unknown = parser.parse_known_args()
    
    # We reconstruct sys.argv for the internal studio main()
    sys.argv = [sys.argv[0], "--task", args.task]
    
    # Start Input Thread
    t = threading.Thread(target=input_monitor, daemon=True)
    t.start()
    
    # Start Atlas (Main Thread)
    run_atlas()
