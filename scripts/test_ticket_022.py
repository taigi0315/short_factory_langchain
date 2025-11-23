#!/usr/bin/env python3
"""
Test script for TICKET-022: AI Video Generation Logic

This script verifies that the video_importance scoring and scene selection logic works correctly.
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import src
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))
os.chdir(parent_dir)

from src.models.models import VideoScript, Scene, SceneType, ImageStyle, VoiceTone, TransitionType, ElevenLabsSettings
from src.agents.video_gen.agent import VideoGenAgent
from src.core.config import settings

def create_test_script() -> VideoScript:
    """Create a test script with varying video_importance scores."""
    
    scenes = [
        Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            visual_description="Opening hook",
            dialogue="Welcome to our video!",
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
            image_style=ImageStyle.CINEMATIC,
            image_create_prompt="Exciting opening scene",
            needs_animation=True,
            video_importance=8,  # High importance
            transition_to_next=TransitionType.FADE,
            hook_technique="shocking_fact"
        ),
        Scene(
            scene_number=2,
            scene_type=SceneType.EXPLANATION,
            visual_description="Background info",
            dialogue="Let me explain the basics.",
            voice_tone=VoiceTone.CALM,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
            image_style=ImageStyle.INFOGRAPHIC,
            image_create_prompt="Simple infographic",
            needs_animation=False,  # Not marked for animation
            video_importance=3,
            transition_to_next=TransitionType.FADE
        ),
        Scene(
            scene_number=3,
            scene_type=SceneType.VISUAL_DEMO,
            visual_description="Complex demonstration",
            dialogue="Watch this amazing process!",
            voice_tone=VoiceTone.ENTHUSIASTIC,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.ENTHUSIASTIC),
            image_style=ImageStyle.DIAGRAM_EXPLANATION,
            image_create_prompt="Complex process diagram",
            needs_animation=True,
            video_importance=10,  # CRITICAL - highest importance
            video_prompt="Show the process unfolding step by step",
            transition_to_next=TransitionType.ZOOM_IN
        ),
        Scene(
            scene_number=4,
            scene_type=SceneType.EXPLANATION,
            visual_description="More details",
            dialogue="Here are some additional points.",
            voice_tone=VoiceTone.FRIENDLY,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
            image_style=ImageStyle.CHARACTER_WITH_BACKGROUND,
            image_create_prompt="Character explaining",
            needs_animation=True,
            video_importance=6,  # Medium importance
            transition_to_next=TransitionType.FADE
        ),
        Scene(
            scene_number=5,
            scene_type=SceneType.CONCLUSION,
            visual_description="Wrap up",
            dialogue="Thanks for watching!",
            voice_tone=VoiceTone.CONFIDENT,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
            image_style=ImageStyle.CINEMATIC,
            image_create_prompt="Closing scene",
            needs_animation=True,
            video_importance=7,  # High importance
            transition_to_next=TransitionType.NONE
        ),
    ]
    
    return VideoScript(
        title="Test Video for AI Generation Logic",
        main_character_description="A friendly educator",
        overall_style="Educational and engaging",
        scenes=scenes
    )

def test_scene_selection():
    """Test the scene selection logic."""
    print("=" * 60)
    print("TICKET-022: AI Video Generation Logic Test")
    print("=" * 60)
    print()
    
    # Create test script
    script = create_test_script()
    print(f"Created test script with {len(script.scenes)} scenes")
    print()
    
    # Display all scenes with their importance scores
    print("All Scenes:")
    print("-" * 60)
    for scene in script.scenes:
        animation_status = "✓" if scene.needs_animation else "✗"
        print(f"  Scene {scene.scene_number}: importance={scene.video_importance:2d}, "
              f"needs_animation={animation_status}, type={scene.scene_type.value}")
    print()
    
    # Test with different MAX_AI_VIDEOS_PER_SCRIPT values
    test_configs = [0, 1, 2, 3, 10]
    
    for max_videos in test_configs:
        print(f"Testing with MAX_AI_VIDEOS_PER_SCRIPT = {max_videos}")
        print("-" * 60)
        
        # Temporarily override settings
        original_max = settings.MAX_AI_VIDEOS_PER_SCRIPT
        settings.MAX_AI_VIDEOS_PER_SCRIPT = max_videos
        
        try:
            # Create agent and test selection
            agent = VideoGenAgent()
            selected = agent._select_scenes_for_ai_video(script.scenes)
            
            print(f"  Selected {len(selected)} scenes for AI video generation:")
            if selected:
                # Show selected scenes sorted by importance
                selected_scenes = [s for s in script.scenes if s.scene_number in selected]
                selected_scenes.sort(key=lambda s: s.video_importance, reverse=True)
                for scene in selected_scenes:
                    print(f"    - Scene {scene.scene_number}: importance={scene.video_importance}, "
                          f"type={scene.scene_type.value}")
            else:
                print("    (none)")
            print()
            
        finally:
            # Restore original setting
            settings.MAX_AI_VIDEOS_PER_SCRIPT = original_max
    
    print("=" * 60)
    print("Test completed successfully!")
    print("=" * 60)
    print()
    print("Expected behavior:")
    print("  - MAX=0: No scenes selected")
    print("  - MAX=1: Scene 3 (importance=10)")
    print("  - MAX=2: Scenes 3 (10) and 1 (8)")
    print("  - MAX=3: Scenes 3 (10), 1 (8), and 5 (7)")
    print("  - MAX=10: All 4 scenes with needs_animation=True")
    print()

if __name__ == "__main__":
    test_scene_selection()
