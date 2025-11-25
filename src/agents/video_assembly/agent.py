import os
from typing import List, Dict
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, TextClip, ColorClip
from src.models.models import Scene, VideoScript
from src.core.config import settings
import structlog

logger = structlog.get_logger()

class VideoAssemblyAgent:
    def __init__(self):
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "videos")
        os.makedirs(self.output_dir, exist_ok=True)

    async def assemble_video(
        self, 
        script: VideoScript, 
        image_paths: Dict[int, List[str]], 
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
                
            image_paths_list = image_paths[scene_num]
            # Handle case where image_paths might be a single string (backward compatibility)
            if isinstance(image_paths_list, str):
                image_paths_list = [image_paths_list]
                
            audio_path = audio_paths[scene_num]
            
            # Create Audio Clip
            audio_clip = AudioFileClip(audio_path)
            total_duration = audio_clip.duration
            
            # Calculate durations for each image
            num_images = len(image_paths_list)
            image_durations = []
            
            if num_images == 1:
                image_durations = [total_duration]
            else:
                # Use provided ratios or default to equal distribution
                ratios = scene.image_ratios
                if not ratios or len(ratios) != num_images:
                    # Equal distribution
                    image_durations = [total_duration / num_images] * num_images
                else:
                    # Use ratios
                    # Normalize ratios just in case
                    total_ratio = sum(ratios)
                    image_durations = [total_duration * (r / total_ratio) for r in ratios]
            
            # Create Image Clips
            scene_clips = []
            for i, img_path in enumerate(image_paths_list):
                duration = image_durations[i]
                img_clip = ImageClip(img_path).with_duration(duration)
                
                # Apply Effect (TICKET-030)
                effect_name = getattr(scene, 'selected_effect', 'ken_burns_zoom_in')
                img_clip = self._apply_effect(img_clip, effect_name, duration)
                
                scene_clips.append(img_clip)
            
            # Concatenate image clips for this scene
            if len(scene_clips) > 1:
                visual_clip = concatenate_videoclips(scene_clips, method="compose")
            else:
                visual_clip = scene_clips[0]
            
            # Combine Visual + Audio
            video_clip = visual_clip.with_audio(audio_clip)
            
            # Add subtitles (simple version)
            # Note: TextClip requires ImageMagick, might be tricky on some systems.
            # For now, we'll skip subtitles to ensure stability, or add them if requested.
            
            clips.append(video_clip)
            
        if not clips:
            raise ValueError("No clips were created. Check asset generation.")
            
        # Concatenate all clips
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Add Title Overlay (TICKET-029)
        try:
            # Create a text clip for the title
            # We use a try-catch block because TextClip requires ImageMagick
            print(f"Adding title overlay: {script.title}")
            
            # Create text clip
            # Using a default font, white color, and some padding
            # Remove bg_color='transparent' as it might cause issues with some IM versions
            # Use None for transparent background
            txt_clip = (TextClip(
                text=script.title,
                font="Arial-Bold", 
                font_size=70, 
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(final_video.w * 0.8, None), # 80% width, auto height
                text_align='center'
            )
            .with_position(('center', 80)) # Center horizontally, 80px from top
            .with_duration(3) # Show for 3 seconds
            .with_effects([]) # Add fadein/fadeout if needed
            )
            
            # Composite the title over the video
            final_video = CompositeVideoClip([final_video, txt_clip])
            
        except Exception as e:
            logger.warning("Failed to add title overlay. Is ImageMagick installed?", error=str(e))
            print(f"WARNING: Could not add title overlay: {e}")
            # Continue without title
        
        # Write output file
        output_filename = f"{script.title.replace(' ', '_')}_final.mp4"
        output_path = os.path.join(self.output_dir, output_filename)
        
        print(f"Writing video to {output_path}...")
        final_video.write_videofile(output_path, fps=24, codec='libx264', audio_codec='aac')
        
        return output_path

    def _apply_effect(self, clip: ImageClip, effect_name: str, duration: float) -> ImageClip:
        """
        Apply visual effect to the image clip.
        """
        w, h = clip.size
        
        # Map complex/unimplemented effects to simple zoom to avoid static images
        # and avoid "dizzying" shake effects
        if effect_name in ["shake", "handheld", "crane_up", "crane_down", "orbit", "dolly_zoom"]:
            effect_name = "ken_burns_zoom_in"
        
        if effect_name == "ken_burns_zoom_in":
            # Zoom from 1.0 to 1.3
            return clip.with_effects([
                lambda c: c.resized(lambda t: 1 + 0.3 * t / duration)
                           .with_position('center')
            ])
            
        elif effect_name == "ken_burns_zoom_out":
            # Zoom from 1.3 to 1.0
            # Start zoomed in (1.3) and shrink
            return clip.with_effects([
                lambda c: c.resized(lambda t: 1.3 - 0.3 * t / duration)
                           .with_position('center')
            ])
            
        elif effect_name == "pan_left":
            # Pan from right to left
            # We need to zoom in slightly first to have room to pan
            zoom_factor = 1.2
            new_w = w * zoom_factor
            new_h = h * zoom_factor
            
            # Resize first
            enlarged = clip.resized(zoom_factor)
            
            # Calculate x positions
            # Start: Right edge aligned (x = -(new_w - w))
            # End: Left edge aligned (x = 0)
            start_x = -(new_w - w)
            end_x = 0
            
            return enlarged.with_position(lambda t: (start_x + (end_x - start_x) * t / duration, 'center'))
            
        elif effect_name == "pan_right":
            # Pan from left to right
            zoom_factor = 1.2
            new_w = w * zoom_factor
            
            enlarged = clip.resized(zoom_factor)
            
            # Start: Left edge aligned (x = 0)
            # End: Right edge aligned (x = -(new_w - w))
            start_x = 0
            end_x = -(new_w - w)
            
            return enlarged.with_position(lambda t: (start_x + (end_x - start_x) * t / duration, 'center'))
            
        elif effect_name == "tilt_up":
             # Pan from bottom to top
            zoom_factor = 1.2
            new_h = h * zoom_factor
            
            enlarged = clip.resized(zoom_factor)
            
            # Start: Bottom edge aligned (y = -(new_h - h))
            # End: Top edge aligned (y = 0)
            start_y = -(new_h - h)
            end_y = 0
            
            return enlarged.with_position(lambda t: ('center', start_y + (end_y - start_y) * t / duration))

        elif effect_name == "tilt_down":
             # Pan from top to bottom
            zoom_factor = 1.2
            new_h = h * zoom_factor
            
            enlarged = clip.resized(zoom_factor)
            
            # Start: Top edge aligned (y = 0)
            # End: Bottom edge aligned (y = -(new_h - h))
            start_y = 0
            end_y = -(new_h - h)
            
            return enlarged.with_position(lambda t: ('center', start_y + (end_y - start_y) * t / duration))
            
        # Default / Static
        return clip
