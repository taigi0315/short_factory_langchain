"""
Gemini Image Generation Client
Uses Google's Gemini 2.5 Flash Image model for image generation.
"""

import os
import base64
import structlog
from typing import Optional
import google.generativeai as genai
from pathlib import Path

logger = structlog.get_logger()


class GeminiImageClient:
    """
    Client for Gemini image generation API.
    Uses gemini-2.5-flash-image-preview model.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize Gemini image client.
        
        Args:
            api_key: Google Gemini API key
        """
        self.api_key = api_key
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-image-preview')
        logger.info("Gemini image client initialized", model="gemini-2.5-flash-image-preview")
    
    async def generate_image(
        self,
        prompt: str,
        model: Optional[str] = None,  # Kept for compatibility, but ignored
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """
        Generate an image using Gemini.
        
        NOTE: Gemini 2.5 Flash Image is currently a PREVIEW model and may have
        limited availability. This implementation assumes the model can generate
        images directly. If the model only generates text descriptions, we'll
        need to use a different approach (e.g., DALL-E, Stable Diffusion).
        
        Args:
            prompt: The image generation prompt
            model: Ignored (kept for compatibility with NanoBanana interface)
            width: Desired image width (note: Gemini may not honor exact dimensions)
            height: Desired image height (note: Gemini may not honor exact dimensions)
            
        Returns:
            str: Base64-encoded image data with data URI prefix
            
        Raises:
            RuntimeError: If generation fails
        """
        try:
            logger.info("Generating image with Gemini", prompt_length=len(prompt))
            
            # Add dimension hints to prompt if specified
            dimension_hint = f"Create a {width}x{height} image. "
            full_prompt = dimension_hint + prompt
            
            # Generate image
            response = self.model.generate_content([full_prompt])
            
            logger.debug("Gemini response received", has_parts=bool(response.parts))
            
            # Check if response contains image data
            if not response.parts:
                raise RuntimeError("No response parts from Gemini")
            
            # Try to find image data in response
            image_data = None
            mime_type = None
            
            for part in response.parts:
                if hasattr(part, 'inline_data') and part.inline_data:
                    # Found inline image data
                    image_data = part.inline_data.data
                    mime_type = part.inline_data.mime_type
                    logger.info("Found inline image data", mime_type=mime_type)
                    break
                elif hasattr(part, 'text'):
                    # Model returned text instead of image
                    logger.warning("Gemini returned text instead of image", text_preview=part.text[:100])
            
            if not image_data:
                # Gemini 2.5 Flash Image may not be available or may only generate text
                raise RuntimeError(
                    "Gemini did not return image data. "
                    "The gemini-2.5-flash-image-preview model may not be available "
                    "or may require different API access. "
                    "Consider using mock mode or a different image generation service."
                )
            
            # Image data from Gemini is already base64 encoded
            # Return as data URI
            data_uri = f"data:{mime_type};base64,{image_data}"
            
            logger.info("Image generated successfully", mime_type=mime_type, data_size=len(image_data))
            return data_uri
            
        except Exception as e:
            logger.error("Failed to generate image with Gemini", error=str(e), error_type=type(e).__name__)
            raise RuntimeError(f"Gemini image generation failed: {e}")
    
    async def download_image(self, data_uri: str, output_path: str) -> None:
        """
        Save a base64 data URI to a file.
        
        Args:
            data_uri: Data URI with base64 image data
            output_path: Path to save the image
        """
        try:
            # Extract base64 data from data URI
            if data_uri.startswith('data:'):
                # Format: data:image/png;base64,<data>
                base64_data = data_uri.split(',', 1)[1]
            else:
                base64_data = data_uri
            
            # Decode and save
            image_bytes = base64.b64decode(base64_data)
            
            # Ensure directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'wb') as f:
                f.write(image_bytes)
            
            logger.info("Image saved", path=output_path, size_bytes=len(image_bytes))
            
        except Exception as e:
            logger.error("Failed to save image", error=str(e), path=output_path)
            raise RuntimeError(f"Failed to save image: {e}")
