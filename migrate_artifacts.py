import os
import sys
import logging

# Ensure root is in path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from DeepAgents.asset_manager import AssetManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("CLOUD_MIGRATION")

def main():
    logger.info("🚀 Starting Artifact Migration to Google Cloud Storage...")
    
    am = AssetManager()
    if not am.gcs_client:
        logger.error("❌ GCS Client failed to initialize. Check credentials.")
        return

    logger.info(f"Target Bucket: {am.bucket_name}")
    
    # Run Sync
    synced = am.sync_local_to_cloud(dry_run=False)
    
    logger.info(f"✅ Migration Complete. {len(synced)} files processed.")
    for f in synced:
        print(f" - {f}")

if __name__ == "__main__":
    main()
