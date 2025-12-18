"""
Dependency injection for FastAPI routes.

Provides singleton instances of agents to avoid repeated initialization overhead.
This significantly improves API response times by reusing agent instances.
"""
from typing import Optional
from src.agents.script_writer.agent import ScriptWriterAgent
from src.agents.director.agent import DirectorAgent
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.voice.agent import VoiceAgent
from src.agents.video_gen.agent import VideoGenAgent
from src.agents.video_assembly.agent import VideoAssemblyAgent
from src.agents.story_finder.agent import StoryFinderAgent
import structlog

logger = structlog.get_logger()

# Singleton instances (initialized lazily)
_script_writer: Optional[ScriptWriterAgent] = None
_director: Optional[DirectorAgent] = None
_image_gen: Optional[ImageGenAgent] = None
_voice: Optional[VoiceAgent] = None
_video_gen: Optional[VideoGenAgent] = None
_video_assembly: Optional[VideoAssemblyAgent] = None
_story_finder: Optional[StoryFinderAgent] = None


def get_script_writer() -> ScriptWriterAgent:
    """
    Get or create ScriptWriterAgent singleton.

    Returns:
        ScriptWriterAgent: Shared agent instance for script generation
    """
    global _script_writer
    if _script_writer is None:
        logger.info("Initializing ScriptWriterAgent singleton")
        _script_writer = ScriptWriterAgent()
    return _script_writer


def get_director() -> DirectorAgent:
    """
    Get or create DirectorAgent singleton.

    Returns:
        DirectorAgent: Shared agent instance for cinematic direction
    """
    global _director
    if _director is None:
        logger.info("Initializing DirectorAgent singleton")
        _director = DirectorAgent()
    return _director


def get_image_gen() -> ImageGenAgent:
    """
    Get or create ImageGenAgent singleton.

    Returns:
        ImageGenAgent: Shared agent instance for image generation
    """
    global _image_gen
    if _image_gen is None:
        logger.info("Initializing ImageGenAgent singleton")
        _image_gen = ImageGenAgent()
    return _image_gen


def get_voice() -> VoiceAgent:
    """
    Get or create VoiceAgent singleton.

    Returns:
        VoiceAgent: Shared agent instance for voice synthesis
    """
    global _voice
    if _voice is None:
        logger.info("Initializing VoiceAgent singleton")
        _voice = VoiceAgent()
    return _voice


def get_video_gen() -> VideoGenAgent:
    """
    Get or create VideoGenAgent singleton.

    Returns:
        VideoGenAgent: Shared agent instance for video generation
    """
    global _video_gen
    if _video_gen is None:
        logger.info("Initializing VideoGenAgent singleton")
        _video_gen = VideoGenAgent()
    return _video_gen


def get_video_assembly() -> VideoAssemblyAgent:
    """
    Get or create VideoAssemblyAgent singleton.

    Returns:
        VideoAssemblyAgent: Shared agent instance for video assembly
    """
    global _video_assembly
    if _video_assembly is None:
        logger.info("Initializing VideoAssemblyAgent singleton")
        _video_assembly = VideoAssemblyAgent()
    return _video_assembly


def get_story_finder() -> StoryFinderAgent:
    """
    Get or create StoryFinderAgent singleton.

    Returns:
        StoryFinderAgent: Shared agent instance for story finding
    """
    global _story_finder
    if _story_finder is None:
        logger.info("Initializing StoryFinderAgent singleton")
        _story_finder = StoryFinderAgent()
    return _story_finder


def reset_agents():
    """
    Reset all agent singletons.

    Useful for testing or forcing reinitialization.
    """
    global _script_writer, _director, _image_gen, _voice, _video_gen, _video_assembly, _story_finder
    _script_writer = None
    _director = None
    _image_gen = None
    _voice = None
    _video_gen = None
    _video_assembly = None
    _story_finder = None
    logger.info("All agent singletons reset")
