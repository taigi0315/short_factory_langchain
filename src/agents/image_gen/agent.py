import os
import asyncio
import logging
import hashlib
import shutil
import uuid
from typing import List, Dict, Optional
import requests

from src.models.models import Scene, ImageStyle
from src.core.config import settings
from src.agents.image_gen.nanobanana_client import NanoBananaClient

logger = logging.getLogger(__name__)

class ImageGenAgent:
    def __init__(self):
        # Use centralized config
        self.mock_mode = not settings.USE_REAL_IMAGE
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "images")
        self.cache_dir = os.path.join(self.output_dir, "cache")
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # API configuration from settings
        self.api_key = settings.NANO_BANANA_API_KEY
        self.api_url = settings.NANO_BANANA_API_URL

    async def generate_images(self, scenes: List[Scene]) -> Dict[int, str]:
        """
        Generates images for a list of scenes.
        Returns a dictionary mapping scene_number to local_file_path.
        """
        logger.info(f"Generating images for {len(scenes)} scenes...")
        
        image_paths = {}
        
        if self.mock_mode:
            return await self._generate_mock_images(scenes)
        
        # Real mode - use NanoBanana
        if not self.api_key:
             logger.error("NANO_BANANA_API_KEY not set. Falling back to mock mode.")
             return await self._generate_mock_images(scenes)

        async with NanoBananaClient(self.api_key, self.api_url) as client:
            # Generate all images in parallel
            tasks = [
                self._generate_single_image(client, scene)
                for scene in scenes
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                scene = scenes[i]
                if isinstance(result, Exception):
                    logger.error(f"Image generation failed for scene {scene.scene_number}: {result}")
                    # Fall back to placeholder
                    image_paths[scene.scene_number] = await self._generate_placeholder(scene)
                else:
                    image_paths[scene.scene_number] = result
        
        return image_paths

    async def _generate_single_image(
        self, 
        client: NanoBananaClient, 
        scene: Scene
    ) -> str:
        """Generate image for a single scene with caching."""
        enhanced_prompt = self._enhance_prompt(scene)
        model = self._select_model(scene)
        
        # Check cache
        cache_key = self._cache_key(enhanced_prompt, model)
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.png")
        
        if os.path.exists(cache_path):
            logger.info(f"✓ Using cached image for scene {scene.scene_number}")
            # Copy to output dir with scene name
            filename = f"scene_{scene.scene_number}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.output_dir, filename)
            shutil.copy(cache_path, filepath)
            return filepath

        logger.info(f"Generating image for scene {scene.scene_number}")
        logger.debug(f"Prompt: {enhanced_prompt}")
        
        try:
            # Generate image
            image_url = await client.generate_image(
                prompt=enhanced_prompt,
                model=model,
                width=1920,
                height=1080,
            )
            
            # Download to cache first
            await client.download_image(image_url, cache_path)
            
            # Copy to final destination
            filename = f"scene_{scene.scene_number}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.output_dir, filename)
            shutil.copy(cache_path, filepath)
            
            logger.info(f"✓ Image saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise

    def _enhance_prompt(self, scene: Scene) -> str:
        """Enhance the base prompt with style and quality modifiers."""
        base_prompt = scene.image_create_prompt or "A cinematic scene"
        
        # Add style modifiers based on image_style
        style_enhancers = {
            ImageStyle.CINEMATIC: "cinematic lighting, film grain, bokeh, 4k, professional photography",
            ImageStyle.SINGLE_CHARACTER: "character focus, detailed face, portrait style",
            ImageStyle.INFOGRAPHIC: "clean design, informational, vector art style",
            ImageStyle.COMIC_PANEL: "comic book style, bold lines, vibrant colors",
        }
        
        # Default to cinematic if style not found or None
        style_suffix = style_enhancers.get(scene.image_style, "high quality, detailed, cinematic")
        
        # Add quality modifiers
        quality_suffix = "8k uhd, sharp focus, professional, trending on artstation"
        
        enhanced = f"{base_prompt}, {style_suffix}, {quality_suffix}"
        return enhanced

    def _select_model(self, scene: Scene) -> str:
        """Select appropriate model based on scene requirements."""
        # For now, default to stable-diffusion-xl for best quality
        return "stable-diffusion-xl"

    def _cache_key(self, prompt: str, model: str) -> str:
        return hashlib.sha256(f"{prompt}:{model}".encode()).hexdigest()[:16]

    async def _generate_mock_images(self, scenes: List[Scene]) -> Dict[int, str]:
        """Generate mock images for all scenes."""
        image_paths = {}
        for scene in scenes:
            image_paths[scene.scene_number] = await self._generate_placeholder(scene)
        return image_paths

    async def _generate_placeholder(self, scene: Scene) -> str:
        """Generate a placeholder image using placehold.co."""
        filename = f"scene_{scene.scene_number}_placeholder.png"
        filepath = os.path.join(self.output_dir, filename)
        
        prompt_slug = (
            scene.image_create_prompt[:20].replace(" ", "+")
            if scene.image_create_prompt
            else "scene"
        )
        image_url = (
            f"https://placehold.co/1280x720/2563eb/ffffff/png?text=Scene+{scene.scene_number}:{prompt_slug}"
        )
        
        # Run synchronous requests in executor to avoid blocking async loop
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self._download_sync, image_url, filepath)
            return filepath
        except Exception as e:
            logger.error(f"Failed to download mock image: {e}")
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

