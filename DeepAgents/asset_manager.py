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
from dotenv import load_dotenv

# Load env for GCS
load_dotenv()

# Setup simple logger if not running in context of main app
logger = logging.getLogger("AssetManager")

class AssetManager:
    """
    Manages the storage and retrieval of generated assets (Image, Video, Audio).
    Structure: Artifacts/{Category}/{Subcategory}/{Extension}/
    """
    def __init__(self, base_dir: Optional[str] = None):
        if base_dir is None:
            # Default to ../Artifacts relative to this file
            self.base_dir = os.path.abspath(
                os.path.join(os.path.dirname(__file__), "../Artifacts")
            )
        else:
            self.base_dir = base_dir
            
        # GCS Setup
        self.bucket_name = os.getenv("GCP_STORAGE_BUCKET")
        self.gcs_client = None
        if self.bucket_name:
            try:
                from google.cloud import storage
                self.gcs_client = storage.Client()
                logger.info(f"AssetManager: GCS Enabled ({self.bucket_name})")
            except ImportError:
                logger.warning("AssetManager: google-cloud-storage not installed. Cloud history unavailable.")
            except Exception as e:
                logger.error(f"AssetManager: GCS Init Failed: {e}")

        # Try to load System Configuration for Global/Reference paths
        try:
             from DeepAgents.system_config import SystemConfiguration
             self.global_config = SystemConfiguration().load_config().get("global_assets", {})
        except:
             self.global_config = {}

    def get_global_assets(self, asset_type: str) -> List[str]:
        """Returns list of global reference assets of a given type."""
        # Simple local file listing (Voice references are local)
        path = None
        if asset_type.lower() == "voice":
             path = os.path.join(self.base_dir, "Audio/Voices/System")
        elif asset_type.lower() == "audio":
             path = os.path.join(self.base_dir, "Audio/Music")
             
        if path and os.path.exists(path):
             # Recursively find files
             files = []
             for root, _, filenames in os.walk(path):
                 for f in filenames:
                    files.append(os.path.join(root, f))
             return files
        return []

    def _get_storage_path(self, asset_type: str, extension: str, subtype: str = None) -> str:
        """Determines the canonical path based on Media Type logic."""
        # Map generic types to specific Artifact structure
        # Structure: Artifacts/Audio/Music/mp3/filename.mp3
        
        category = "Data"
        subcategory = "General"
        
        if asset_type == "audio":
            category = "Audio"
            if subtype == "voice":
                subcategory = "Voices/Clones"
            elif subtype == "music":
                subcategory = "Music"
            else:
                subcategory = "General"
        elif asset_type == "video":
            category = "Video"
            subcategory = "mp4" # Flattened if no subtype
        elif asset_type == "image":
            category = "Images"
            if subtype == "storyboard":
                 subcategory = "Storyboards"
            else:
                 subcategory = "General"
                 
        # Ensure we don't duplicate extension in path if it's already the folder name
        if subcategory != extension and extension:
             ext_folder = extension
        else:
             ext_folder = ""
             
        # Normalize relative path
        rel_path = os.path.join(category, subcategory, ext_folder)
        full_path = os.path.join(self.base_dir, rel_path)
        os.makedirs(full_path, exist_ok=True)
        return full_path

    def _upload_to_gcs(self, local_path: str, filename: str) -> str:
        """Uploads file to GCS and returns Public URL."""
        if not self.gcs_client or not self.bucket_name:
            return None
            
        try:
            bucket = self.gcs_client.bucket(self.bucket_name)
            # Create a blob with a logical path (Year/Month/Filename) for better organization in bucket
            blob_name = f"history/{time.strftime('%Y/%m')}/{filename}"
            blob = bucket.blob(blob_name)
            blob.upload_from_filename(local_path)
            
            # Since bucket is Uniform/Public or we need Signed URL:
            # We will generate a signed URL valid for 7 days (max allowed for V4 usually)
            # Or usually standard Storage URL if public.
            # User said "bucket is public", so we use public link.
            return blob.public_url
        except Exception as e:
            logger.error(f"GCS Upload Failed: {e}")
            return None

    def save_asset( # pylint: disable=too-many-arguments, too-many-locals
        self,
        data: Union[bytes, str],
        asset_type: str,
        session_id: str,
        prompt: str,
        metadata: Optional[Dict[str, Any]] = None,
        extension: Optional[str] = None,
        subtype: str = None # New param for strict categorization
    ) -> Optional[str]:
        """
        Saves an asset to disk AND uploads to GCS for history.
        subtype: 'music', 'voice', 'storyboard' etc.
        """
        if metadata is None:
            metadata = {}

        # Determine extension
        if not extension:
            if asset_type in ('image', 'storyboard'): extension = "png"
            elif asset_type == 'video': extension = "mp4"
            elif asset_type == 'audio': extension = "wav"
            else: extension = "bin"
            
        # Clean extension
        extension = extension.replace(".", "")

        # Unique Filename
        timestamp = int(time.time())
        prompt_hash = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
        filename = f"{asset_type}_{subtype or 'gen'}_{timestamp}_{prompt_hash}.{extension}"

        # Get Target Directory
        target_dir = self._get_storage_path(asset_type, extension, subtype)
        file_path = os.path.join(target_dir, filename)

        # Save Data Locally
        try:
            # Handle Replicate FileOutput objects
            if hasattr(data, "read") and hasattr(data, "url"):
                 data = str(data)

            if isinstance(data, str) and (data.startswith("http://") or data.startswith("https://")):
                with requests.get(data, stream=True, timeout=30) as r:
                    r.raise_for_status()
                    with open(file_path, 'wb') as f:
                        shutil.copyfileobj(r.raw, f)
            else:
                mode = 'wb' if isinstance(data, bytes) else 'w'
                if 'b' in mode:
                    with open(file_path, mode) as f: f.write(data) # type: ignore
                else:
                    with open(file_path, mode, encoding="utf-8") as f: f.write(data) # type: ignore

            # Upload to Cloud (History)
            cloud_url = self._upload_to_gcs(file_path, filename)

            # Save Metadata (Enriched)
            meta = {
                "prompt": prompt,
                "timestamp": timestamp,
                "date": time.strftime("%Y-%m-%d %H:%M:%S"),
                "asset_type": asset_type,
                "subtype": subtype,
                "filename": filename,
                "local_path": file_path,
                "cloud_url": cloud_url,
                "session_id": session_id,
                "metadata": metadata
            }
            with open(file_path + ".json", "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2)

            return file_path
        except Exception as e: # pylint: disable=broad-exception-caught
            logger.error("Error saving asset: %s", e)
            return None

    def save_text_document(
        self,
        text: str,
        title: str,
        session_id: str,
        subdir: str = "Reports",
        extension: str = "md"
    ) -> Dict[str, str]:
        """
        Saves a text document and uploads to Cloud.
        Returns dict with keys: 'local_path', 'cloud_url'.
        """
        # 1. Prepare Paths
        # Structure: Artifacts/Documents/{subdir}/
        rel_path = os.path.join("Documents", subdir)
        full_dir = os.path.join(self.base_dir, rel_path)
        os.makedirs(full_dir, exist_ok=True)
        
        # 2. Filename
        clean_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '_')
        timestamp = int(time.time())
        extension = extension.lstrip('.')
        filename = f"{clean_title}_{timestamp}.{extension}"
        file_path = os.path.join(full_dir, filename)
        
        # 3. Write Local
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
                
            # 4. Upload Cloud
            cloud_url = self._upload_to_gcs(file_path, filename)
            
            return {
                "local_path": file_path,
                "cloud_url": cloud_url or "Local Only (GCS Not Configured)"
            }
        except Exception as e:
            logger.error(f"Failed to save document: {e}")
            return {"local_path": "", "cloud_url": ""}

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

                    # Filter by Session ID (check metadata, not path)
                    if session_id:
                        meta_sid = str(meta.get("session_id", ""))
                        if meta_sid != str(session_id):
                            continue

                    if asset_type and meta.get("asset_type") != asset_type:
                        continue
                        
                    # Add Cloud URL if available
                    if "cloud_url" not in meta and "url" in meta:
                         meta["cloud_url"] = meta["url"] # Legacy fix

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

    def sync_local_to_cloud(self, dry_run=False) -> List[str]:
        """
        Backfills existing local assets to GCS.
        Updates the JSON metadata with the new cloud_url.
        """
        if not self.gcs_client:
            logger.error("Sync Failed: GCS not configured.")
            return []

        synced_files = []
        logger.info(f"Starting Cloud Sync (Dry Run: {dry_run})...")

        for root, _, files in os.walk(self.base_dir):
            for file in files:
                if file.endswith(".json"): continue
                
                # Check for companion metadata file
                meta_path = os.path.join(root, file + ".json")
                if not os.path.exists(meta_path):
                    # Maybe it's a raw file? Skip for now to assume we only sync generated assets.
                    continue
                    
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    
                    # Skip if already synced
                    if meta.get("cloud_url") and "storage.googleapis.com" in meta.get("cloud_url"):
                        continue
                        
                    # Upload
                    local_path = os.path.join(root, file)
                    if not dry_run:
                        # Use existing logic
                        url = self._upload_to_gcs(local_path, file)
                        if url:
                            meta["cloud_url"] = url
                            # Update JSON
                            with open(meta_path, 'w', encoding='utf-8') as f:
                                json.dump(meta, f, indent=2)
                            synced_files.append(file)
                            logger.info(f"Synced: {file}")
                    else:
                        synced_files.append(file + " (dry)")
                        
                except Exception as e:
                    logger.error(f"Failed to sync {file}: {e}")
                    
        return synced_files
