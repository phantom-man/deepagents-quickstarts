import subprocess
import time
import sys
import os
from agent_brain import AgentComms

def run_verification():
    print("🧪 --- Starting Agent Mesh Verification ---")

    # 1. Start Cinematographer (Background)
    print("🎥 Launching Cinematographer Agent (Subprocess, Mode=Storyboard)...")
    
    # Force UTF-8 encoding for inner process
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Using python executable specifically
    cine_process = subprocess.Popen(
        [sys.executable, "DeepAgents/VeoAgent.py", "--mode", "storyboard"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        env=env
    )
    
    print("⏳ Waiting 10s for Cinematographer to hydrate and connect...")
    time.sleep(10)
    
    # Check if it died
    if cine_process.poll() is not None:
        stdout, stderr = cine_process.communicate()
        print(f"❌ Cinematographer died early!\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        return

    # 2. Start Director (Foreground)
    print("🎬 Launching Director Agent (Block)...")
    try:
        # Run Director to send a task
        subprocess.run([sys.executable, "DeepAgents/DeepAgents.py"], check=True)
        print("✅ Director finished thinking and sending orders.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Director crashed: {e}")
        cine_process.terminate()
        return

    # 3. Monitor for Response
    print("📡 Monitoring Nervous System (Postgres) for Cinematographer ack...")
    
    comms = AgentComms(password="d1204l0723")
    if not comms.connect():
        print("❌ CRITICAL: Could not connect to Postgres DB. Is the server running?")
        cine_process.terminate()
        return

    # We look for a message FROM Cinematographer TO Director
    # Poll for 30 seconds
    max_retries = 6
    found = False
    
    for i in range(max_retries):
        print(f"   Polling ({i+1}/{max_retries})...")
        time.sleep(5)
        
        if comms.conn:
             with comms.conn.cursor() as cur:
                cur.execute("SELECT content FROM agent_messages WHERE sender = 'Cinematographer' AND recipient = 'Director' AND status = 'unread' ORDER BY id DESC LIMIT 1")
                row = cur.fetchone()
                
             if row:
                print(f"✅ VERIFIED! Message received from Cinematographer: '{row[0]}'")
                found = True
                break
        else:
             print("❌ Lost connection to DB.")
             break
            
    if not found:
        print("⚠️ No response detected within timeout. Dumping recent logs:")
        # Dump Cinematographer output non-blocking? Hard with basic subprocess.
        # We'll just kill it.
        
    # 4. Cleanup
    print("🛑 Shutting down Cinematographer...")
    cine_process.terminate()
    try:
        outs, errs = cine_process.communicate(timeout=5)
        print(f"--- Cinematographer Logs ---\n{outs}\n{errs}\n----------------------------")
    except:
        cine_process.kill()
        print("Killed forcefully.")

    if found:
        print("🎉 TEST PASSED: Agents are communicating!")
        sys.exit(0)
    else:
        print("❌ TEST FAILED: Loop did not complete.")
        sys.exit(1)

if __name__ == "__main__":
    run_verification()
