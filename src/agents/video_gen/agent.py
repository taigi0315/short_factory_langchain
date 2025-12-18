import os
import asyncio
import time
import structlog
import hashlib
import numpy as np
from typing import List, Tuple, Optional, Any, Dict
from pathlib import Path
from moviepy import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip, ColorClip, VideoClip
)
import moviepy.video.fx as vfx
from PIL import Image, ImageDraw, ImageFont
from src.core.config import settings
from src.core.video_constants import TEXT_OVERLAY, VIDEO_EFFECTS
from src.utils.text_rendering import FontLoader, wrap_text, fit_font_to_width
from src.models.models import (
    VideoScript, Scene, ImageStyle, SceneType, VoiceTone, 
    ElevenLabsSettings, TransitionType, SceneConfig
)

from src.agents.video_gen.providers.base import VideoGenerationProvider
from src.agents.video_gen.providers.mock import MockVideoProvider
from src.agents.video_gen.providers.luma import LumaVideoProvider
from src.agents.video_gen.effects import VideoEffects
from src.agents.video_gen.text_overlay import TextOverlay

logger = structlog.get_logger()

from src.core.retry import retry_with_backoff
from src.agents.base_agent import BaseAgent

# ... imports ...

class VideoGenAgent(BaseAgent):
    def __init__(self) -> None:
        if settings.VIDEO_RESOLUTION == "1080p":
            if settings.IMAGE_ASPECT_RATIO == "16:9":
                self.resolution = (settings.IMAGE_WIDTH_16_9, settings.IMAGE_HEIGHT_16_9) 
            else: 
                self.resolution = (settings.IMAGE_WIDTH_9_16, settings.IMAGE_HEIGHT_9_16)
        else:
            # Fallback for 720p
            self.resolution = (720, 1280) if settings.IMAGE_ASPECT_RATIO == "9:16" else (1280, 720)
        self.fps = settings.VIDEO_FPS
        self.preset = settings.VIDEO_QUALITY
        self.video_provider: Optional[VideoGenerationProvider] = None
        super().__init__(
            agent_name="VideoGenAgent",
            require_llm=False
        )

    def _setup(self) -> None:
        """Agent-specific setup."""
        super()._setup()
        self.output_dir = Path(settings.GENERATED_ASSETS_DIR) / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize video provider
        self.video_provider = self._get_video_provider()
        
        logger.info(
            "VideoGenAgent initialized", 
            resolution=self.resolution,
            fps=self.fps,
            provider=type(self.video_provider).__name__
        )

    def _get_video_provider(self) -> VideoGenerationProvider:
        """Initialize appropriate video provider based on settings."""
        if settings.VIDEO_GENERATION_PROVIDER == "luma" and settings.LUMA_API_KEY:
            return LumaVideoProvider(settings.LUMA_API_KEY)
        return MockVideoProvider()

    def _select_scenes_for_ai_video(self, script: VideoScript) -> List[int]:
        """Select scenes that require AI video generation."""
        return [
            scene.scene_number 
            for scene in script.scenes 
            if scene.needs_animation or scene.video_prompt
        ]

    async def generate_video(
        self,
        script: VideoScript,
        images: List[str],
        audio_map: Dict[int, str],
        style: ImageStyle
    ) -> str:
        """
        Generate complete video from script, images, and audio.
        
        Args:
            script: The video script
            images: List of image paths (one per scene)
            audio_map: Mapping of scene number to audio file path
            style: Visual style for the video
            
        Returns:
            Path to the generated video file
        """
        logger.info("Starting video generation", title=script.title, scenes=len(script.scenes))
        
        scene_clips = []
        
        # Determine which scenes need AI video
        ai_scenes = self._select_scenes_for_ai_video(script)
        
        for i, scene in enumerate(script.scenes):
            image_path = images[i] if i < len(images) else None
            audio_path = audio_map.get(scene.scene_number)
            
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Missing image for scene {scene.scene_number}")
                continue
                
            # Get audio duration
            duration = settings.DEFAULT_SCENE_DURATION
            audio_clip = None
            if audio_path and os.path.exists(audio_path):
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
            
            # Create video clip for scene
            force_ai = scene.scene_number in ai_scenes
            clip = await self._create_scene_clip(
                scene=scene,
                image_path=image_path,
                duration=duration,
                style=style,
                force_ai_video=force_ai
            )
            
            if audio_clip:
                clip = clip.with_audio(audio_clip)
                
            scene_clips.append(clip)
            
        if not scene_clips:
            raise RuntimeError("No scenes were successfully generated")
            
        # Apply transitions
        final_video = self._apply_transitions(scene_clips)
        
        # Add title card if needed (optional, maybe Director handles this?)
        # For now, just render the video
        
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
            logger.error("Failed to render video file", error=str(e))
            raise
            
        # Cleanup
        for clip in scene_clips:
            clip.close()
        final_video.close()
        
        return str(output_path)



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
            
            if force_ai_video and self.video_provider:
                try:
                    logger.info("Generating AI video for scene", scene_number=scene.scene_number, provider=type(self.video_provider).__name__)
                    
                    # Use decorated method for retry logic
                    video_path = await asyncio.wait_for(
                        self._generate_ai_video_with_retry(
                            image_path=image_path,
                            prompt=scene.video_prompt or "Animate this image"
                        ),
                        timeout=300.0 # 5 minutes timeout for video generation
                    )
                    
                    if video_path and os.path.exists(video_path) and video_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm')):
                        logger.info("AI video generated successfully", path=video_path)
                        image_path = video_path
                    else:
                        logger.warning("Provider returned invalid video path or static image, falling back to static/Ken Burns", path=video_path)
                        
                except Exception as gen_error:
                     logger.error("AI video generation failed after retries, falling back to static", error=str(gen_error))
            
            is_video = image_path.lower().endswith(('.mp4', '.mov', '.avi', '.webm'))
            
            # ... rest of the method ...

            if is_video:
                try:
                    logger.debug("Loading video clip", path=image_path)
                    clip = VideoFileClip(image_path)
                    
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
                    
                    if clip.duration < duration:
                        logger.info("Video shorter than audio, freezing last frame", 
                                  video_duration=clip.duration, 
                                  target_duration=duration)
                        remaining = duration - clip.duration
                        frozen = clip.to_ImageClip(t=clip.duration - 0.05).with_duration(remaining)
                        clip = concatenate_videoclips([clip, frozen])
                    else:
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
                try:
                    logger.debug("Loading image", path=image_path)
                    img_clip = ImageClip(image_path)
                    
                    w, h = img_clip.size
                    target_w, target_h = self.resolution
                    
                    logger.debug("Resizing image", 
                               original_size=f"{w}x{h}",
                               target_size=f"{target_w}x{target_h}")
                    
                    scale = min(target_w / w, target_h / h)
                    img_clip = img_clip.resized(scale)
                    
                    if img_clip.w < target_w or img_clip.h < target_h:
                        bg = ColorClip(size=self.resolution, color=(0, 0, 0))
                        x_pos = (target_w - img_clip.w) // 2
                        y_pos = (target_h - img_clip.h) // 2
                        img_clip = CompositeVideoClip([
                            bg.with_duration(1),
                            img_clip.with_position((x_pos, y_pos))
                        ])
                    
                    clip = img_clip.with_duration(duration)
                    
                    effect = scene.selected_effect
                    if not effect and hasattr(scene, 'recommended_effect') and scene.recommended_effect:
                        effect = scene.recommended_effect
                        logger.info("Using recommended effect from Director", 
                                   scene_number=scene.scene_number,
                                   effect=effect)
                    if not effect:
                        effect = "ken_burns_zoom_in"
                        logger.warning("No effect specified, using default", 
                                      scene_number=scene.scene_number,
                                      effect=effect)
                    else:
                        logger.info("Applying effect to scene",
                                   scene_number=scene.scene_number,
                                   effect=effect,
                                   source="selected" if scene.selected_effect else "recommended")
                    
                    logger.debug("Applying effect to image", 
                               scene_number=scene.scene_number,
                               effect=effect)
                    
                    if duration > 1.0:
                        try:
                            clip = self._apply_effect_to_clip(clip, effect, duration)
                            logger.debug("Effect applied successfully",
                                        scene_number=scene.scene_number,
                                        effect=effect)
                        except Exception as effect_error:
                            logger.warning("Effect application failed, using static", 
                                         effect=effect,
                                         error=str(effect_error))
                            
                            
                except Exception as img_error:
                    logger.error("Failed to load/process image, using placeholder",
                               error=str(img_error),
                               image_path=image_path)
                    return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            
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
            return ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
    def _create_title_card(self, title: str, duration: float = 3.0) -> VideoClip:
        """Create a title card with transparent background and colorful centered text at the top."""
        return TextOverlay.create_title_card(title, self.resolution, duration)
    
    def _apply_ken_burns(self, clip: VideoClip, duration: float) -> VideoClip:
        """Apply Ken Burns effect (slow zoom)."""
        return VideoEffects.apply_ken_burns(clip, duration)
    
    def _apply_effect_to_clip(self, clip: VideoClip, effect: str, duration: float) -> VideoClip:
        """
        Apply the specified effect to a video clip.

        Args:
            clip: The video clip to apply effect to
            effect: Effect name (ken_burns_zoom_in, pan_left, tilt_up, etc.)
            duration: Duration of the clip

        Returns:
            Clip with effect applied
        """
        return VideoEffects.apply_effect(clip, effect, duration)


    def _create_text_overlay_pil(
        self,
        text: str,
        duration: float,
        resolution: Tuple[int, int]
    ) -> VideoClip:
        """Create text overlay using PIL with text wrapping and better sizing."""
        return TextOverlay.create_text_overlay(text, resolution, duration)
    
    async def generate_from_text(self, prompt: str) -> str:
        """
        Generate a video from a text prompt (Dev/Test method).
        Generates an image from the prompt, then creates a video with text overlay.
        """
        logger.info("Generating video from text", prompt=prompt)
        
        try:
            # Import ImageGenAgent to generate an image first
            from src.agents.image_gen.agent import ImageGenAgent
            from src.models.models import VisualSegment

            # Create a scene for image generation
            scene = Scene(
                scene_number=1,
                scene_type=SceneType.EXPLANATION,
                content=[VisualSegment(
                    segment_text=prompt,
                    image_prompt=prompt
                )],
                text_overlay=prompt,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
                needs_animation=False,
                transition_to_next=TransitionType.NONE
            )

            # Generate image
            logger.info("Generating image for text-to-video", prompt=prompt)
            image_agent = ImageGenAgent()
            image_paths_dict = await image_agent.generate_images([scene])
            image_paths_list = image_paths_dict.get(1)

            if not image_paths_list or len(image_paths_list) == 0:
                logger.warning("Image generation failed, using color placeholder")
                image_path = "placeholder_for_text_video.jpg"
            else:
                image_path = image_paths_list[0] if isinstance(image_paths_list, list) else image_paths_list
                if not os.path.exists(image_path):
                    logger.warning("Image file not found, using color placeholder")
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
            from src.models.models import VisualSegment

            scene = Scene(
                scene_number=1,
                scene_type=SceneType.EXPLANATION,
                content=[VisualSegment(
                    segment_text=prompt if prompt else "Image video",
                    image_prompt="image"
                )],
                text_overlay=prompt if prompt else None,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
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
        def resolve_path(path_or_url: Optional[str]) -> Optional[str]:
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
                        logger.debug("Loading audio", path=audio_path)
                        audio_clip = AudioFileClip(audio_path)
                        
                        # Speed up audio by 10% (TICKET-027 Issue 6)
                        # 1.1x speed makes narration 10% faster
                        audio_clip = audio_clip.with_effects([vfx.MultiplySpeed(1.1)])
                        
                        duration = audio_clip.duration
                        logger.debug("Audio loaded", duration=duration)
                    else:
                        logger.warning("No audio for scene", scene_number=scene.scene_number)
                        duration = settings.DEFAULT_SCENE_DURATION
                        audio_clip = None
                except Exception as e:
                    logger.error("Error generating audio", error=str(e))
                    duration = settings.DEFAULT_SCENE_DURATION
                    audio_clip = None
            
            if config.use_uploaded_video and video_path and os.path.exists(video_path):
                logger.info("Using uploaded video", scene_number=config.scene_number, path=video_path)
                clip = await self._load_uploaded_video(video_path, duration)
            elif image_path and os.path.exists(image_path):
                logger.info("Using image with effect", 
                           scene_number=config.scene_number,
                           effect=config.effect)
                clip = await self._create_image_clip_with_effect(
                    image_path,
                    config.effect,
                    duration
                )
            else:
                logger.warning("No video or image found, using black screen", 
                             scene_number=config.scene_number,
                             image_path=image_path,
                             video_path=video_path)
                clip = ColorClip(size=self.resolution, color=(0, 0, 0), duration=duration)
            
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
        
        def load_video() -> VideoClip:
            clip = VideoFileClip(video_path)
            
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
            
            if clip.duration < target_duration:
                remaining = target_duration - clip.duration
                frozen = clip.to_ImageClip(t=clip.duration - 0.05).with_duration(remaining)
                clip = concatenate_videoclips([clip, frozen])
            else:
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
        
        def create_clip() -> VideoClip:
            img_clip = ImageClip(image_path)
            
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
            
            if effect == "ken_burns_zoom_in":
                clip = clip.resized(lambda t: 1 + 0.1 * t / duration)
            elif effect == "ken_burns_zoom_out":
                clip = clip.resized(lambda t: 1.1 - 0.1 * t / duration)
            elif effect == "pan_left":
                clip = clip.with_position(lambda t: (-50 * t / duration, 0))
            elif effect == "pan_right":
                clip = clip.with_position(lambda t: (50 * t / duration, 0))
            
            return clip
        
        return await asyncio.to_thread(create_clip)

    def _apply_transitions(self, clips: List[VideoClip]) -> VideoClip:
        """Apply transitions between scene clips."""
        if not clips:
            return None
            
        if len(clips) == 1:
            return clips[0]
            
        transition_duration = 0.5
        
        return concatenate_videoclips(clips, method="compose")


    @retry_with_backoff(operation_name="AI video generation")
    async def _generate_ai_video_with_retry(self, image_path: str, prompt: str) -> Optional[str]:
        """Generate AI video with retry logic."""
        if not self.video_provider:
            return None
        return await self.video_provider.generate_video(
            image_path, 
            prompt
        )
