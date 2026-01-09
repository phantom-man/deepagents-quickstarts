import os
import logging
from moviepy import VideoFileClip, AudioFileClip

logger = logging.getLogger(__name__)

def merge_audio_video(video_path, audio_path, output_path=None):
    """
    Combines a video file and an audio file.
    Trims/Loops video to match audio duration? 
    For now: Trims audio to video duration OR Loops video?
    """
    try:
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video not found: {video_path}")
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio not found: {audio_path}")

        video_clip = VideoFileClip(video_path)
        audio_clip = AudioFileClip(audio_path)

        # Set audio to video
        # Strategy: If video is shorter than audio, we assume video is a loop or we just take the first chunks.
        # But user wants "band plays out lyrics".
        # Typically Composer song = 3-4 mins. Veo video = 4-60 secs.
        # We probably need to loop the video or specific logic.
        # For MVP: We just set the audio. If video is shorter, audio cuts off? 
        # Or we loop video to match audio?
        
        # Let's loop video to match audio duration
        final_video = video_clip.looped(duration=audio_clip.duration)
        final_video = final_video.with_audio(audio_clip)

        if not output_path:
             base, _ = os.path.splitext(video_path)
             output_path = f"{base}_music_video.mp4"

        final_video.write_videofile(output_path, codec="libx264", audio_codec="aac")
        return output_path
        
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        return None
