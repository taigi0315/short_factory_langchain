"""
Test script for Director Agent

Tests the Director Agent's ability to analyze scripts and generate cinematic direction.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.agents.director.agent import DirectorAgent
from src.models.models import VideoScript, Scene, SceneType, ImageStyle, VoiceTone, TransitionType, ElevenLabsSettings


async def test_director_agent():
    """Test Director Agent with a sample script"""
    
    print("=" * 80)
    print("DIRECTOR AGENT TEST")
    print("=" * 80)
    
    # Create a sample script
    sample_script = VideoScript(
        title="The Pyrite Curse: When Fool's Gold Bankrupted a Town",
        main_character_description="A knowledgeable historian character",
        overall_style="documentary",
        scenes=[
            Scene(
                scene_number=1,
                scene_type=SceneType.HOOK,
                dialogue="Did you know an entire town was brought to its knees by a shiny rock that wasn't gold?",
                text_overlay=None,
                voice_tone=VoiceTone.MYSTERIOUS,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.MYSTERIOUS),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Character with mysterious expression in dramatic lighting",
                needs_animation=True,
                video_prompt="Character raises eyebrow with intrigue",
                transition_to_next=TransitionType.FADE
            ),
            Scene(
                scene_number=2,
                scene_type=SceneType.EXPLANATION,
                dialogue="Welcome to Jamestown, California, during the height of the Gold Rush.",
                text_overlay=None,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.WIDE_ESTABLISHING_SHOT,
                image_create_prompt="Bustling 1850s California town street scene",
                needs_animation=False,
                video_prompt=None,
                transition_to_next=TransitionType.FADE
            ),
            Scene(
                scene_number=3,
                scene_type=SceneType.VISUAL_DEMO,
                dialogue="Miners would find this golden, metallic mineral and celebrate their fortune.",
                text_overlay=None,
                voice_tone=VoiceTone.EXCITED,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                image_style=ImageStyle.CLOSE_UP_REACTION,
                image_create_prompt="Close-up of hands holding shiny pyrite mineral",
                needs_animation=True,
                video_prompt="Camera zooms in on the glittering mineral",
                transition_to_next=TransitionType.ZOOM_IN
            ),
            Scene(
                scene_number=4,
                scene_type=SceneType.CONCLUSION,
                dialogue="And that's how fool's gold fooled an entire generation of prospectors.",
                text_overlay=None,
                voice_tone=VoiceTone.CONFIDENT,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
                image_style=ImageStyle.WIDE_ESTABLISHING_SHOT,
                image_create_prompt="Wide shot of abandoned mining town",
                needs_animation=False,
                video_prompt=None,
                transition_to_next=TransitionType.FADE
            )
        ]
    )
    
    print(f"\n📝 Sample Script: {sample_script.title}")
    print(f"   Scenes: {len(sample_script.scenes)}")
    
    # Initialize Director Agent
    print("\n🎬 Initializing Director Agent...")
    director = DirectorAgent()
    
    # Analyze script
    print("\n🎥 Analyzing script for cinematic direction...")
    directed_script = await director.analyze_script(sample_script)
    
    # Display results
    print("\n" + "=" * 80)
    print("CINEMATIC DIRECTION RESULTS")
    print("=" * 80)
    
    print(f"\n🎨 Visual Theme: {directed_script.visual_theme}")
    print(f"📈 Emotional Arc: {directed_script.emotional_arc}")
    print(f"⏱️  Pacing Notes: {directed_script.pacing_notes}")
    print(f"🎭 Director's Vision: {directed_script.director_vision}")
    
    print("\n" + "-" * 80)
    print("SCENE-BY-SCENE DIRECTION")
    print("-" * 80)
    
    for i, directed_scene in enumerate(directed_script.directed_scenes):
        scene = directed_scene.original_scene
        direction = directed_scene.direction
        
        print(f"\n🎬 SCENE {scene.scene_number}: {directed_scene.story_beat}")
        print(f"   Dialogue: \"{scene.dialogue[:60]}...\"")
        print(f"\n   📷 Shot Type: {direction.shot_type.value}")
        print(f"   🎥 Camera Movement: {direction.camera_movement.value}")
        print(f"   📐 Camera Angle: {direction.camera_angle.value}")
        print(f"   💡 Lighting: {direction.lighting_mood.value}")
        print(f"   🖼️  Composition: {direction.composition.value}")
        print(f"\n   🎭 Emotional Purpose: {direction.emotional_purpose}")
        print(f"   📖 Narrative Function: {direction.narrative_function}")
        
        if direction.connection_from_previous:
            print(f"\n   ⬅️  From Previous: {direction.connection_from_previous}")
        if direction.connection_to_next:
            print(f"   ➡️  To Next: {direction.connection_to_next}")
        
        print(f"\n   📝 Director's Notes: {direction.director_notes}")
        
        print(f"\n   🖼️  Enhanced Image Prompt:")
        print(f"      {direction.enhanced_image_prompt[:100]}...")
        
        if direction.enhanced_video_prompt:
            print(f"\n   🎬 Enhanced Video Prompt:")
            print(f"      {direction.enhanced_video_prompt[:100]}...")
        
        print("\n" + "-" * 80)
    
    print("\n✅ Director Agent test complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_director_agent())
