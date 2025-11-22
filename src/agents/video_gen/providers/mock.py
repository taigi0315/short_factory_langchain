import structlog
from src.agents.video_gen.providers.base import VideoGenerationProvider

logger = structlog.get_logger()

class MockVideoProvider(VideoGenerationProvider):
    """
    Mock provider for testing. 
    Returns the input image path, effectively skipping video generation
    and falling back to static image processing in the agent.
    """
    
    async def generate_video(self, image_path: str, prompt: str) -> str:
        logger.info("Mock generating video", image_path=image_path, prompt=prompt)
        # In a real mock, we might copy a placeholder video.
        # For now, returning the image path signals to the agent 
        # that it should probably just use the image (or we can handle it there).
        return image_path
