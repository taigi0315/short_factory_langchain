import aiohttp
import asyncio
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class NanoBananaClient:
    """
    Async client for the NanoBanana Image Generation API.
    Handles authentication, job submission, polling, and image downloading.
    """
    
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self) -> "NanoBananaClient":
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, *args: Any) -> None:
        if self.session:
            await self.session.close()
    
    async def generate_image(
        self, 
        prompt: str, 
        model: str = "stable-diffusion-xl",
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """
        Generate an image and return its URL.
        
        Args:
            prompt: The image generation prompt
            model: The model to use (e.g., "stable-diffusion-xl")
            width: Image width
            height: Image height
            
        Returns:
            str: URL of the generated image
            
        Raises:
            RuntimeError: If generation fails
            TimeoutError: If generation times out
        """
        if not self.session:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")

        # 1. Submit generation request
        payload = {
            "prompt": prompt,
            "model": model,
            "width": width,
            "height": height,
            "num_images": 1,
        }
        
        try:
            async with self.session.post(f"{self.api_url}/generate", json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()
                job_id = data.get("job_id")
                
                if not job_id:
                    # Some APIs might return image directly or different format
                    # Adjusting based on typical async patterns, but fallback if immediate
                    if "image_url" in data:
                        return str(data["image_url"])
                    raise RuntimeError(f"No job_id returned from API: {data}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"Failed to submit image generation job: {e}")
            raise

        # 2. Poll for completion
        max_attempts = 60  # 60 seconds timeout
        for attempt in range(max_attempts):
            try:
                async with self.session.get(f"{self.api_url}/status/{job_id}") as resp:
                    resp.raise_for_status()
                    status_data = await resp.json()
                    
                    status = status_data.get("status")
                    
                    if status == "completed":
                        return str(status_data["image_url"])
                    elif status == "failed":
                        error_msg = status_data.get("error", "Unknown error")
                        raise RuntimeError(f"Image generation failed: {error_msg}")
                    
                    # Wait before next poll
                    await asyncio.sleep(1)
            except aiohttp.ClientError as e:
                logger.warning(f"Error polling status (attempt {attempt+1}): {e}")
                await asyncio.sleep(1)
        
        raise TimeoutError(f"Image generation timed out after {max_attempts}s")
    
    async def download_image(self, url: str, output_path: str) -> None:
        """Download image from URL to local file."""
        if not self.session:
            raise RuntimeError("Client not initialized")
            
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(await resp.read())
