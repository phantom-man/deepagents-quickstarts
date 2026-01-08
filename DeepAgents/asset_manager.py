import os
import json
import time
import hashlib
import requests
import shutil
from datetime import datetime

class AssetManager:
    """
    Manages the storage and retrieval of generated assets (Image, Video, Audio).
    Structure: data/assets/{session_id}/{asset_type}/
    """
    def __init__(self, base_dir=None):
        if base_dir is None:
            # Default to ../../data/assets relative to this file
            self.base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data/assets"))
        else:
            self.base_dir = base_dir
            
    def _get_session_dir(self, session_id, asset_type):
        path = os.path.join(self.base_dir, str(session_id), asset_type)
        os.makedirs(path, exist_ok=True)
        return path

    def save_asset(self, data, asset_type, session_id, prompt, metadata=None, extension=None):
        """
        Saves an asset to disk.
        data: bytes (for raw data) or str (for URL to download)
        asset_type: 'image', 'video', 'audio', 'storyboard'
        """
        if metadata is None: metadata = {}
        
        # Determine extension
        if not extension:
            if asset_type == 'image' or asset_type == 'storyboard': extension = "png"
            elif asset_type == 'video': extension = "mp4"
            elif asset_type == 'audio': extension = "wav"
            else: extension = "bin"

        # Unique Filename
        timestamp = int(time.time())
        file_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        filename = f"{timestamp}_{file_hash}.{extension}"
        
        target_dir = self._get_session_dir(session_id, asset_type)
        file_path = os.path.join(target_dir, filename)
        
        # Save Data
        try:
            if isinstance(data, str) and (data.startswith("http://") or data.startswith("https://")):
                # Download URL
                with requests.get(data, stream=True) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            else:
                # Save Bytes
                mode = 'wb' if isinstance(data, bytes) else 'w'
                with open(file_path, mode) as f:
                    f.write(data)
                    
            # Save Metadata
            meta = {
                "prompt": prompt,
                "timestamp": timestamp,
                "asset_type": asset_type,
                "filename": filename,
                "metadata": metadata
            }
            with open(file_path + ".json", "w") as f:
                json.dump(meta, f, indent=2)
                
            return file_path
        except Exception as e:
            print(f"Error saving asset: {e}")
            return None

    def list_assets(self, session_id=None, asset_type=None):
        """
        Lists assets.
        If session_id provided, lists for that session.
        If asset_type provided, filters by type.
        """
        assets = []
        
        search_dirs = []
        if session_id:
            root_s = os.path.join(self.base_dir, str(session_id))
            if os.path.exists(root_s):
                search_dirs.append(root_s)
        else:
            # Walk all sessions
            pass # TODO: Implement global walk if needed, but simple listing of sessions might be better
            
        # For simplicity, if session_id is None, we walk everything
        dirs_to_walk = [self.base_dir]
        
        for root, dirs, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".json"):
                    # Found a metadata file
                    try:
                        with open(os.path.join(root, file), 'r') as f:
                            meta = json.load(f)
                            
                        # Filter
                        if session_id and str(session_id) not in root: continue
                        if asset_type and meta.get("asset_type") != asset_type: continue
                        
                        # Add full path
                        # Construct image path from metadata filename
                        asset_file = meta.get("filename")
                        full_asset_path = os.path.join(root, asset_file)
                        
                        if os.path.exists(full_asset_path):
                            meta["path"] = full_asset_path
                            # Add relative path for Streamlit serving if needed? 
                            # Streamlit st.image can process absolute paths usually.
                            assets.append(meta)
                    except:
                        pass
                        
        # Sort by timestamp desc
        assets.sort(key=lambda x: x["timestamp"], reverse=True)
        return assets
