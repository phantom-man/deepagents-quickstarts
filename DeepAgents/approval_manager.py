"""
Approval Manager Module.
Handles the persistence of Human-in-the-Loop (HITL) approvals for assets.
Uses a simple JSON store to track approved paths.
"""
import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("ApprovalManager")

APPROVAL_DB_PATH = os.path.join(os.path.dirname(__file__), "../data/approved_assets.json")

def _load_db() -> dict:
    if not os.path.exists(APPROVAL_DB_PATH):
        return {"approved": [], "rejected": []}
    try:
        with open(APPROVAL_DB_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"approved": [], "rejected": []}

def _save_db(data: dict):
    os.makedirs(os.path.dirname(APPROVAL_DB_PATH), exist_ok=True)
    with open(APPROVAL_DB_PATH, "w") as f:
        json.dump(data, f, indent=2)

def is_asset_approved(asset_path_or_id: str) -> bool:
    """Checks if an asset has been explicitly approved."""
    db = _load_db()
    # Check exact match or basename match
    if asset_path_or_id in db["approved"]:
        return True
    
    # Handle simple filename matching for robustness
    filename = os.path.basename(asset_path_or_id)
    return any(os.path.basename(p) == filename for p in db["approved"])

def is_asset_rejected(asset_path_or_id: str) -> bool:
    """Checks if an asset has been explicitly rejected."""
    # Similar logic
    db = _load_db()
    filename = os.path.basename(asset_path_or_id)
    return any(os.path.basename(p) == filename for p in db["rejected"])

def approve_asset(asset_path: str):
    """Marks an asset as approved."""
    if not asset_path: return
    db = _load_db()
    if asset_path not in db["approved"]:
        db["approved"].append(asset_path)
        _save_db(db)
        logger.info(f"✅ Asset Approved: {asset_path}")

def reject_asset(asset_path: str):
    """Marks an asset as rejected."""
    if not asset_path: return
    db = _load_db()
    if asset_path not in db["rejected"]:
        db["rejected"].append(asset_path)
        _save_db(db)
        logger.info(f"❌ Asset Rejected: {asset_path}")
