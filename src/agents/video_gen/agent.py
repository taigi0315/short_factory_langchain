import os
import uuid
import logging
from typing import Optional
from moviepy import ColorClip, TextClip, CompositeVideoClip
from src.core.config import settings

logger = logging.getLogger(__name__)

class VideoGenAgent:
    def __init__(self):
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "videos")
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_from_text(self, prompt: str) -> str:
        """
        Generate a video from a text prompt.
        Returns the path to the generated video file.
        """
        logger.info(f"Generating video from text: {prompt}")
        
        # Mock implementation: Create a simple color clip with text
        # For now, just a color clip to avoid ImageMagick dependency issues with TextClip if not set up
        filename = f"text_gen_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            # Create a 3-second blue clip
            clip = ColorClip(size=(1280, 720), color=(0, 0, 255), duration=3)
            clip.write_videofile(output_path, fps=24, logger=None)
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate mock video: {e}")
            # Fallback to a dummy file if moviepy fails
            with open(output_path, "wb") as f:
                f.write(b"Mock video content")
            return output_path

    def generate_from_image(self, image_path: str, prompt: str) -> str:
        """
        Generate a video from an image and a prompt.
        Returns the path to the generated video file.
        """
        logger.info(f"Generating video from image: {image_path} with prompt: {prompt}")
        
        filename = f"img_gen_{uuid.uuid4().hex[:8]}.mp4"
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            # Create a 3-second red clip (simulating image animation)
            clip = ColorClip(size=(1280, 720), color=(255, 0, 0), duration=3)
            clip.write_videofile(output_path, fps=24, logger=None)
            return output_path
        except Exception as e:
            logger.error(f"Failed to generate mock video: {e}")
            with open(output_path, "wb") as f:
                f.write(b"Mock video content")
            return output_path
