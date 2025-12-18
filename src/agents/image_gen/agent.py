import os
import asyncio
import structlog
import hashlib
import shutil
import uuid
from typing import List, Dict, Optional
import aiohttp
import aiofiles

from src.models.models import Scene, ImageStyle
from src.agents.director.models import DirectedScript, DirectedScene
from src.core.config import settings
from src.core.exceptions import ImageGenerationError
from src.agents.image_gen.gemini_image_client import GeminiImageClient

logger = structlog.get_logger()

from src.core.retry import retry_with_backoff
from src.agents.base_agent import BaseAgent

class ImageGenAgent(BaseAgent):
    def __init__(self) -> None:
        super().__init__(
            agent_name="ImageGenAgent",
            require_llm=False
        )

    def _setup(self) -> None:
        """Agent-specific setup."""
        self.mock_mode = not settings.USE_REAL_IMAGE
        
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "images")
        self.cache_dir = os.path.join(self.output_dir, "cache")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.api_key = settings.GEMINI_API_KEY
        
        if not self.mock_mode and not self.api_key:
             logger.error("GEMINI_API_KEY not set. Cannot generate images in real mode.")
             raise ValueError(
                 "GEMINI_API_KEY is required for real image generation. "
                 "Set USE_REAL_IMAGE=false to use mock mode, or provide a valid API key."
             )
        
        logger.info(
            "ImageGenAgent setup complete", 
            mode="REAL" if not self.mock_mode else "MOCK"
        )

    async def generate_images(
        self, 
        scenes: List[Scene],
        workflow_id: Optional[str] = None
    ) -> Dict[int, List[str]]:
        """
        Generates images for a list of scenes.
        
        Args:
            scenes: List of scenes to generate images for
            workflow_id: Optional workflow ID for checkpoint saving
            
        Returns:
            Dictionary mapping scene_number to list of local_file_paths
        """
        logger.info("Generating images for scenes", count=len(scenes), workflow_id=workflow_id)
        
        image_paths = {}
        
        if self.mock_mode:
            return await self._generate_mock_images(scenes)
        
        if not self.api_key:
             logger.error("GEMINI_API_KEY not set. Cannot generate images in real mode.")
             raise ValueError(
                 "GEMINI_API_KEY is required for real image generation. "
                 "Set USE_REAL_IMAGE=false to use mock mode, or provide a valid API key."
             )

        async with GeminiImageClient(self.api_key) as client:
            workflow_manager = None
            if workflow_id:
                from src.core.workflow_state import workflow_manager as wf_mgr
                workflow_manager = wf_mgr
            
            for scene in scenes:
                try:
                    # Use the decorated method which handles retries internally
                    scene_image_paths = await self._generate_scene_images(client, scene)
                    image_paths[scene.scene_number] = scene_image_paths
                    
                    if workflow_manager and scene_image_paths and workflow_id:
                        # TODO: Update workflow manager to support list of images
                        workflow_manager.save_image(workflow_id, scene.scene_number, scene_image_paths[0])
                        logger.info("Checkpoint saved", 
                                  workflow_id=workflow_id,
                                  progress=f"{len(image_paths)}/{len(scenes)}")
                    
                    logger.info(
                        "Images generated successfully",
                        scene_number=scene.scene_number,
                        count=len(scene_image_paths)
                    )
                        
                except Exception as e:
                    logger.error(
                        "Image generation failed for scene after retries",
                        scene_number=scene.scene_number,
                        error=str(e)
                    )
                    
                    if workflow_manager and workflow_id:
                        from src.core.workflow_state import WorkflowStep
                        workflow_manager.mark_failed(
                            workflow_id,
                            WorkflowStep.IMAGE_GENERATION,
                            f"Image generation failed for scene {scene.scene_number}: {e}",
                            type(e).__name__
                        )
                    
                    raise RuntimeError(
                        f"Image generation failed for scene {scene.scene_number}: {e}"
                    ) from e
        
        return image_paths

    async def generate_images_from_directed_script(
        self,
        directed_script: DirectedScript,
        workflow_id: Optional[str] = None
    ) -> Dict[int, List[str]]:
        """
        Generates images for a DirectedScript using the Director's enhanced visual segments.
        

        Args:
            directed_script: DirectedScript with cinematic direction
            workflow_id: Optional workflow ID for checkpoint saving
            
        Returns:
            Dictionary mapping scene_number to list of local_file_paths
        """
        logger.info(
            "Generating images from directed script",
            scenes=len(directed_script.directed_scenes),
            workflow_id=workflow_id
        )
        
        enhanced_scenes = []
        for directed_scene in directed_script.directed_scenes:
            scene = directed_scene.original_scene
            
            if directed_scene.visual_segments:
                enhanced_scene = Scene(
                    scene_number=scene.scene_number,
                    scene_type=scene.scene_type,
                    voice_tone=scene.voice_tone,
                    image_style=scene.image_style,
                    content=directed_scene.visual_segments,  # Use Director's enhanced segments
                    elevenlabs_settings=scene.elevenlabs_settings,
                    needs_animation=scene.needs_animation,
                    transition_to_next=scene.transition_to_next
                )
                enhanced_scenes.append(enhanced_scene)
            else:
                enhanced_scenes.append(scene)
        
        return await self.generate_images(enhanced_scenes, workflow_id)

    @retry_with_backoff(operation_name="image generation")
    async def _generate_scene_images(
        self, 
        client: GeminiImageClient, 
        scene: Scene
    ) -> List[str]:
        """Generate one or more images for a single scene based on visual segments."""
        prompts = []
        if scene.content:
            prompts = [seg.image_prompt for seg in scene.content]
        elif scene.image_prompts:
            prompts = scene.image_prompts
        else:
            prompts = [scene.image_create_prompt]
            
        generated_paths = []
        
        for i, prompt in enumerate(prompts):
            enhanced_prompt = self._enhance_prompt_text(prompt, scene.image_style)
            model = self._select_model(scene)
            
            cache_key = self._cache_key(enhanced_prompt, model)
            cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")
            
            if os.path.exists(cache_path):
                logger.info("Using cached image for scene", scene_number=scene.scene_number, index=i)
                filename = f"scene_{scene.scene_number}_{i}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(self.output_dir, filename)
                shutil.copy(cache_path, filepath)
                generated_paths.append(filepath)
                continue

            logger.info("Generating image for scene", scene_number=scene.scene_number, index=i)
            logger.debug("Image prompt", prompt=enhanced_prompt)
            
            try:
                if settings.IMAGE_ASPECT_RATIO == "9:16":
                    width, height = settings.IMAGE_WIDTH_9_16, settings.IMAGE_HEIGHT_9_16
                else:
                    width, height = settings.IMAGE_WIDTH_16_9, settings.IMAGE_HEIGHT_16_9
                
                image_url = await client.generate_image(
                    prompt=enhanced_prompt,
                    model=model,
                    width=width,
                    height=height,
                    aspect_ratio=settings.IMAGE_ASPECT_RATIO,
                )
                
                await client.download_image(image_url, cache_path)
                
                filename = f"scene_{scene.scene_number}_{i}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(self.output_dir, filename)
                shutil.copy(cache_path, filepath)
                
                # Crop to 9:16 if image is square (Gemini generates 1024x1024)
                filepath = self._crop_to_aspect_ratio(filepath, settings.IMAGE_ASPECT_RATIO)
                
                logger.info("Image saved", filepath=filepath)
                generated_paths.append(filepath)
                
            except ImageGenerationError:
                raise  # Re-raise our custom exceptions
            except Exception as e:
                logger.error("Image generation failed", error=str(e))
                raise ImageGenerationError(
                    "Image generation failed",
                    details={"segment": i + 1, "error": str(e)}
                ) from e
                
        return generated_paths

    def _enhance_prompt_text(self, base_prompt: str, style: ImageStyle, global_visual_style: str = "") -> str:
        """Enhance the base prompt with photorealistic style and quality modifiers."""
        prompt = base_prompt or "A cinematic scene"
        
        # Add vertical composition emphasis for 9:16 aspect ratio
        vertical_composition = (
            "vertical 9:16 portrait aspect ratio (1080x1920), CRITICAL: subject MUST be fully visible with complete head/face/body, "
            "centered in frame with significant headroom above subject (at least 20% empty space above head), "
            "wide margins on all sides, zoomed out composition, wide angle shot, "
            "NEVER crop the top of head or face, full body visible from head to toe"
        )
        
        # Add style modifiers based on image_style - emphasize photorealism
        style_enhancers = {
            ImageStyle.CINEMATIC: "photorealistic, cinematic lighting, professional photography, realistic textures, film grain, bokeh, 4k, wide dynamic range",
            ImageStyle.SINGLE_CHARACTER: "photorealistic portrait, professional photography, detailed face, realistic skin texture, studio lighting, centered subject, eye level",
            ImageStyle.CHARACTER_WITH_BACKGROUND: "photorealistic, professional photography, realistic environment, natural lighting, environmental portrait, wide shot showing surroundings",
            ImageStyle.INFOGRAPHIC: "clean infographic overlay on photorealistic background, professional design, data visualization, modern graphics, clear typography, centered layout",
            ImageStyle.DIAGRAM_EXPLANATION: "photorealistic scene with clean diagram overlay, professional photography, educational graphics, clear visual explanation",
            ImageStyle.BEFORE_AFTER_COMPARISON: "photorealistic split-screen comparison, professional photography, realistic before and after, clear distinction",
            ImageStyle.STEP_BY_STEP_VISUAL: "photorealistic step-by-step sequence, professional photography, realistic demonstration, sequential layout",
            ImageStyle.COMIC_PANEL: "photorealistic scene with comic-style framing, professional photography, cinematic composition, dramatic angles",
            ImageStyle.CLOSE_UP_REACTION: "photorealistic close-up, professional portrait photography, detailed facial features, emotional expression, centered face",
            ImageStyle.WIDE_ESTABLISHING_SHOT: "photorealistic extreme wide shot, professional landscape photography, cinematic establishing shot, realistic environment, panoramic view",
            ImageStyle.SPLIT_SCREEN: "photorealistic split-screen, professional photography, realistic dual perspective, balanced composition",
        }
        

        style_suffix = style_enhancers.get(
            style, 
            "photorealistic, high quality, professional photography, realistic lighting and textures, cinematic"
        )
        

        quality_suffix = "8k uhd, sharp focus, professional photography, photorealistic, realistic details, natural lighting, high resolution"
        
        # Build enhanced prompt with global visual style if provided
        enhanced = f"{prompt}, {vertical_composition}, {style_suffix}, {quality_suffix}"
        
        # Append global visual style for consistency across all images
        if global_visual_style:
            enhanced = f"{enhanced}, {global_visual_style}"
        
        return enhanced

    def _enhance_prompt(self, scene: Scene) -> str:
        """Legacy wrapper for backward compatibility if needed."""
        return self._enhance_prompt_text(scene.image_create_prompt, scene.image_style)
    
    def _crop_to_aspect_ratio(self, filepath: str, target_aspect: str) -> str:
        """
        Crop image to target aspect ratio.
        Gemini generates 1024x1024 square images, so we need to crop to 9:16 for vertical video.
        
        Args:
            filepath: Path to the image file
            target_aspect: Target aspect ratio (e.g., "9:16", "16:9", "1:1")
            
        Returns:
            Path to the cropped image (same filepath, modified in place)
        """
        from PIL import Image
        
        # Parse aspect ratio
        if ":" not in target_aspect:
            logger.warning(f"Invalid aspect ratio format: {target_aspect}, skipping crop")
            return filepath
        
        try:
            width_ratio, height_ratio = map(int, target_aspect.split(":"))
        except ValueError:
            logger.warning(f"Could not parse aspect ratio: {target_aspect}, skipping crop")
            return filepath
        
        # Open image
        try:
            img = Image.open(filepath)
            current_width, current_height = img.size
            
            logger.info(f"Cropping image from {current_width}x{current_height} to {target_aspect} aspect ratio")
            
            # Calculate target dimensions
            current_aspect = current_width / current_height
            target_aspect_value = width_ratio / height_ratio
            
            if abs(current_aspect - target_aspect_value) < 0.01:
                # Already correct aspect ratio
                logger.info("Image already has correct aspect ratio, skipping crop")
                return filepath
            
            # Determine crop dimensions
            if current_aspect > target_aspect_value:
                # Image is too wide, crop width
                new_width = int(current_height * target_aspect_value)
                new_height = current_height
                left = (current_width - new_width) // 2
                top = 0
                right = left + new_width
                bottom = current_height
            else:
                # Image is too tall, crop height
                new_width = current_width
                new_height = int(current_width / target_aspect_value)
                left = 0
                
                # Smart Crop for Portraits (keep top)
                # If target is vertical (e.g. 9:16), bias crop to top to keep heads visible
                if target_aspect_value < 0.8:
                    top = 0
                else:
                    top = (current_height - new_height) // 2
                    
                right = current_width
                bottom = top + new_height
            
            # Crop image
            cropped_img = img.crop((left, top, right, bottom))
            
            # Save cropped image (overwrite original)
            cropped_img.save(filepath)
            logger.info(f"Image cropped to {cropped_img.size[0]}x{cropped_img.size[1]}")
            
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to crop image: {e}, using original")
            return filepath

    def _select_model(self, scene: Scene) -> str:
        """Select appropriate model based on scene requirements."""
        # For now, default to stable-diffusion-xl for best quality
        return "stable-diffusion-xl"

    def _cache_key(self, prompt: str, model: str) -> str:
        return hashlib.sha256(f"{prompt}:{model}".encode()).hexdigest()[:16]

    async def _generate_mock_images(self, scenes: List[Scene]) -> Dict[int, List[str]]:
        """Generate mock images for all scenes."""
        image_paths = {}
        for scene in scenes:
            count = len(scene.image_prompts) if scene.image_prompts else 1
            scene_paths = []
            for i in range(count):
                path = await self._generate_placeholder(scene, index=i)
                scene_paths.append(path)
            image_paths[scene.scene_number] = scene_paths
        return image_paths

    async def _generate_placeholder(self, scene: Scene, index: int = 0) -> str:
        """Generate a placeholder image using placehold.co."""
        filename = f"scene_{scene.scene_number}_{index}_placeholder.png"
        filepath = os.path.join(self.output_dir, filename)
        
        base_prompt = scene.image_prompts[index] if scene.image_prompts and index < len(scene.image_prompts) else scene.image_create_prompt
        
        prompt_slug = (
            base_prompt[:20].replace(" ", "+")
            if base_prompt
            else "scene"
        )
        image_url = (
            f"https://placehold.co/1280x720/2563eb/ffffff/png?text=Scene+{scene.scene_number}-{index}:{prompt_slug}"
        )
        
        try:
            await self._download_async(image_url, filepath)
            return filepath
        except Exception as e:
            logger.error("Failed to download mock image", error=str(e))

            async with aiofiles.open(filepath, "wb") as f:
                await f.write(b"Placeholder")
            return filepath

    async def _download_async(self, url: str, filepath: str) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(filepath, "wb") as f:
                        await f.write(content)
                else:
                    raise RuntimeError(f"Download failed with status {response.status}")

