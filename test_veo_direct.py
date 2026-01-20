"""Direct test of Veo 3.1 fast video generation."""
import os
import time
from pathlib import Path
from dotenv import load_dotenv

# Load env from DeepAgents folder
load_dotenv(Path(__file__).parent / "DeepAgents" / ".env")

from google import genai
from google.genai import types

# Initialize client with correct project
project = os.environ.get('GOOGLE_CLOUD_PROJECT', 'crafty-hook-483415-b3')
location = 'us-central1'

print(f'Using project: {project}')
print(f'Using location: {location}')

client = genai.Client(
    vertexai=True,
    project=project,
    location=location,
)

print('Client initialized:', client)
print()
print('Testing Veo 3.1 fast...')

# Test simple generation
prompt = 'A golden retriever playing fetch in a sunny park'
model = 'veo-3.1-fast-generate-001'

try:
    # Veo 3.1 only supports durations: 4, 6, or 8 seconds
    config = types.GenerateVideosConfig(
        aspect_ratio='16:9',
        number_of_videos=1,
        duration_seconds=8,  # Must be 4, 6, or 8
        enhance_prompt=True,
    )
    print(f'Config created: {config}')
    
    operation = client.models.generate_videos(
        model=model,
        prompt=prompt,
        config=config,
    )
    print(f'Operation started: {operation}')
    print(f'Operation done: {operation.done}')
    if hasattr(operation, 'name'):
        print(f'Operation name: {operation.name}')
    
    # Poll for completion
    print('\nWaiting for video generation...')
    max_wait = 180  # 3 minutes
    poll_interval = 10
    elapsed = 0
    
    while not operation.done and elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        print(f'  Still generating... ({elapsed}s elapsed)')
        operation = client.operations.get(operation)
    
    if not operation.done:
        print(f'ERROR: Timed out after {max_wait}s')
    else:
        print('\nOperation completed!')
        print(f'Response: {operation.response}')
        
        if operation.response and hasattr(operation.response, 'generated_videos'):
            videos = operation.response.generated_videos
            print(f'Generated {len(videos)} video(s)')
            for i, video in enumerate(videos):
                print(f'  Video {i}: {video}')
                if hasattr(video, 'video'):
                    v = video.video
                    if hasattr(v, 'uri') and v.uri:
                        print(f'    URI: {v.uri}')
                    if hasattr(v, 'video_bytes') and v.video_bytes:
                        byte_count = len(v.video_bytes)
                        print(f'    Bytes: {byte_count} bytes')
                        
                        # Save video to disk
                        output_path = Path(__file__).parent / "Artifacts" / "Video" / "veo_test_output.mp4"
                        output_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(output_path, 'wb') as f:
                            f.write(v.video_bytes)
                        print(f'    SAVED TO: {output_path}')
                        print(f'    File size: {output_path.stat().st_size:,} bytes')
        else:
            print('No generated_videos in response')
            print(f'Full operation: {operation}')
            
except Exception as e:
    import traceback
    print(f'ERROR: {type(e).__name__}: {e}')
    traceback.print_exc()
