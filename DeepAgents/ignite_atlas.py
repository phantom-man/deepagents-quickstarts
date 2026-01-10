import subprocess
import sys
import time
import os
import signal
import atexit

# ANSI Colors
CYAN = "\033[96m"
RESET = "\033[0m"

def main():
    print(f"{CYAN}🔥 Igniting Atlas Session...{RESET}")
    print(f"{CYAN}   1. Starting Voice Bridge (Background){RESET}")
    
    # 1. Start Voice Bridge
    # Use the current python executable
    voice_process = subprocess.Popen(
        [sys.executable, "DeepAgents/voice_bridge.py"],
        stdout=subprocess.DEVNULL, # Suppress voice logging to keep console clean
        stderr=subprocess.DEVNULL
    )
    
    # Register cleanup
    def cleanup():
        print(f"\n{CYAN}🛑 Extinguishing Session...{RESET}")
        try:
            voice_process.terminate()
            voice_process.wait(timeout=2)
        except:
            voice_process.kill()
        print(f"{CYAN}✅ Session Ended.{RESET}")

    atexit.register(cleanup)
    
    # Wait a sec for voice to init
    time.sleep(2)
    
    # 2. Start Atlas Console (Foreground)
    print(f"{CYAN}   2. Launching Atlas Console{RESET}")
    
    # We run this in the SAME process loop or Subprocess?
    # Subprocess allows us to keep the Session Manager distinct.
    try:
        # Pass through all arguments given to ignition
        cmd = [sys.executable, "DeepAgents/run_atlas.py"] + sys.argv[1:]
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        pass
    except subprocess.CalledProcessError as e:
        print(f"Atlas Error: {e}")

if __name__ == "__main__":
    main()
