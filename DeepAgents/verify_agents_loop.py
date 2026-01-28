"""
Verifies the communication loop between Director and Cinematographer agents.
Invokes both agents as subprocesses and checks for message exchange in DB.
"""

import logging
import os
import subprocess
import sys
import time

try:
    from agent_brain import AgentComms
except ImportError:
    # Fallback to local import if run from root without module context
    from DeepAgents.agent_brain import AgentComms


def run_verification():
    """
    Main verification logic.
    Launches Cinematographer (bg) and Director (fg).
    Monitors Postgres for communication.
    """
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logger = logging.getLogger("Verifier")

    logger.info("🧪 --- Starting Agent Mesh Verification ---")

    # 1. Start Cinematographer (Background)
    logger.info("🎥 Launching Cinematographer Agent (Subprocess, Mode=Storyboard)...")

    # Force UTF-8 encoding for inner process
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    # Using python executable specifically
    # pylint: disable=consider-using-with
    cine_process = subprocess.Popen(
        [sys.executable, "DeepAgents/VeoAgent.py", "--mode", "storyboard"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        env=env,
    )

    logger.info("⏳ Waiting 10s for Cinematographer to hydrate and connect...")
    time.sleep(10)

    # Check if it died
    if cine_process.poll() is not None:
        stdout, stderr = cine_process.communicate()
        logger.error(
            "❌ Cinematographer died early!\nSTDOUT: %s\nSTDERR: %s", stdout, stderr
        )
        return

    # 2. Start Director (Foreground)
    logger.info("🎬 Launching Director Agent (Block)...")
    try:
        # Run Director to send a task
        subprocess.run([sys.executable, "DeepAgents/DeepAgents.py"], check=True)
        logger.info("✅ Director finished thinking and sending orders.")
    except subprocess.CalledProcessError as e:
        logger.error("❌ Director crashed: %s", e)
        cine_process.terminate()
        return

    # 3. Monitor for Response
    logger.info("📡 Monitoring Nervous System (Postgres) for Cinematographer ack...")

    comms = AgentComms(password="d1204l0723")
    if not comms.connect():
        logger.error(
            "❌ CRITICAL: Could not connect to Postgres DB. Is the server running?"
        )
        cine_process.terminate()
        return

    # We look for a message FROM Cinematographer TO Director
    # Poll for 30 seconds
    max_retries = 6
    found = False

    for i in range(max_retries):
        logger.info("   Polling (%d/%d)...", i + 1, max_retries)
        time.sleep(5)

        if comms.conn:
            with comms.conn.cursor() as cur:
                cur.execute(
                    "SELECT content FROM agent_messages "
                    "WHERE sender = 'Cinematographer' AND recipient = 'Director' "
                    "AND status = 'unread' ORDER BY id DESC LIMIT 1"
                )
                row = cur.fetchone()

            if row:
                logger.info(
                    "✅ VERIFIED! Message received from Cinematographer: '%s'", row[0]
                )
                found = True
                break
        else:
            logger.error("❌ Lost connection to DB.")
            break

    if not found:
        logger.warning("⚠️ No response detected within timeout. Dumping recent logs:")

    # 4. Cleanup
    logger.info("🛑 Shutting down Cinematographer...")
    cine_process.terminate()
    try:
        outs, errs = cine_process.communicate(timeout=5)
        logger.info(
            "--- Cinematographer Logs ---\n%s\n%s\n----------------------------",
            outs,
            errs,
        )
    except subprocess.TimeoutExpired:
        cine_process.kill()
        logger.info("Killed forcefully.")

    if found:
        logger.info("🎉 TEST PASSED: Agents are communicating!")
        sys.exit(0)
    else:
        logger.error("❌ TEST FAILED: Loop did not complete.")
        sys.exit(1)


if __name__ == "__main__":
    run_verification()
