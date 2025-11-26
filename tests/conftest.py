"""
Shared test fixtures for all agent tests.

This module provides common fixtures used across multiple test files,
reducing duplication and ensuring consistency in test setup.
"""
import pytest
from unittest.mock import MagicMock
from pathlib import Path
from src.core.config import settings


@pytest.fixture
def mock_llm():
    """
    Shared fixture for mocking LLM across all agent tests.
    
    Returns:
        MagicMock: A mocked LLM instance with invoke method
    """
    llm = MagicMock()
    llm.invoke = MagicMock()
    return llm


@pytest.fixture
def mock_settings_real_mode(monkeypatch):
    """
    Configure settings for real mode (USE_REAL_LLM=True).
    
    Args:
        monkeypatch: pytest monkeypatch fixture
        
    Returns:
        settings: The settings object with real mode enabled
    """
    monkeypatch.setattr(settings, "USE_REAL_LLM", True)
    monkeypatch.setattr(settings, "GEMINI_API_KEY", "test_gemini_key")
    monkeypatch.setattr(settings, "TAVILY_API_KEY", "test_tavily_key")
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "test_elevenlabs_key")
    return settings


@pytest.fixture
def mock_settings_mock_mode(monkeypatch):
    """
    Configure settings for mock mode (USE_REAL_LLM=False).
    
    Args:
        monkeypatch: pytest monkeypatch fixture
        
    Returns:
        settings: The settings object with mock mode enabled
    """
    monkeypatch.setattr(settings, "USE_REAL_LLM", False)
    monkeypatch.setattr(settings, "USE_REAL_VOICE", False)
    monkeypatch.setattr(settings, "USE_REAL_IMAGE_GEN", False)
    return settings


@pytest.fixture
def temp_output_dir(tmp_path):
    """
    Create a temporary output directory for test artifacts.
    
    Args:
        tmp_path: pytest tmp_path fixture
        
    Returns:
        Path: Path to temporary output directory
    """
    output_dir = tmp_path / "test_output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def mock_video_script():
    """
    Create a mock VideoScript for testing.
    
    Returns:
        dict: A dictionary representing a mock video script
    """
    from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings
    
    return VideoScript(
        title="Test Video",
        main_character_description="A friendly cartoon character",
        overall_style="Educational",
        global_visual_style="Pixar-style 3D",
        scenes=[
            Scene(
                scene_number=1,
                scene_type=SceneType.HOOK,
                voice_tone=VoiceTone.EXCITED,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Test hook scene",
                needs_animation=True,
                transition_to_next=TransitionType.FADE,
                content=[]
            ),
            Scene(
                scene_number=2,
                scene_type=SceneType.EXPLANATION,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.INFOGRAPHIC,
                image_create_prompt="Test explanation scene",
                needs_animation=False,
                transition_to_next=TransitionType.SLIDE_LEFT,
                content=[]
            ),
            Scene(
                scene_number=3,
                scene_type=SceneType.CONCLUSION,
                voice_tone=VoiceTone.CONFIDENT,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Test conclusion scene",
                needs_animation=False,
                transition_to_next=TransitionType.NONE,
                content=[]
            )
        ]
    )


@pytest.fixture
def mock_scene():
    """
    Create a single mock Scene for testing.
    
    Returns:
        Scene: A mock scene object
    """
    from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings
    
    return Scene(
        scene_number=1,
        scene_type=SceneType.EXPLANATION,
        voice_tone=VoiceTone.FRIENDLY,
        elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
        image_style=ImageStyle.CHARACTER_WITH_BACKGROUND,
        image_create_prompt="A friendly character explaining a concept",
        needs_animation=False,
        transition_to_next=TransitionType.FADE,
        content=[]
    )


# Pytest configuration
def pytest_configure(config):
    """
    Configure pytest with custom markers.
    """
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "requires_api: mark test as requiring real API keys"
    )
