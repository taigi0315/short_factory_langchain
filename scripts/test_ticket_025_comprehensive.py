"""
Comprehensive test suite for VideoEffectAgent (TICKET-025)
Tests various scenarios and edge cases
"""
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.video_effect.agent import VideoEffectAgent
from src.models.models import (
    VideoScript, Scene, SceneType, VoiceTone, ImageStyle, 
    TransitionType, HookTechnique, ElevenLabsSettings
)


def create_test_script(scenario: str) -> VideoScript:
    """Create test scripts for different scenarios"""
    
    if scenario == "action":
        # Action-heavy script (thunder example)
        scenes = [
            Scene(
                scene_number=1,
                scene_type=SceneType.HOOK,
                dialogue="Did you know thunder can strike with incredible force?",
                voice_tone=VoiceTone.EXCITED,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Dark storm clouds with lightning",
                needs_animation=True,
                video_prompt="Lightning strikes dramatically",
                transition_to_next=TransitionType.FADE,
                hook_technique=HookTechnique.SHOCKING_FACT,
                video_importance=10
            ),
            Scene(
                scene_number=2,
                scene_type=SceneType.VISUAL_DEMO,
                dialogue="Watch what happens when lightning hits a tree",
                voice_tone=VoiceTone.DRAMATIC,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.DRAMATIC),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Tree being struck by lightning",
                needs_animation=True,
                video_prompt="Tree shakes violently as lightning strikes",
                transition_to_next=TransitionType.FADE,
                video_importance=9
            ),
            Scene(
                scene_number=3,
                scene_type=SceneType.EXPLANATION,
                dialogue="Thunder is the sound created by rapidly expanding air",
                voice_tone=VoiceTone.SERIOUS,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.SERIOUS),
                image_style=ImageStyle.DIAGRAM_EXPLANATION,
                image_create_prompt="Scientific diagram of sound waves",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=5
            ),
            Scene(
                scene_number=4,
                scene_type=SceneType.CONCLUSION,
                dialogue="Nature's power is truly amazing",
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.WIDE_ESTABLISHING_SHOT,
                image_create_prompt="Peaceful landscape after storm",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=5
            )
        ]
        return VideoScript(
            title="The Power of Thunder",
            main_character_description="Nature documentary narrator",
            overall_style="Documentary",
            global_visual_style="Cinematic 4K nature documentary",
            scenes=scenes
        )
    
    elif scenario == "educational":
        # Educational/explanation-heavy script
        scenes = [
            Scene(
                scene_number=1,
                scene_type=SceneType.HOOK,
                dialogue="Ever wondered how photosynthesis works?",
                voice_tone=VoiceTone.CURIOUS,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CURIOUS),
                image_style=ImageStyle.INFOGRAPHIC,
                image_create_prompt="Colorful diagram of a plant",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                hook_technique=HookTechnique.INTRIGUING_QUESTION,
                video_importance=7
            ),
            Scene(
                scene_number=2,
                scene_type=SceneType.EXPLANATION,
                dialogue="Plants use sunlight to create energy",
                voice_tone=VoiceTone.FRIENDLY,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
                image_style=ImageStyle.DIAGRAM_EXPLANATION,
                image_create_prompt="Diagram showing sunlight hitting leaves",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=5
            ),
            Scene(
                scene_number=3,
                scene_type=SceneType.VISUAL_DEMO,
                dialogue="Here's the process step by step",
                voice_tone=VoiceTone.CONFIDENT,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
                image_style=ImageStyle.STEP_BY_STEP_VISUAL,
                image_create_prompt="Step-by-step photosynthesis diagram",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=6
            ),
            Scene(
                scene_number=4,
                scene_type=SceneType.CONCLUSION,
                dialogue="And that's how plants make their food!",
                voice_tone=VoiceTone.ENTHUSIASTIC,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.ENTHUSIASTIC),
                image_style=ImageStyle.CHARACTER_WITH_BACKGROUND,
                image_create_prompt="Happy plant in sunlight",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=4
            )
        ]
        return VideoScript(
            title="How Photosynthesis Works",
            main_character_description="Science educator",
            overall_style="Educational",
            global_visual_style="Clean educational infographic style",
            scenes=scenes
        )
    
    elif scenario == "vertical_movement":
        # Script with vertical movement keywords
        scenes = [
            Scene(
                scene_number=1,
                scene_type=SceneType.HOOK,
                dialogue="Look up at the tallest building in the world",
                voice_tone=VoiceTone.SURPRISED,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.SURPRISED),
                image_style=ImageStyle.WIDE_ESTABLISHING_SHOT,
                image_create_prompt="Looking up at a massive skyscraper",
                needs_animation=True,
                video_prompt="Camera tilts up revealing the tower's height",
                transition_to_next=TransitionType.FADE,
                hook_technique=HookTechnique.VISUAL_SURPRISE,
                video_importance=8
            ),
            Scene(
                scene_number=2,
                scene_type=SceneType.VISUAL_DEMO,
                dialogue="Now look down from the top",
                voice_tone=VoiceTone.DRAMATIC,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.DRAMATIC),
                image_style=ImageStyle.WIDE_ESTABLISHING_SHOT,
                image_create_prompt="View from the top looking down",
                needs_animation=True,
                video_prompt="Camera tilts down showing the ground far below",
                transition_to_next=TransitionType.FADE,
                video_importance=7
            ),
            Scene(
                scene_number=3,
                scene_type=SceneType.EXPLANATION,
                dialogue="This building stands over 800 meters tall",
                voice_tone=VoiceTone.SERIOUS,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.SERIOUS),
                image_style=ImageStyle.INFOGRAPHIC,
                image_create_prompt="Infographic showing building height comparison",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=5
            ),
            Scene(
                scene_number=4,
                scene_type=SceneType.CONCLUSION,
                dialogue="That's the power of human engineering",
                voice_tone=VoiceTone.CONFIDENT,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Majestic view of the building",
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                video_importance=6
            )
        ]
        return VideoScript(
            title="The World's Tallest Building",
            main_character_description="Architecture enthusiast",
            overall_style="Documentary",
            global_visual_style="Cinematic architectural photography",
            scenes=scenes
        )


def test_scenario(scenario_name: str, script: VideoScript, expected_effects: dict):
    """Test a specific scenario"""
    print(f"\n{'='*60}")
    print(f"TESTING: {scenario_name}")
    print(f"{'='*60}")
    
    agent = VideoEffectAgent()
    recommendations = agent.analyze_script(script, max_ai_videos=2)
    
    print(f"\n📊 Results:")
    print(f"   Total scenes: {len(recommendations)}")
    print(f"   AI videos: {sum(1 for r in recommendations if r.recommend_ai_video)}")
    
    # Check each scene
    all_passed = True
    for rec in recommendations:
        scene = script.scenes[rec.scene_number - 1]
        expected = expected_effects.get(rec.scene_number, {})
        
        print(f"\n🎬 Scene {rec.scene_number}: {scene.scene_type.value}")
        print(f"   Dialogue: {scene.dialogue[:50]}...")
        print(f"   Effect: {rec.effect}")
        print(f"   Transition: {rec.transition_to_next.value}")
        print(f"   AI Video: {'✅' if rec.recommend_ai_video else '❌'}")
        
        # Validate against expectations
        if expected:
            effect_match = rec.effect == expected.get('effect', rec.effect)
            ai_match = rec.recommend_ai_video == expected.get('ai_video', rec.recommend_ai_video)
            
            if not effect_match:
                print(f"   ⚠️  Expected effect: {expected.get('effect')}, got: {rec.effect}")
                all_passed = False
            if not ai_match:
                print(f"   ⚠️  Expected AI video: {expected.get('ai_video')}, got: {rec.recommend_ai_video}")
                all_passed = False
            
            if effect_match and ai_match:
                print(f"   ✅ Matches expectations")
    
    return all_passed


def run_all_tests():
    """Run all test scenarios"""
    print("🚀 COMPREHENSIVE VIDEOEFFECTAGENT TEST SUITE")
    print("="*60)
    
    results = {}
    
    # Test 1: Action scenario
    action_script = create_test_script("action")
    results['action'] = test_scenario(
        "Action-Heavy Script (Thunder)",
        action_script,
        expected_effects={
            1: {'effect': 'shake', 'ai_video': True},  # Hook with "strike"
            2: {'effect': 'shake', 'ai_video': True},  # Visual demo with "strikes"
            3: {'effect': 'static', 'ai_video': False},  # Explanation
            4: {'effect': 'ken_burns_zoom_out', 'ai_video': False}  # Conclusion
        }
    )
    
    # Test 2: Educational scenario
    edu_script = create_test_script("educational")
    results['educational'] = test_scenario(
        "Educational Script (Photosynthesis)",
        edu_script,
        expected_effects={
            1: {'effect': 'ken_burns_zoom_in', 'ai_video': False},  # Hook, importance 7
            2: {'effect': 'static', 'ai_video': False},  # Explanation, low importance
            3: {'effect': 'pan_right', 'ai_video': False},  # Visual demo
            4: {'effect': 'ken_burns_zoom_out', 'ai_video': False}  # Conclusion
        }
    )
    
    # Test 3: Vertical movement scenario
    vertical_script = create_test_script("vertical_movement")
    results['vertical'] = test_scenario(
        "Vertical Movement Script (Skyscraper)",
        vertical_script,
        expected_effects={
            1: {'effect': 'tilt_up', 'ai_video': True},  # "look up"
            2: {'effect': 'tilt_down', 'ai_video': True},  # "look down"
            3: {'effect': 'static', 'ai_video': False},  # Explanation
            4: {'effect': 'ken_burns_zoom_out', 'ai_video': False}  # Conclusion
        }
    )
    
    # Summary
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print(f"{'='*60}")
    
    for test_name, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name.upper()}: {status}")
    
    all_passed = all(results.values())
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED - Review output above")
    print(f"{'='*60}")
    
    return all_passed


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
