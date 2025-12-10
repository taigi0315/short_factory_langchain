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
        width: int = 1080,
        height: int = 1920,
        aspect_ratio: str = "9:16",  # Vertical for YouTube Shorts
    ) -> str:
        """
        Generate an image using Gemini with retry logic for rate limiting.
        
        NOTE: Gemini 2.5 Flash Image is currently a PREVIEW model and may have
        limited availability. This implementation assumes the model can generate
        images directly. If the model only generates text descriptions, we'll
        need to use a different approach (e.g., DALL-E, Stable Diffusion).
        
        Args:
            prompt: The image generation prompt
            model: Ignored (kept for compatibility with NanoBanana interface)
            width: Desired image width (note: Gemini may not honor exact dimensions)
            height: Desired image height (note: Gemini may not honor exact dimensions)
            aspect_ratio: Target aspect ratio (e.g., "9:16", "16:9")
            
        Returns:
            str: Base64-encoded image data with data URI prefix
            
        Raises:
            RuntimeError: If generation fails after all retries
        """
        import asyncio
        from google.api_core import exceptions as google_exceptions
        
        max_retries = 3
        base_delay = 2.0  # Start with 2 seconds
        
        for attempt in range(max_retries):
            try:
                logger.info("Generating image with Gemini", 
                           prompt_length=len(prompt), 
                           aspect_ratio=aspect_ratio,
                           attempt=attempt + 1,
                           max_retries=max_retries)
                
                # Use ONLY aspect ratio in prompt to avoid conflicts
                # Gemini doesn't support exact pixel dimensions, so we only specify aspect ratio
                # The width/height params are kept for API compatibility but not used in prompt
                aspect_hint = f"Create an image in {aspect_ratio} aspect ratio"
                if aspect_ratio == "9:16":
                    aspect_hint += " (vertical/portrait orientation)"
                elif aspect_ratio == "16:9":
                    aspect_hint += " (horizontal/landscape orientation)"
                
                full_prompt = f"{aspect_hint}. {prompt}"
                
                
                # Generate image
                # Note: Gemini doesn't support aspect_ratio in generation_config
                # We rely on prompt text to specify aspect ratio
                response = await self.model.generate_content_async([full_prompt])
                
                logger.debug("Gemini response received", has_parts=bool(response.parts))
                
                # Check if response contains image data
                if not response.parts:
                    raise RuntimeError("No response parts from Gemini")
                
                # Try to find image data in response
                image_data = None
                mime_type = None
                text_parts = []
                
                for idx, part in enumerate(response.parts):
                    logger.debug(f"Examining part {idx}", 
                               has_inline_data=hasattr(part, 'inline_data'),
                               has_text=hasattr(part, 'text'))
                    
                    if hasattr(part, 'inline_data') and part.inline_data:
                        # Found inline image data
                        image_data = part.inline_data.data
                        mime_type = part.inline_data.mime_type
                        logger.info("Found inline image data", 
                                  mime_type=mime_type,
                                  data_length=len(image_data) if image_data else 0,
                                  data_type=type(image_data).__name__)
                        break
                    elif hasattr(part, 'text'):
                        # Model returned text instead of image
                        text_parts.append(part.text)
                        logger.warning("Gemini returned text instead of image", 
                                     text_preview=part.text[:100])
                
                if not image_data:
                    # Gemini 2.5 Flash Image may not be available or may only generate text
                    full_text = "\n".join(text_parts) if text_parts else "No response"
                    raise RuntimeError(
                        f"Gemini did not return image data. "
                        f"The gemini-2.5-flash-image-preview model may not be available "
                        f"or may require different API access. "
                        f"Response: {full_text[:200]}... "
                        f"Consider using mock mode or a different image generation service."
                    )
                
                # Validate that image_data is bytes (not base64 string)
                if isinstance(image_data, str):
                    logger.warning("Image data is string, attempting to decode from base64")
                    try:
                        image_bytes = base64.b64decode(image_data)
                    except Exception as e:
                        raise RuntimeError(f"Failed to decode base64 image data: {e}")
                elif isinstance(image_data, bytes):
                    logger.info("Image data is already bytes")
                    image_bytes = image_data
                else:
                    raise RuntimeError(f"Unexpected image data type: {type(image_data)}")
                
                # Validate PNG header
                if not image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
                    logger.error("Invalid PNG header", 
                               first_bytes=image_bytes[:16].hex() if len(image_bytes) >= 16 else image_bytes.hex())
                    raise RuntimeError(
                        f"Generated image data is not a valid PNG file. "
                        f"First bytes: {image_bytes[:16].hex() if len(image_bytes) >= 16 else image_bytes.hex()}"
                    )
                
                # Encode to base64 for data URI
                base64_data = base64.b64encode(image_bytes).decode('utf-8')
                data_uri = f"data:{mime_type};base64,{base64_data}"
                
                logger.info("Image generated successfully", 
                           mime_type=mime_type, 
                           data_size=len(image_bytes),
                           base64_size=len(base64_data))
                
                return data_uri
                
            except google_exceptions.ResourceExhausted as e:
                # Rate limit hit
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Gemini API rate limit hit (ResourceExhausted). "
                        f"Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})",
                        error=str(e)
                    )
                    await asyncio.sleep(delay)
                else:
                    logger.error("Gemini API rate limit exceeded after all retries", error=str(e))
                    raise RuntimeError(f"Gemini API rate limit exceeded: {str(e)}")
                    
            except Exception as e:
                # Check if it's a rate limit error in the message
                error_msg = str(e).lower()
                if any(keyword in error_msg for keyword in ['rate limit', '429', 'quota', 'too many requests']):
                    if attempt < max_retries - 1:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Gemini API rate limit detected in error message. "
                            f"Retrying in {delay}s... (attempt {attempt + 1}/{max_retries})",
                            error=str(e)
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error("Gemini API rate limit exceeded after all retries", error=str(e))
                        raise RuntimeError(f"Gemini API rate limit exceeded: {str(e)}")
                else:
                    # Not a rate limit error, re-raise immediately
                    logger.error("Gemini image generation failed", error=str(e), error_type=type(e).__name__)
                    raise
        
        # Should never reach here
        raise RuntimeError("Image generation failed after all retries")
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    async def download_image(self, data_uri: str, output_path: str) -> None:
        """
        Save a base64 data URI to a file.
        
        Args:
            data_uri: Data URI with base64 image data
            output_path: Path to save the image
        """
        import aiofiles
        
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
            
            async with aiofiles.open(output_path, 'wb') as f:
                await f.write(image_bytes)
            
            logger.info("Image saved", path=output_path, size_bytes=len(image_bytes))
            
        except Exception as e:
            logger.error("Failed to save image", error=str(e), path=output_path)
            raise RuntimeError(f"Failed to save image: {e}")
