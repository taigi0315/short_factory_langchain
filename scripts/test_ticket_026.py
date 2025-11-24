import sys
import os
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle, ElevenLabsSettings, TransitionType

def test_validation_fix():
    print("Testing VideoScript validation fix...")
    
    # Mock data with invalid enum values
    mock_data = {
        "title": "Test Script",
        "main_character_description": "A test character",
        "overall_style": "educational",
        "global_visual_style": "3D",
        "scenes": [
            {
                "scene_number": 1,
                "scene_type": "hook",  # Valid
                "dialogue": "Hello",
                "voice_tone": "excited", # Valid
                "elevenlabs_settings": {
                    "stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0, "loudness": 0.0
                },
                "image_style": "visual_demo", # INVALID - Should be mapped to STEP_BY_STEP_VISUAL
                "image_create_prompt": "Test prompt",
                "needs_animation": True,
                "transition_to_next": "fade"
            },
            {
                "scene_number": 2,
                "scene_type": "explanation",
                "dialogue": "Scene 2",
                "voice_tone": "serious",
                "elevenlabs_settings": {
                    "stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0, "loudness": 0.0
                },
                "image_style": "cinematic",
                "image_create_prompt": "Test prompt 2",
                "needs_animation": False,
                "transition_to_next": "fade"
            },
            {
                "scene_number": 3,
                "scene_type": "explanation",
                "dialogue": "Scene 3",
                "voice_tone": "serious",
                "elevenlabs_settings": {
                    "stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0, "loudness": 0.0
                },
                "image_style": "cinematic",
                "image_create_prompt": "Test prompt 3",
                "needs_animation": False,
                "transition_to_next": "fade"
            },
            {
                "scene_number": 4,
                "scene_type": "narrative", # INVALID - Should be mapped to STORY_TELLING
                "dialogue": "Scene 4",
                "voice_tone": "explanation", # INVALID - Should be mapped to SERIOUS
                "elevenlabs_settings": {
                    "stability": 0.5, "similarity_boost": 0.75, "style": 0.0, "speed": 1.0, "loudness": 0.0
                },
                "image_style": "unknown_style", # INVALID - Should be mapped to CINEMATIC (default)
                "image_create_prompt": "Test prompt 4",
                "needs_animation": False,
                "transition_to_next": "fade" # Valid
            }
        ]
    }

    try:
        script = VideoScript(**mock_data)
        print("✅ VideoScript parsed successfully!")
        
        # Verify mappings
        scene1 = script.scenes[0]
        print(f"Scene 1 image_style: {scene1.image_style} (Expected: {ImageStyle.STEP_BY_STEP_VISUAL})")
        assert scene1.image_style == ImageStyle.STEP_BY_STEP_VISUAL
        
        scene4 = script.scenes[3]
        print(f"Scene 4 scene_type: {scene4.scene_type} (Expected: {SceneType.STORY_TELLING})")
        assert scene4.scene_type == SceneType.STORY_TELLING
        
        print(f"Scene 4 voice_tone: {scene4.voice_tone} (Expected: {VoiceTone.SERIOUS})")
        assert scene4.voice_tone == VoiceTone.SERIOUS
        
        print(f"Scene 4 image_style: {scene4.image_style} (Expected: {ImageStyle.CINEMATIC})")
        assert scene4.image_style == ImageStyle.CINEMATIC
        
        print("✅ All assertions passed!")
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_validation_fix()
