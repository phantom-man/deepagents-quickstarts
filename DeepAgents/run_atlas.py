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

try:
    # Attempt to import PromptToolkit
    from prompt_toolkit import PromptSession
    from prompt_toolkit.patch_stdout import patch_stdout
    PROMPT_TOOLKIT_AVAILABLE = True
except ImportError:
    PROMPT_TOOLKIT_AVAILABLE = False
    
def input_monitor():
    """
    Runs in a dedicated thread. 
    Continuously listens for user input in the console.
    Pushes valid input to AtlasLink.
    """
    if PROMPT_TOOLKIT_AVAILABLE:
        # We don't use this thread for input if PromptToolkit is active in main
        # But for backward compat or if main doesn't loop
        return

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
    try:
        from prompt_toolkit import PromptSession
        from prompt_toolkit.patch_stdout import patch_stdout
        USE_PROMPT_TOOLKIT = True
    except ImportError:
        USE_PROMPT_TOOLKIT = False

    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="Discuss the nature of AI Consciousness")
    parser.add_argument("--voice-only", action="store_true", help="Skip Agent Init and just echo voice.")
    args, unknown = parser.parse_known_args()
    
    # We reconstruct sys.argv for the internal studio main()
    # Ensure we include other arguments (like --model)
    # We strip --voice-only from argv so argparse in studio.py doesn't choke if it's not defined there
    sys.argv = [sys.argv[0], "--task", args.task] + unknown
    
    # Inject Voice Only Flag into Environment (Studio checks this)
    if args.voice_only:
        os.environ["ATLAS_VOICE_ONLY_MODE"] = "true"

    if USE_PROMPT_TOOLKIT:
        # Run Atlas in a background thread
        # Run PromptSession in the main thread with patch_stdout
        # This allows logs to print ABOVE the prompt line without breaking it.
        t_atlas = threading.Thread(target=run_atlas, daemon=True)
        t_atlas.start()
        
        session = PromptSession()
        
        print(f"\n{BLUE}ℹ️  Atlas Console (Enhanced): Type your command and press ENTER to interrupt.{RESET}")
        
        with patch_stdout():
            while True:
                try:
                    # Blocking prompt that handles background stdout beautifully
                    # If Voice Only mode is active, check_refresh_interval ensures we don't block forever 
                    # if the background thread dies.
                    user_text = session.prompt(">> ", in_thread=True)
                    if user_text.strip():
                        if args.voice_only:
                             # Direct echo to voice bridge in Voice Only Mode
                             # We bypass atlas_link queue for speed/simplicity or just queue it 
                             # But studio.py needs to pop it.
                             atlas_link.send_interruption(user_text)
                             from DeepAgents.studio import voice_update
                             voice_update(f"User says: {user_text}")
                        else:
                             print(f"{GREEN}⚡ Sending Update to Atlas: '{user_text}'{RESET}")
                             atlas_link.send_interruption(user_text)
                except (EOFError, KeyboardInterrupt):
                    break

        
        # User quit the prompt
        print("Exiting...")
        os._exit(0)

    else:
        # Legacy Fallback
        # Start Input Thread
        t = threading.Thread(target=input_monitor, daemon=True)
        t.start()
        
        # Start Atlas (Main Thread)
        run_atlas()
