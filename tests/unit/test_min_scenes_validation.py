"""
Test MIN_SCENES validation | MIN_SCENES 검증 테스트
==============================================

This test verifies that the VideoScript model correctly enforces
MIN_SCENES and MAX_SCENES requirements.

이 테스트는 VideoScript 모델이 MIN_SCENES 및 MAX_SCENES 요구사항을
올바르게 적용하는지 확인합니다.
"""

import pytest
from pydantic import ValidationError
from src.models.models import (
    VideoScript, Scene, SceneType, VoiceTone, ImageStyle, 
    TransitionType, ElevenLabsSettings, VisualSegment
)
from src.core.config import settings


def create_test_scene(scene_number: int) -> Scene:
    """Create a test scene with valid data."""
    return Scene(
        scene_number=scene_number,
        scene_type=SceneType.EXPLANATION,
        content=[VisualSegment(
            segment_text=f"Test dialogue for scene {scene_number}",
            image_prompt=f"Test image prompt {scene_number}"
        )],
        text_overlay="",
        voice_tone=VoiceTone.FRIENDLY,
        elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
        image_style=ImageStyle.SINGLE_CHARACTER,
        character_pose="standing",
        background_description="simple background",
        needs_animation=False,
        video_prompt=None,
        transition_to_next=TransitionType.FADE
    )


def test_min_scenes_validation_too_few():
    """
    Test that VideoScript rejects scripts with fewer than MIN_SCENES.
    
    MIN_SCENES보다 적은 장면을 가진 스크립트를 거부하는지 테스트합니다.
    """
    # Create a script with too few scenes (less than MIN_SCENES)
    too_few_scenes = [create_test_scene(i) for i in range(1, settings.MIN_SCENES)]
    
    with pytest.raises(ValidationError) as exc_info:
        VideoScript(
            title="Test Video",
            main_character_description="Test character",
            overall_style="educational",
            global_visual_style="Cinematic",
            scenes=too_few_scenes
        )
    
    # Verify error message mentions MIN_SCENES
    error_str = str(exc_info.value)
    assert "at least" in error_str.lower()
    assert str(settings.MIN_SCENES) in error_str


def test_min_scenes_validation_exact_min():
    """
    Test that VideoScript accepts scripts with exactly MIN_SCENES.
    
    정확히 MIN_SCENES 개의 장면을 가진 스크립트를 허용하는지 테스트합니다.
    """
    # Create a script with exactly MIN_SCENES
    exact_min_scenes = [create_test_scene(i) for i in range(1, settings.MIN_SCENES + 1)]
    
    # Should not raise an error
    script = VideoScript(
        title="Test Video",
        main_character_description="Test character",
        overall_style="educational",
        global_visual_style="Cinematic",
        scenes=exact_min_scenes
    )
    
    assert len(script.scenes) == settings.MIN_SCENES


def test_max_scenes_validation_too_many():
    """
    Test that VideoScript rejects scripts with more than MAX_SCENES.
    
    MAX_SCENES보다 많은 장면을 가진 스크립트를 거부하는지 테스트합니다.
    """
    # Create a script with too many scenes (more than MAX_SCENES)
    too_many_scenes = [create_test_scene(i) for i in range(1, settings.MAX_SCENES + 3)]
    
    with pytest.raises(ValidationError) as exc_info:
        VideoScript(
            title="Test Video",
            main_character_description="Test character",
            overall_style="educational",
            global_visual_style="Cinematic",
            scenes=too_many_scenes
        )
    
    # Verify error message mentions MAX_SCENES
    error_str = str(exc_info.value)
    assert "at most" in error_str.lower()
    assert str(settings.MAX_SCENES) in error_str


def test_max_scenes_validation_exact_max():
    """
    Test that VideoScript accepts scripts with exactly MAX_SCENES.
    
    정확히 MAX_SCENES 개의 장면을 가진 스크립트를 허용하는지 테스트합니다.
    """
    # Create a script with exactly MAX_SCENES
    exact_max_scenes = [create_test_scene(i) for i in range(1, settings.MAX_SCENES + 1)]
    
    # Should not raise an error
    script = VideoScript(
        title="Test Video",
        main_character_description="Test character",
        overall_style="educational",
        global_visual_style="Cinematic",
        scenes=exact_max_scenes
    )
    
    assert len(script.scenes) == settings.MAX_SCENES


def test_valid_scene_count_range():
    """
    Test that VideoScript accepts scripts within the valid range.
    
    유효한 범위 내의 장면 수를 가진 스크립트를 허용하는지 테스트합니다.
    """
    # Test with a mid-range number of scenes
    mid_range = (settings.MIN_SCENES + settings.MAX_SCENES) // 2
    mid_range_scenes = [create_test_scene(i) for i in range(1, mid_range + 1)]
    
    # Should not raise an error
    script = VideoScript(
        title="Test Video",
        main_character_description="Test character",
        overall_style="educational",
        global_visual_style="Cinematic",
        scenes=mid_range_scenes
    )
    
    assert settings.MIN_SCENES <= len(script.scenes) <= settings.MAX_SCENES


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
