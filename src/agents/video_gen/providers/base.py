from abc import ABC, abstractmethod

class VideoGenerationProvider(ABC):
    """
    Abstract base class for AI video generation providers.
    """
    
    @abstractmethod
    async def generate_video(self, image_path: str, prompt: str) -> str:
        """
        Generate a video from an image and a prompt.
        
        Args:
            image_path: Path to the source image (first frame).
            prompt: Text prompt describing the motion/animation.
            
        Returns:
            str: Path to the generated video file.
            
        Raises:
            RuntimeError: If generation fails.
        """
        pass
