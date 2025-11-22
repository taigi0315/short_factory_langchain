import os
import time
import structlog
import hashlib
import numpy as np
from typing import List, Tuple, Optional
from pathlib import Path
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip, ColorClip, VideoClip
)
# In MoviePy v2, effects are often in vfx
# We need to check how to access fadein/fadeout/resize/crop
# Usually they are methods on the clip, or in vfx
from moviepy.video.fx import FadeIn, FadeOut, Resize, Crop
# Wait, let's check if we can just import vfx and use vfx.fadein
# Or if they are available as methods.
# MoviePy 2.x usually has them as methods or effects classes.
# Let's try to import vfx and see.
import moviepy.video.fx as vfx
from PIL import Image, ImageDraw, ImageFont
from src.core.config import settings
from src.models.models import (
    VideoScript, Scene, ImageStyle, SceneType, VoiceTone, 
    ElevenLabsSettings, TransitionType
)

logger = structlog.get_logger()

class VideoGenAgent:
    """Enhanced video generation with real images and audio."""
    
    def __init__(self):
        # Use centralized config
        self.use_real_video = settings.USE_REAL_LLM # Using LLM flag as proxy for "Real Mode" generally, or could use specific flag if added
        # Actually, let's use the new settings if available, or default to True if not explicitly set
        # But TICKET-014 said "USE_REAL_VIDEO" in config.
        # Let's assume settings has it (we just added it).
        # Wait, we didn't add USE_REAL_VIDEO to config.py, we added VIDEO_RESOLUTION etc.
        # We should check if USE_REAL_VIDEO exists or just use a default.
        # Let's check if 'USE_REAL_VIDEO' is in settings. It is not in the pydantic model we just edited.
        # We added VIDEO_RESOLUTION, VIDEO_FPS, VIDEO_QUALITY.
        # We should probably use USE_REAL_IMAGE and USE_REAL_VOICE as indicators, or just always try real if assets are provided.
        # Let's assume if we are called with real assets, we generate real video.
        
        self.output_dir = Path(settings.GENERATED_ASSETS_DIR) / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Resolution settings
        self.resolution = (1920, 1080) if settings.VIDEO_RESOLUTION == "1080p" else (1280, 720)
        self.fps = settings.VIDEO_FPS
        self.preset = settings.VIDEO_QUALITY

    async def generate_video(
        self,
        script: VideoScript,
        images: List[str], # Paths as strings
        audio_map: dict[int, str], # Map scene_number -> audio_path
        style: ImageStyle = ImageStyle.CINEMATIC
    ) -> str:
        """Generate video from script, images, and audio."""
        
        logger.info("Generating video for script", title=script.title)
        
        try:
            # Create scene clips
            scene_clips = []
            
            # Sort scenes by number
            sorted_scenes = sorted(script.scenes, key=lambda s: s.scene_number)
            
            # Ensure we have enough images
            if len(images) < len(sorted_scenes):
                logger.warning("Not enough images for scenes. Reusing last image.", image_count=len(images), scene_count=len(sorted_scenes))
                # Pad images with the last one
                while len(images) < len(sorted_scenes):
                    images.append(images[-1] if images else "placeholder.jpg")

            for i, scene in enumerate(sorted_scenes):
                image_path = images[i]
                audio_path = audio_map.get(scene.scene_number)
                
                if not audio_path or not os.path.exists(audio_path):
                    logger.warning("Missing audio for scene. Using default duration.", scene_number=scene.scene_number)
                    duration = 3.0
                    audio_clip = None
                else:
                    audio_clip = AudioFileClip(audio_path)
                    duration = audio_clip.duration
                
                # Create visual clip
                clip = self._create_scene_clip(
                    scene, 
                    image_path, 
                    duration,
                    style
                )
                
                # Set audio
                if audio_clip:
                    clip = clip.with_audio(audio_clip)
                    
                scene_clips.append(clip)
            
            # Apply transitions
            final_video = self._apply_transitions(scene_clips)
            
            # Render video
            timestamp = int(time.time())
            safe_title = "".join([c for c in script.title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
            output_path = self.output_dir / f"video_{safe_title}_{timestamp}.mp4"
            
            logger.info("Rendering video...", output_path=str(output_path))
            
            # Run in thread executor to avoid blocking async loop
            import asyncio
            await asyncio.to_thread(
                final_video.write_videofile,
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset=self.preset,
                threads=4,
                logger=None 
            )
            
            # Cleanup
            final_video.close()
            for clip in scene_clips:
                clip.close()
                
            logger.info("Video generated successfully", output_path=str(output_path))
            return str(output_path)
            
        except Exception as e:
            logger.error("Video generation failed", exc_info=True)
            raise

    def _create_scene_clip(
        self,
        scene: Scene,
        image_path: str,
        duration: float,
        style: ImageStyle
    ) -> VideoClip:
        """Create a video clip for a single scene."""
        
        if not os.path.exists(image_path):
            logger.warning("Image not found. Using color placeholder.", image_path=image_path)
            img_clip = ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
        else:
            # Load and resize image
            img_clip = ImageClip(image_path)
            
            # Resize to cover resolution (maintain aspect ratio)
            w, h = img_clip.size
            target_w, target_h = self.resolution
            
            # Calculate scaling to cover
            scale = max(target_w / w, target_h / h)
            img_clip = img_clip.resized(scale)
            
            # Center crop
            img_clip = img_clip.cropped(
                x_center=img_clip.w/2,
                y_center=img_clip.h/2,
                width=target_w,
                height=target_h
            )
        
        # Set duration
        img_clip = img_clip.with_duration(duration)
        
        # Apply Ken Burns effect (slow zoom)
        # Only if duration is reasonable (> 1s)
        if duration > 1.0:
            img_clip = self._apply_ken_burns(img_clip, duration)
        
        # Add text overlay if needed
        if scene.text_overlay:
            try:
                text_clip = self._create_text_overlay_pil(
                    scene.text_overlay,
                    duration,
                    self.resolution
                )
                return CompositeVideoClip([img_clip, text_clip])
            except Exception as e:
                logger.warning("Failed to create text overlay", error=str(e))
                return img_clip
        
        return img_clip
    
    def _apply_ken_burns(self, clip: VideoClip, duration: float) -> VideoClip:
        """Apply Ken Burns effect (slow zoom)."""
        # Zoom factor: 1.0 to 1.1 over duration
        return clip.resized(lambda t: 1 + 0.1 * t / duration)

    def _create_text_overlay_pil(
        self,
        text: str,
        duration: float,
        resolution: Tuple[int, int]
    ) -> VideoClip:
        """Create text overlay using PIL (to avoid ImageMagick dependency)."""
        w, h = resolution
        
        # Create transparent image
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Load font (try default or specific)
        try:
            # Try to find a system font or use default
            font_size = int(h * 0.05) # 5% of height
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
            
        # Calculate text size and position (bottom center)
        # PIL text handling varies by version, simple approximation
        text_w = draw.textlength(text, font=font)
        text_h = font_size # Approx
        
        x = (w - text_w) // 2
        y = h - (h * 0.15) # 15% from bottom
        
        # Draw text with outline/shadow for visibility
        shadow_color = (0, 0, 0, 255)
        text_color = (255, 255, 255, 255)
        
        # Thick outline
        for adj in range(-2, 3):
            for adj2 in range(-2, 3):
                draw.text((x+adj, y+adj2), text, font=font, fill=shadow_color)
                
        draw.text((x, y), text, font=font, fill=text_color)
        
        # Convert to numpy array for MoviePy
        img_np = np.array(img)
        
        # Create ImageClip
        txt_clip = ImageClip(img_np, transparent=True)
        txt_clip = txt_clip.with_duration(duration)
        
        # Fade in/out
        txt_clip = txt_clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
        
        return txt_clip
    
    async def generate_from_text(self, prompt: str) -> str:
        """
        Generate a video from a text prompt (Dev/Test method).
        Generates an image from the prompt, then creates a video with text overlay.
        """
        logger.info("Generating video from text", prompt=prompt)
        
        try:
            # Import ImageGenAgent to generate an image first
            from src.agents.image_gen.agent import ImageGenAgent
            
            # Create a scene for image generation
            scene = Scene(
                scene_number=1,
                scene_type=SceneType.EXPLANATION,
                visual_description=prompt,
                dialogue=None,
                text_overlay=prompt,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt=prompt,
                needs_animation=False,
                transition_to_next=TransitionType.NONE
            )
            
            # Generate image
            logger.info("Generating image for text-to-video", prompt=prompt)
            image_agent = ImageGenAgent()
            image_paths = await image_agent.generate_images([scene])
            image_path = image_paths.get(1)
            
            if not image_path or not os.path.exists(image_path):
                logger.warning("Image generation failed, using color placeholder")
                image_path = "placeholder_for_text_video.jpg"
            else:
                logger.info("Image generated successfully for text-to-video", path=image_path)
            
            # Create video clip
            clip = self._create_scene_clip(
                scene,
                image_path,
                3.0,  # 3 seconds
                ImageStyle.CINEMATIC
            )
            
            # Render
            timestamp = int(time.time())
            output_path = self.output_dir / f"text_gen_{timestamp}.mp4"
            
            clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset=self.preset,
                threads=4,
                logger=None
            )
            
            clip.close()
            logger.info("Text-to-video generation completed", output_path=str(output_path))
            return str(output_path)
            
        except Exception as e:
            logger.error("Failed to generate text video", exc_info=True)
            raise

    def generate_from_image(self, image_path: str, prompt: str) -> str:
        """
        Generate a video from an image and a prompt (Dev/Test method).
        Applies Ken Burns effect to the image.
        """
        logger.info("Generating video from image", image_path=image_path)
        
        try:
            scene = Scene(
                scene_number=1,
                scene_type=SceneType.EXPLANATION,
                visual_description="Image video",
                dialogue=None,
                text_overlay=prompt if prompt else None,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="image",
                needs_animation=False,
                transition_to_next=TransitionType.NONE
            )
            
            clip = self._create_scene_clip(
                scene,
                image_path,
                3.0, # 3 seconds
                ImageStyle.CINEMATIC
            )
            
            timestamp = int(time.time())
            output_path = self.output_dir / f"img_gen_{timestamp}.mp4"
            
            clip.write_videofile(
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset=self.preset,
                threads=4,
                logger=None
            )
            
            clip.close()
            return str(output_path)
            
        except Exception as e:
            logger.error("Failed to generate image video", exc_info=True)
            raise

    def _apply_transitions(self, clips: List[VideoClip]) -> VideoClip:
        """Apply transitions between scene clips."""
        if not clips:
            return None
            
        if len(clips) == 1:
            return clips[0]
            
        transition_duration = 0.5
        
        # Simple concatenation for now to avoid complex crossfade issues with audio
        # Crossfades often require careful audio handling
        return concatenate_videoclips(clips, method="compose")

