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

from src.agents.video_gen.providers.base import VideoGenerationProvider
from src.agents.video_gen.providers.mock import MockVideoProvider
from src.agents.video_gen.providers.luma import LumaVideoProvider

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
        
        # Resolution settings - VERTICAL for YouTube Shorts (9:16 aspect ratio)
        # Format: (width, height) - portrait orientation
        self.resolution = (1080, 1920) if settings.VIDEO_RESOLUTION == "1080p" else (720, 1280)
        self.fps = settings.VIDEO_FPS
        self.preset = settings.VIDEO_QUALITY
        
        # Initialize video generation provider
        self.video_provider = self._get_video_provider()

    def _get_video_provider(self) -> VideoGenerationProvider:
        """Get the configured video generation provider."""
        provider_name = settings.VIDEO_GENERATION_PROVIDER.lower()
        
        if provider_name == "luma":
            logger.info("Using Luma Video Provider")
            return LumaVideoProvider()
        elif provider_name == "runway":
            logger.warning("Runway provider not implemented, falling back to mock")
            return MockVideoProvider()
        else:
            logger.info("Using Mock Video Provider (Simple Animation)")
            return MockVideoProvider()

    def _select_scenes_for_ai_video(self, scenes: List[Scene]) -> set[int]:
        """
        Select which scenes should get AI video generation based on video_importance.
        
        Returns a set of scene_numbers that should use AI video generation.
        """
        max_ai_videos = settings.MAX_AI_VIDEOS_PER_SCRIPT
        
        if max_ai_videos <= 0:
            logger.info("AI video generation disabled (MAX_AI_VIDEOS_PER_SCRIPT=0)")
            return set()
        
        # Filter scenes that need animation
        animation_scenes = [s for s in scenes if s.needs_animation]
        
        if not animation_scenes:
            logger.info("No scenes marked for animation")
            return set()
        
        # Sort by video_importance (descending), then by scene_number for tie-breaking
        sorted_scenes = sorted(
            animation_scenes,
            key=lambda s: (s.video_importance, -s.scene_number),
            reverse=True
        )
        
        # Select top N scenes
        selected_scenes = sorted_scenes[:max_ai_videos]
        selected_numbers = {s.scene_number for s in selected_scenes}
        
        logger.info("Scene selection for AI video",
                   total_animation_scenes=len(animation_scenes),
                   max_allowed=max_ai_videos,
                   selected_count=len(selected_numbers),
                   selected_scenes=[
                       {"scene": s.scene_number, "importance": s.video_importance}
                       for s in selected_scenes
                   ])
        
        return selected_numbers

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
            # Determine which scenes should get AI video generation
            ai_video_scene_numbers = self._select_scenes_for_ai_video(script.scenes)
            logger.info("Selected scenes for AI video generation", 
                       scene_numbers=ai_video_scene_numbers,
                       max_allowed=settings.MAX_AI_VIDEOS_PER_SCRIPT)
            
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
                    duration = settings.DEFAULT_SCENE_DURATION
                    audio_clip = None
                else:
                    audio_clip = AudioFileClip(audio_path)
                    duration = audio_clip.duration
                
                # Determine if this scene should use AI video generation
                should_use_ai_video = scene.scene_number in ai_video_scene_numbers
                
                # Create visual clip
                clip = await self._create_scene_clip(
                    scene, 
                    image_path, 
                    duration,
                    style,
                    force_ai_video=should_use_ai_video
                )
                
                # Set audio
                if audio_clip:
                    clip = clip.with_audio(audio_clip)
                    
                scene_clips.append(clip)
            
            # Add title card at the beginning
            title_card = self._create_title_card(script.title, duration=3.0)
            scene_clips.insert(0, title_card)
            
            # Apply transitions
            final_video = self._apply_transitions(scene_clips)
            
            # Render video
            timestamp = int(time.time())
            safe_title = "".join([c for c in script.title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
            output_path = self.output_dir / f"video_{safe_title}_{timestamp}.mp4"
            
            logger.info("Rendering video...", output_path=str(output_path))
            
            # Run in thread executor to avoid blocking async loop
            import asyncio
            try:
                await asyncio.to_thread(
                    final_video.write_videofile,
                    str(output_path),
                    fps=self.fps,
                    codec='libx264',
                    audio_codec='aac',
                    preset=self.preset,
                    logger=None 
                )
                
                # Verify the file was created
                if not os.path.exists(output_path):
                    raise RuntimeError(f"Video file was not created at {output_path}")
                    
                file_size = os.path.getsize(output_path)
                logger.info("Video file created", path=str(output_path), size_bytes=file_size)
                
            except Exception as render_error:
                logger.error("Video rendering failed", 
                           error=str(render_error),
                           error_type=type(render_error).__name__,
                           output_path=str(output_path),
                           exc_info=True)
                raise RuntimeError(f"Failed to render video: {str(render_error)}") from render_error
            
            # Cleanup
            try:
                final_video.close()
                for clip in scene_clips:
                    clip.close()
            except Exception as cleanup_error:
                logger.warning("Error during clip cleanup", error=str(cleanup_error))
                
            logger.info("Video generated successfully", output_path=str(output_path))
            return str(output_path)
            
        except Exception as e:
            logger.error("Video generation failed", exc_info=True, error_type=type(e).__name__)
            raise

    async def _create_scene_clip(
        self,
        scene: Scene,
        image_path: str,
        duration: float,
        style: ImageStyle,
        force_ai_video: bool = False
    ) -> VideoClip:
        """Create a video clip for a single scene.
        
        Args:
            scene: Scene configuration
            image_path: Path to the image file
            duration: Duration of the clip in seconds
            style: Image style
            force_ai_video: If True, attempt AI video generation regardless of needs_animation
        """
        
        try:
            if not os.path.exists(image_path):
                logger.warning("Image/Video not found. Using color placeholder.", image_path=image_path)
                return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            
            # AI Video Generation (Image-to-Video)
            # Only generate AI video if this scene was selected based on importance
            if force_ai_video and self.video_provider:
                try:
                    logger.info("Generating AI video for scene", scene_number=scene.scene_number, provider=type(self.video_provider).__name__)
                    
                    # Generate video using provider
                    video_path = await self.video_provider.generate_video(
                        image_path, 
                        scene.video_prompt or "Animate this image"
                    )
                    
                    # If provider returned a valid video path, use it
                    if video_path and os.path.exists(video_path) and video_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                        logger.info("AI video generated successfully", path=video_path)
                        image_path = video_path
                        # Continue to video processing logic below
                    else:
                        logger.warning("Provider returned invalid video path or static image, falling back to static/Ken Burns", path=video_path)
                        # If it returned the image path (Mock), we just fall through to static handling
                        
                except Exception as gen_error:
                     logger.error("AI video generation failed, falling back to static", error=str(gen_error))
            
            # Check if it's a video file (either original or generated)
            is_video = image_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm'))
            
            if is_video:
                try:
                    logger.debug("Loading video clip", path=image_path)
                    clip = VideoFileClip(image_path)
                    
                    # Resize and crop video to fill screen
                    w, h = clip.size
                    target_w, target_h = self.resolution
                    
                    scale = max(target_w / w, target_h / h)
                    clip = clip.resized(scale)
                    clip = clip.cropped(
                        x_center=clip.w/2,
                        y_center=clip.h/2,
                        width=target_w,
                        height=target_h
                    )
                    
                    # Sync duration
                    if clip.duration < duration:
                        # Freeze last frame
                        logger.info("Video shorter than audio, freezing last frame", 
                                  video_duration=clip.duration, 
                                  target_duration=duration)
                        remaining = duration - clip.duration
                        frozen = clip.to_ImageClip(t=clip.duration - 0.05).with_duration(remaining)
                        clip = concatenate_videoclips([clip, frozen])
                    else:
                        # Trim
                        logger.info("Video longer than audio, trimming", 
                                  video_duration=clip.duration, 
                                  target_duration=duration)
                        clip = clip.subclipped(0, duration)
                        
                except Exception as vid_error:
                    logger.error("Failed to load/process video, falling back to placeholder",
                               error=str(vid_error),
                               path=image_path)
                    return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            else:
                # Image handling
                try:
                    # Load and resize image
                    logger.debug("Loading image", path=image_path)
                    img_clip = ImageClip(image_path)
                    
                    # Resize to cover resolution (maintain aspect ratio)
                    w, h = img_clip.size
                    target_w, target_h = self.resolution
                    
                    logger.debug("Resizing image", 
                               original_size=f"{w}x{h}",
                               target_size=f"{target_w}x{target_h}")
                    
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
                    clip = img_clip.with_duration(duration)
                    
                    # Apply Ken Burns effect (slow zoom)
                    # Only if duration is reasonable (> 1s)
                    if duration > 1.0:
                        try:
                            clip = self._apply_ken_burns(clip, duration)
                        except Exception as kb_error:
                            logger.warning("Ken Burns effect failed, skipping", error=str(kb_error))
                            
                except Exception as img_error:
                    logger.error("Failed to load/process image, using placeholder",
                               error=str(img_error),
                               image_path=image_path)
                    return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            
            # Add text overlay if needed
            if scene.text_overlay:
                try:
                    text_clip = self._create_text_overlay_pil(
                        scene.text_overlay,
                        duration,
                        self.resolution
                    )
                    return CompositeVideoClip([clip, text_clip])
                except Exception as text_error:
                    logger.warning("Failed to create text overlay, skipping", error=str(text_error))
                    return clip
            
            return clip
            
        except Exception as e:
            logger.error("Scene clip creation failed", 
                       scene_number=scene.scene_number,
                       error=str(e),
                       exc_info=True)
            # Return a simple black clip as last resort
            return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
    
    def _create_title_card(self, title: str, duration: float = 3.0) -> VideoClip:
        """Create a title card with black background and centered text."""
        w, h = self.resolution
        
        # Black background
        bg = ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
        
        # Create title text
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Larger font for title - 5% of height
        font_size = int(h * 0.05)
        
        try:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Wrap title text
        max_width = int(w * 0.85)
        lines = self._wrap_text(title, font, max_width, draw)
        
        # Calculate positioning (center of screen)
        line_height = int(font_size * 1.3)
        total_height = len(lines) * line_height
        start_y = (h - total_height) // 2
        
        # Draw title with outline
        text_color = (255, 255, 255, 255)
        shadow_color = (50, 50, 50, 255)
        
        for i, line in enumerate(lines):
            line_w = draw.textlength(line, font=font)
            x = (w - line_w) // 2
            y = start_y + (i * line_height)
            
            # Subtle outline
            for adj in range(-2, 3):
                for adj2 in range(-2, 3):
                    if adj != 0 or adj2 != 0:
                        draw.text((x+adj, y+adj2), line, font=font, fill=shadow_color)
            
            draw.text((x, y), line, font=font, fill=text_color)
        
        # Convert to clip
        img_np = np.array(img)
        title_clip = ImageClip(img_np, transparent=True).with_duration(duration)
        
        # Composite over black background with fade
        title_clip = title_clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])
        
        return CompositeVideoClip([bg, title_clip])
    
    def _apply_ken_burns(self, clip: VideoClip, duration: float) -> VideoClip:
        """Apply Ken Burns effect (slow zoom)."""
        # Zoom factor: 1.0 to 1.1 over duration
        return clip.resized(lambda t: 1 + 0.1 * t / duration)


    def _wrap_text(self, text: str, font, max_width: int, draw) -> List[str]:
        """Wrap text to fit within max_width."""
        words = text.split()
        lines = []
        current_line = []
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_width = draw.textlength(test_line, font=font)
            
            if test_width <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines if lines else [text]

    def _create_text_overlay_pil(
        self,
        text: str,
        duration: float,
        resolution: Tuple[int, int]
    ) -> VideoClip:
        """Create text overlay using PIL with text wrapping and better sizing."""
        w, h = resolution
        
        # Create transparent image
        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        
        # Smaller font size - 3% of height instead of 5%
        font_size = int(h * 0.03)
        
        # Load font
        try:
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
                except:
                    font = ImageFont.load_default()
        except:
            font = ImageFont.load_default()
        
        # Text wrapping - use 90% of width for safety
        max_width = int(w * 0.9)
        lines = self._wrap_text(text, font, max_width, draw)
        
        # Calculate total text block height
        line_height = int(font_size * 1.2)  # 20% line spacing
        total_text_height = len(lines) * line_height
        
        # Position at 80% from top (20% from bottom)
        start_y = int(h * 0.80) - (total_text_height // 2)
        
        # Draw text with outline/shadow for visibility
        shadow_color = (0, 0, 0, 255)
        text_color = (255, 255, 255, 255)
        
        for i, line in enumerate(lines):
            # Center each line
            line_w = draw.textlength(line, font=font)
            x = (w - line_w) // 2
            y = start_y + (i * line_height)
            
            # Thick outline for readability
            for adj in range(-3, 4):
                for adj2 in range(-3, 4):
                    if adj != 0 or adj2 != 0:  # Skip center
                        draw.text((x+adj, y+adj2), line, font=font, fill=shadow_color)
            
            # Main text
            draw.text((x, y), line, font=font, fill=text_color)
        
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
            clip = await self._create_scene_clip(
                scene,
                image_path,
                settings.DEFAULT_SCENE_DURATION,
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
                logger=None
            )
            
            clip.close()
            logger.info("Text-to-video generation completed", output_path=str(output_path))
            return str(output_path)
            
        except Exception as e:
            logger.error("Failed to generate text video", exc_info=True)
            raise

    async def generate_from_image(self, image_path: str, prompt: str) -> str:
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
            
            clip = await self._create_scene_clip(
                scene,
                image_path,
                settings.DEFAULT_SCENE_DURATION,
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
                logger=None
            )
            
            clip.close()
            return str(output_path)
            
        except Exception as e:
            logger.error("Failed to generate image video", exc_info=True)
            raise

    async def build_from_scene_configs(
        self,
        script: VideoScript,
        scene_configs: List['SceneConfig']  # Import from models
    ) -> str:
        """
        Build video using mix of uploaded videos and image+effect.
        
        Args:
            script: The video script
            scene_configs: Configuration for each scene
            
        Returns:
            Path to final video
        """
        from src.models.models import SceneConfig
        from src.agents.voice.agent import VoiceAgent
        import asyncio
        
        logger.info("Building video from scene configurations", 
                   total_scenes=len(scene_configs),
                   title=script.title)
        
        scene_clips = []
        voice_agent = VoiceAgent()
        
        # Helper to resolve path
        def resolve_path(path_or_url: str) -> str:
            if not path_or_url:
                return None
            if path_or_url.startswith("/generated_assets/"):
                # Convert URL to local path
                rel_path = path_or_url.replace("/generated_assets/", "", 1)
                return str(Path(settings.GENERATED_ASSETS_DIR) / rel_path)
            if os.path.exists(path_or_url):
                return path_or_url
            # Try relative to GENERATED_ASSETS_DIR
            try_path = Path(settings.GENERATED_ASSETS_DIR) / path_or_url
            if try_path.exists():
                return str(try_path)
            return path_or_url

        for config in scene_configs:
            # Find matching scene
            scene = next((s for s in script.scenes if s.scene_number == config.scene_number), None)
            if not scene:
                logger.warning("Scene not found in script", scene_number=config.scene_number)
                continue
            
            # Resolve paths
            video_path = resolve_path(config.video_path)
            image_path = resolve_path(config.image_path)
            audio_path = resolve_path(config.audio_path)
            
            # Get audio duration
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
            else:
                # Generate audio if missing
                logger.info("Generating missing audio for scene", scene_number=config.scene_number)
                try:
                    _, audio_path = await voice_agent._generate_single_voiceover(scene)
                    if audio_path and os.path.exists(audio_path):
                        audio_clip = AudioFileClip(audio_path)
                        duration = audio_clip.duration
                    else:
                        logger.warning("Failed to generate audio, using default duration")
                        duration = settings.DEFAULT_SCENE_DURATION
                        audio_clip = None
                except Exception as e:
                    logger.error("Error generating audio", error=str(e))
                    duration = settings.DEFAULT_SCENE_DURATION
                    audio_clip = None
            
            # Create visual clip
            if config.use_uploaded_video and video_path and os.path.exists(video_path):
                # Use uploaded video
                logger.info("Using uploaded video", scene_number=config.scene_number, path=video_path)
                clip = await self._load_uploaded_video(video_path, duration)
            elif image_path and os.path.exists(image_path):
                # Use image + effect
                logger.info("Using image with effect", 
                           scene_number=config.scene_number,
                           effect=config.effect)
                clip = await self._create_image_clip_with_effect(
                    image_path,
                    config.effect,
                    duration
                )
            else:
                # Fallback to black screen
                logger.warning("No video or image found, using black screen", 
                             scene_number=config.scene_number,
                             image_path=image_path,
                             video_path=video_path)
                clip = ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            
            # Add audio
            if audio_clip:
                clip = clip.with_audio(audio_clip)
            
            scene_clips.append(clip)
        
        if not scene_clips:
            raise RuntimeError("No scene clips created")
        
        # Apply transitions and render
        final_video = self._apply_transitions(scene_clips)
        
        # Render
        timestamp = int(time.time())
        safe_title = "".join([c for c in script.title if c.isalnum() or c in (' ', '-', '_')]).strip().replace(' ', '_')
        output_path = self.output_dir / f"video_{safe_title}_{timestamp}.mp4"
        
        logger.info("Rendering final video...", output_path=str(output_path))
        
        try:
            await asyncio.to_thread(
                final_video.write_videofile,
                str(output_path),
                fps=self.fps,
                codec='libx264',
                audio_codec='aac',
                preset=self.preset,
                logger=None
            )
        except Exception as e:
            logger.error("Failed to render video file", error=str(e), output_path=str(output_path))
            raise
        
        logger.info("Video built successfully", output_path=str(output_path))
        
        # Cleanup
        for clip in scene_clips:
            clip.close()
        final_video.close()
        
        return str(output_path)

    async def _load_uploaded_video(self, video_path: str, target_duration: float) -> VideoClip:
        """Load and process uploaded video"""
        import asyncio
        
        def load_video():
            clip = VideoFileClip(video_path)
            
            # Resize to target resolution
            w, h = clip.size
            target_w, target_h = self.resolution
            scale = max(target_w / w, target_h / h)
            clip = clip.resized(scale)
            clip = clip.cropped(
                x_center=clip.w/2,
                y_center=clip.h/2,
                width=target_w,
                height=target_h
            )
            
            # Sync duration
            if clip.duration < target_duration:
                # Freeze last frame
                remaining = target_duration - clip.duration
                frozen = clip.to_ImageClip(t=clip.duration - 0.05).with_duration(remaining)
                clip = concatenate_videoclips([clip, frozen])
            else:
                # Trim
                clip = clip.subclipped(0, target_duration)
            
            return clip
        
        return await asyncio.to_thread(load_video)

    async def _create_image_clip_with_effect(
        self,
        image_path: str,
        effect: str,
        duration: float
    ) -> VideoClip:
        """Create video clip from image with specified effect"""
        import asyncio
        
        def create_clip():
            img_clip = ImageClip(image_path)
            
            # Resize to cover resolution
            w, h = img_clip.size
            target_w, target_h = self.resolution
            scale = max(target_w / w, target_h / h)
            img_clip = img_clip.resized(scale)
            img_clip = img_clip.cropped(
                x_center=img_clip.w/2,
                y_center=img_clip.h/2,
                width=target_w,
                height=target_h
            )
            
            clip = img_clip.with_duration(duration)
            
            # Apply effect
            if effect == "ken_burns_zoom_in":
                clip = clip.resized(lambda t: 1 + 0.1 * t / duration)
            elif effect == "ken_burns_zoom_out":
                clip = clip.resized(lambda t: 1.1 - 0.1 * t / duration)
            elif effect == "pan_left":
                clip = clip.with_position(lambda t: (-50 * t / duration, 0))
            elif effect == "pan_right":
                clip = clip.with_position(lambda t: (50 * t / duration, 0))
            # "static" - no effect
            
            return clip
        
        return await asyncio.to_thread(create_clip)

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

