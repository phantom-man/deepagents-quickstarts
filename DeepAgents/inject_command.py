import argparse
import sys
import os

# Ensure we can import from local
sys.path.append(os.path.dirname(__file__))
from atlas_db import init_db, add_command

def main():
    parser = argparse.ArgumentParser(description="Inject a command into the Atlas Agent stream.")
    parser.add_argument("prompt", nargs="?", help="The text prompt to inject.")
    parser.add_argument("--loop", action="store_true", help="Run in interactive loop mode.")
    
    args = parser.parse_args()
    
    # Initialize DB just in case
    init_db()
    
    if args.loop:
        print("💉 Atlas Injection Console (Ctrl+C to exit)")
        print("   Type a message to interrupt/guide Atlas.")
        try:
            while True:
                user_input = input(">> ")
                if user_input.strip():
                    add_command(user_input)
                    print("   [Sent to Queue]")
        except KeyboardInterrupt:
            print("\nExiting.")
            return

    if args.prompt:
        add_command(args.prompt)
        print(f"✅ Injected: '{args.prompt}'")
    else:
        if not args.loop:
            print("Please provide a prompt or use --loop.")

if __name__ == "__main__":
    main()
