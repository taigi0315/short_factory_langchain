import os
import asyncio
import structlog
import hashlib
import shutil
import uuid
from typing import List, Dict, Optional
import requests

from src.models.models import Scene, ImageStyle
from src.agents.director.models import DirectedScript, DirectedScene
from src.core.config import settings
from src.agents.image_gen.gemini_image_client import GeminiImageClient

logger = structlog.get_logger()

class ImageGenAgent:
    def __init__(self):
        # Use centralized config
        self.mock_mode = not settings.USE_REAL_IMAGE
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "images")
        self.cache_dir = os.path.join(self.output_dir, "cache")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # API configuration - use Gemini for image generation
        self.api_key = settings.GEMINI_API_KEY

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
        
        # Real mode - use Gemini
        if not self.api_key:
             logger.error("GEMINI_API_KEY not set. Cannot generate images in real mode.")
             raise ValueError(
                 "GEMINI_API_KEY is required for real image generation. "
                 "Set USE_REAL_IMAGE=false to use mock mode, or provide a valid API key."
             )

        client = GeminiImageClient(self.api_key)
        
        # Import workflow manager if workflow_id provided
        workflow_manager = None
        if workflow_id:
            from src.core.workflow_state import workflow_manager as wf_mgr
            workflow_manager = wf_mgr
        
        # Generate images one by one to enable incremental checkpoints
        for scene in scenes:
            # Retry logic: up to 3 attempts with exponential backoff
            max_retries = 3
            last_error = None
            
            for attempt in range(1, max_retries + 1):
                try:
                    logger.info(
                        "Generating images for scene (attempt {}/{})".format(attempt, max_retries),
                        scene_number=scene.scene_number,
                        attempt=attempt
                    )
                    
                    scene_image_paths = await self._generate_scene_images(client, scene)
                    image_paths[scene.scene_number] = scene_image_paths
                    
                    # Save checkpoint after each successful scene (saving the first image as representative or all?)
                    # Workflow manager might expect a single path or we need to update it too.
                    # For now, let's assume we save the first image path for simple checkpointing, 
                    # or update workflow manager later. 
                    # If we pass a list to save_image, it might break if it expects str.
                    # Let's check workflow_manager usage. It's imported dynamically.
                    # Assuming for now we just save the first one or skip if complex.
                    if workflow_manager and scene_image_paths:
                        # TODO: Update workflow manager to support list of images
                        workflow_manager.save_image(workflow_id, scene.scene_number, scene_image_paths[0])
                        logger.info("Checkpoint saved", 
                                  workflow_id=workflow_id,
                                  progress=f"{len(image_paths)}/{len(scenes)}")
                    
                    # Success! Break out of retry loop
                    logger.info(
                        "Images generated successfully",
                        scene_number=scene.scene_number,
                        count=len(scene_image_paths),
                        attempt=attempt
                    )
                    break
                    
                except Exception as e:
                    last_error = e
                    logger.warning(
                        "Image generation failed for scene (attempt {}/{})".format(attempt, max_retries),
                        scene_number=scene.scene_number,
                        attempt=attempt,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    
                    # If this was the last attempt, handle failure
                    if attempt == max_retries:
                        logger.error(
                            "All retry attempts exhausted for scene",
                            scene_number=scene.scene_number,
                            total_attempts=max_retries,
                            final_error=str(e)
                        )
                        
                        # Save failure state if workflow tracking is enabled
                        if workflow_manager:
                            from src.core.workflow_state import WorkflowStep
                            workflow_manager.mark_failed(
                                workflow_id,
                                WorkflowStep.IMAGE_GENERATION,
                                f"Image generation failed for scene {scene.scene_number} after {max_retries} attempts: {e}",
                                type(e).__name__
                            )
                        
                        # Raise the error to stop video generation
                        raise RuntimeError(
                            f"Image generation failed for scene {scene.scene_number} after {max_retries} attempts: {e}"
                        ) from e
                    else:
                        # Wait before retrying (exponential backoff: 2s, 4s)
                        wait_time = 2 ** attempt
                        logger.info(
                            f"Waiting {wait_time}s before retry...",
                            scene_number=scene.scene_number,
                            wait_seconds=wait_time
                        )
                        await asyncio.sleep(wait_time)
        
        return image_paths

    async def generate_images_from_directed_script(
        self,
        directed_script: DirectedScript,
        workflow_id: Optional[str] = None
    ) -> Dict[int, List[str]]:
        """
        Generates images for a DirectedScript using the Director's enhanced visual segments.
        
        TICKET-035: This method uses the Director Agent's enhanced image prompts from
        DirectedScene.visual_segments instead of the Script Writer's basic descriptions.
        
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
        
        # Create temporary Scene objects with Director's enhanced visual segments
        # This allows us to reuse the existing generate_images infrastructure
        enhanced_scenes = []
        for directed_scene in directed_script.directed_scenes:
            # Copy the original scene
            scene = directed_scene.original_scene
            
            # Override content with Director's enhanced visual segments
            if directed_scene.visual_segments:
                # Create a new Scene with the enhanced segments
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
                # Fallback to original scene if no visual segments
                enhanced_scenes.append(scene)
        
        # Delegate to existing generate_images method
        return await self.generate_images(enhanced_scenes, workflow_id)

    async def _generate_scene_images(
        self, 
        client: GeminiImageClient, 
        scene: Scene
    ) -> List[str]:
        """Generate one or more images for a single scene based on visual segments."""
        prompts = []
        # Use content segments if available (TICKET-033)
        if scene.content:
            prompts = [seg.image_prompt for seg in scene.content]
        # Fallback for backward compatibility or if content is empty (shouldn't happen with new prompt)
        elif scene.image_prompts:
            prompts = scene.image_prompts
        else:
            prompts = [scene.image_create_prompt]
            
        generated_paths = []
        
        for i, prompt in enumerate(prompts):
            # Create a temporary scene object or just pass prompt to helper if refactored
            # But _enhance_prompt takes a Scene. 
            # We should probably refactor _enhance_prompt or just temporarily modify the scene object 
            # (which is risky if async/parallel, but here we are sequential per scene).
            # Better: Create a helper that takes prompt + style.
            
            enhanced_prompt = self._enhance_prompt_text(prompt, scene.image_style)
            model = self._select_model(scene)
            
            # Check cache
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
                    width, height = 1080, 1920
                else:
                    width, height = 1920, 1080
                
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
                
                logger.info("Image saved", filepath=filepath)
                generated_paths.append(filepath)
                
            except Exception as e:
                logger.error("Image generation failed", error=str(e))
                raise
                
        return generated_paths

    def _enhance_prompt_text(self, base_prompt: str, style: ImageStyle) -> str:
        """Enhance the base prompt with photorealistic style and quality modifiers."""
        prompt = base_prompt or "A cinematic scene"
        
        # Add style modifiers based on image_style - emphasize photorealism
        style_enhancers = {
            ImageStyle.CINEMATIC: "photorealistic, cinematic lighting, professional photography, realistic textures, film grain, bokeh, 4k",
            ImageStyle.SINGLE_CHARACTER: "photorealistic portrait, professional photography, detailed face, realistic skin texture, studio lighting",
            ImageStyle.CHARACTER_WITH_BACKGROUND: "photorealistic, professional photography, realistic environment, natural lighting",
            ImageStyle.INFOGRAPHIC: "clean infographic overlay on photorealistic background, professional design, data visualization, modern graphics",
            ImageStyle.DIAGRAM_EXPLANATION: "photorealistic scene with clean diagram overlay, professional photography, educational graphics",
            ImageStyle.BEFORE_AFTER_COMPARISON: "photorealistic split-screen comparison, professional photography, realistic before and after",
            ImageStyle.STEP_BY_STEP_VISUAL: "photorealistic step-by-step sequence, professional photography, realistic demonstration",
            ImageStyle.COMIC_PANEL: "photorealistic scene with comic-style framing, professional photography, cinematic composition",
            ImageStyle.CLOSE_UP_REACTION: "photorealistic close-up, professional portrait photography, detailed facial features, emotional expression",
            ImageStyle.WIDE_ESTABLISHING_SHOT: "photorealistic wide shot, professional landscape photography, cinematic establishing shot, realistic environment",
            ImageStyle.SPLIT_SCREEN: "photorealistic split-screen, professional photography, realistic dual perspective",
        }
        
        # Default to photorealistic cinematic if style not found
        style_suffix = style_enhancers.get(
            style, 
            "photorealistic, high quality, professional photography, realistic lighting and textures, cinematic"
        )
        
        # Add quality modifiers emphasizing realism
        quality_suffix = "8k uhd, sharp focus, professional photography, photorealistic, realistic details, natural lighting"
        
        enhanced = f"{prompt}, {style_suffix}, {quality_suffix}"
        return enhanced

    def _enhance_prompt(self, scene: Scene) -> str:
        """Legacy wrapper for backward compatibility if needed."""
        return self._enhance_prompt_text(scene.image_create_prompt, scene.image_style)

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
        
        # Run synchronous requests in executor to avoid blocking async loop
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._download_sync, image_url, filepath)
            return filepath
        except Exception as e:
            logger.error("Failed to download mock image", error=str(e))
            # Create a dummy file if download fails
            with open(filepath, "wb") as f:
                f.write(b"Placeholder")
            return filepath

    def _download_sync(self, url: str, filepath: str):
        """Helper for synchronous download."""
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open(filepath, "wb") as f:
                f.write(response.content)
        else:
            raise RuntimeError(f"Download failed with status {response.status_code}")

