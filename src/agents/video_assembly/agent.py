import os
from typing import List, Dict
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
from src.models.models import Scene, VideoScript
from src.core.config import settings

class VideoAssemblyAgent:
    def __init__(self):
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "videos")
        os.makedirs(self.output_dir, exist_ok=True)

    async def assemble_video(
        self, 
        script: VideoScript, 
        image_paths: Dict[int, str], 
        audio_paths: Dict[int, str]
    ) -> str:
        """
        Assembles the video from images and audio.
        Returns the path to the final video file.
        """
        print("Assembling video...")
        clips = []
        
        for scene in script.scenes:
            scene_num = scene.scene_number
            
            if scene_num not in image_paths or scene_num not in audio_paths:
                print(f"Skipping scene {scene_num}: Missing assets")
                continue
                
            image_path = image_paths[scene_num]
            audio_path = audio_paths[scene_num]
            
            # Create Audio Clip
            audio_clip = AudioFileClip(audio_path)
            duration = audio_clip.duration
            
            # Create Image Clip
            # Set duration to match audio
            img_clip = ImageClip(image_path).with_duration(duration)
            
            # Optional: Add simple zoom effect or transition here later
            
            # Combine Image + Audio
            video_clip = img_clip.with_audio(audio_clip)
            
            # Add subtitles (simple version)
            # Note: TextClip requires ImageMagick, might be tricky on some systems.
            # For now, we'll skip subtitles to ensure stability, or add them if requested.
            
            clips.append(video_clip)
            
        if not clips:
            raise ValueError("No clips were created. Check asset generation.")
            
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Write output file
        output_filename = f"{script.title.replace(' ', '_')}_final.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"Writing video to {output_path}...")
        final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        
        return output_path
