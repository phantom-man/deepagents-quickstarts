"""
Asset Manager Module.
Manages the storage and retrieval of generated assets (Image, Video, Audio).
"""
import os
import json
import time
import hashlib
import shutil
import logging
from typing import Optional, Union, List, Dict, Any
import requests

# Setup simple logger if not running in context of main app
logger = logging.getLogger("AssetManager")

class AssetManager:
    """
    Manages the storage and retrieval of generated assets (Image, Video, Audio).
    Structure: data/assets/{session_id}/{asset_type}/
    """
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to ../Artifacts relative to this file
            self.base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../Artifacts")
            )
        else:
            self.base_dir = base_dir

        # Try to load System Configuration for Global/Reference paths
        try:
             from DeepAgents.system_config import SystemConfiguration
             self.global_config = SystemConfiguration().load_config().get("global_assets", {})
        except:
             self.global_config = {}

    def get_global_assets(self, asset_type: str) -> List[str]:
        """Returns list of global reference assets of a given type."""
        # Map user type to config key
        key_map = {"audio": "audio", "video": "video", "image": "images", "voice": "audio"}
        cfg_key = key_map.get(asset_type.lower(), asset_type.lower())
        
        path = self.global_config.get(cfg_key)
        if not path:
             # Fallback
             base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
             if asset_type == "voice": path = os.path.join(base, "Artifacts/Audio/Voices")
             else: path = os.path.join(base, f"Artifacts/{asset_type.capitalize()}")
             
        if path and not os.path.isabs(path):
             path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", path))

        if os.path.exists(path):
            return [os.path.join(path, f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
        return []

    def _get_session_dir(self, session_id: str, asset_type: str) -> str:
        path = os.path.join(self.base_dir, str(session_id), asset_type)
        os.makedirs(path, exist_ok=True)
        return path

    def save_asset( # pylint: disable=too-many-arguments, too-many-locals
        self,
        data: Union[bytes, str],
        asset_type: str,
        session_id: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
        extension: Optional[str] = None
    ) -> Optional[str]:
        """
        Saves an asset to disk.
        data: bytes (for raw data) or str (for URL to download)
        asset_type: 'image', 'video', 'audio', 'storyboard'
        """
        if metadata is None:
            metadata = {}

        # Determine extension
        if not extension:
            if asset_type in ('image', 'storyboard'):
                extension = "png"
            elif asset_type == 'video':
                extension = "mp4"
            elif asset_type == 'audio':
                extension = "wav"
            else:
                extension = "bin"

        # Unique Filename
        timestamp = int(time.time())
        # Use first 32 chars of prompt hash to avoid too long names
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
        filename = f"{timestamp}_{prompt_hash}.{extension}"

        target_dir = self._get_session_dir(session_id, asset_type)
        file_path = os.path.join(target_dir, filename)

        # Save Data
        try:
            # Handle Replicate FileOutput objects
            if hasattr(data, "read") and hasattr(data, "url"):
                 # It's a FileOutput/Stream object. Use its URL.
                 data = str(data)

            if isinstance(data, str) and (data.startswith("http://") or data.startswith("https://")):
                # Download URL - Add timeout!
                with requests.get(data, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            else:
                # Save Bytes
                mode = 'wb' if isinstance(data, bytes) else 'w'
                # pylint: disable=unspecified-encoding
                # Binary mode doesn't take encoding, text mode needs it
                if 'b' in mode:
                    with open(file_path, mode) as f:
                        f.write(data) # type: ignore
                else:
                    with open(file_path, mode, encoding="utf-8") as f:
                        f.write(data) # type: ignore

            # Save Metadata
            meta = {
                "prompt": prompt,
                "timestamp": timestamp,
                "asset_type": asset_type,
                "filename": filename,
                "metadata": metadata
            }
            with open(file_path + ".json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            return file_path
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error saving asset: %s", e)
            return None

    def list_assets(
        self,
        session_id: Optional[str] = None,
        asset_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Lists assets.
        If session_id provided, lists for that session.
        If asset_type provided, filters by type.
        """
        assets = []

        # We walk everything from base_dir to find metadata files
        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if not file.endswith(".json"):
                    continue

                # Found a metadata file
                try:
                    with open(os.path.join(root, file), 'r', encoding="utf-8") as f:
                        meta = json.load(f)

                    # Filter
                    if session_id and str(session_id) not in root:
                        continue
                    if asset_type and meta.get("asset_type") != asset_type:
                        continue

                    # Add full path
                    # Construct image path from metadata filename
                    asset_file = meta.get("filename")
                    full_asset_path = os.path.join(root, asset_file)

                    if os.path.exists(full_asset_path):
                        meta["path"] = full_asset_path
                        assets.append(meta)
                except Exception: # pylint: disable=broad-exception-caught
                    pass

        # Sort by timestamp desc
        assets.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
        return assets
