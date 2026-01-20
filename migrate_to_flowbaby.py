"""
Bulk ingest memories from flowbaby_migration.json into Flowbaby.
Uses the Flowbaby Python bridge ingest.py script.
"""
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# Paths
MIGRATION_FILE = Path("flowbaby_migration.json")
WORKSPACE_PATH = Path("C:/Users/User/source/repos/deepagents-quickstarts")
BRIDGE_PATH = Path.home() / ".vscode/extensions/flowbaby.flowbaby-0.7.3/bridge/ingest.py"

def ingest_memory(memory: dict, index: int) -> dict:
    """Ingest a single memory into Flowbaby."""
    now = datetime.utcnow().isoformat() + "Z"
    
    # Build payload matching Flowbaby's contract
    payload = {
        "workspace_path": str(WORKSPACE_PATH),
        "topic": memory["topic"],
        "context": memory["context"],
        "topicId": memory.get("metadata", {}).get("plan_id", f"migrated-{index:03d}"),
        "planId": memory.get("metadata", {}).get("plan_id", "memoripilot-migration"),
        "status": memory.get("metadata", {}).get("status", "Active"),
        "decisions": memory.get("decisions", []),
        "rationale": memory.get("rationale", []),
        "createdAt": now,
        "updatedAt": now
    }
    
    # Call the bridge
    cmd = [
        sys.executable,
        str(BRIDGE_PATH),
        "--summary",
        "--summary-json",
        json.dumps(payload)
    ]
    
    print(f"\n[{index+1}] Ingesting: {memory['topic'][:50]}...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,  # 2 min timeout per memory
            cwd=str(WORKSPACE_PATH)
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            if response.get("success"):
                print(f"    [OK] Ingested {response.get('ingested_chars', '?')} chars in {response.get('ingestion_duration_sec', '?'):.1f}s")
                return {"success": True, "topic": memory["topic"]}
            else:
                print(f"    [FAIL] {response.get('error', 'Unknown error')}")
                return {"success": False, "topic": memory["topic"], "error": response.get("error")}
        else:
            print(f"    [FAIL] Exit code {result.returncode}")
            print(f"    stderr: {result.stderr[:200] if result.stderr else 'none'}")
            return {"success": False, "topic": memory["topic"], "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        print("    [TIMEOUT] Ingestion took too long")
        return {"success": False, "topic": memory["topic"], "error": "Timeout"}
    except json.JSONDecodeError as e:
        print(f"    [FAIL] Invalid JSON response: {e}")
        return {"success": False, "topic": memory["topic"], "error": str(e)}
    except Exception as e:
        print(f"    [FAIL] Exception: {e}")
        return {"success": False, "topic": memory["topic"], "error": str(e)}

def main():
    """Main entry point."""
    print("=" * 60)
    print("Flowbaby Memory Migration Tool")
    print("=" * 60)
    
    # Check bridge exists
    if not BRIDGE_PATH.exists():
        print(f"[ERROR] Flowbaby bridge not found at: {BRIDGE_PATH}")
        print("Please ensure Flowbaby extension is installed.")
        sys.exit(1)
    
    # Load migration file
    if not MIGRATION_FILE.exists():
        print(f"[ERROR] Migration file not found: {MIGRATION_FILE}")
        sys.exit(1)
    
    with open(MIGRATION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    memories = data.get("memories", [])
    print(f"\nFound {len(memories)} memories to migrate.\n")
    
    # Ingest each memory
    results = []
    for i, memory in enumerate(memories):
        result = ingest_memory(memory, i)
        results.append(result)
    
    # Summary
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count
    
    print("\n" + "=" * 60)
    print(f"Migration Complete: {success_count}/{len(results)} succeeded")
    if fail_count > 0:
        print("\nFailed memories:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['topic']}: {r.get('error', 'Unknown')[:50]}")
    print("=" * 60)

if __name__ == "__main__":
    main()
