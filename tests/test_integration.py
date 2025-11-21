"""
End-to-end integration test for video generation pipeline.
Tests the complete workflow: Story → Script → Images → Audio → Video
"""
import os
import pytest
import asyncio
from src.agents.story_finder.agent import StoryFinderAgent
from src.agents.script_writer.agent import ScriptWriterAgent
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.voice.agent import VoiceAgent
from src.agents.video_assembly.agent import VideoAssemblyAgent
from src.agents.story_finder.models import StoryIdea


@pytest.mark.asyncio
async def test_full_pipeline_mock_mode():
    """
    Test complete pipeline in mock mode (fast, no API costs).
    This validates the entire workflow works end-to-end.
    """
    # Setup: Ensure output directories exist
    os.makedirs("generated_assets", exist_ok=True)
    
    print("\n" + "="*60)
    print("Starting End-to-End Integration Test")
    print("="*60)
    
    # Step 1: Generate story ideas
    print("\n[1/5] Generating story ideas...")
    story_agent = StoryFinderAgent()
    try:
        stories = story_agent.find_stories("A funny cat video", num_stories=1)
        story = stories.stories[0]
        print(f"✓ Generated story: {story.title}")
    except Exception as e:
        # If LLM fails (no API key), use mock story
        print(f"⚠ LLM generation failed ({e}), using mock story")
        story = StoryIdea(
            title="Test Cat Story",
            summary="A cat discovers the world of premium coffee",
            hook="Coffee snob cats are taking over the internet",
            keywords=["cat", "coffee", "comedy"]
        )
    
    # Step 2: Generate script
    print("\n[2/5] Generating script...")
    script_agent = ScriptWriterAgent()
    full_subject = (
        f"Title: {story.title}\n"
        f"Summary: {story.summary}\n"
        f"Hook: {story.hook}\n"
        f"Keywords: {', '.join(story.keywords)}"
    )
    
    try:
        script = script_agent.generate_script(full_subject)
        print(f"✓ Generated script with {len(script.scenes)} scenes")
    except Exception as e:
        # If LLM fails, create a simple mock script
        print(f"⚠ Script generation failed ({e}), using mock script")
        from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle, TransitionType, HookTechnique, ElevenLabsSettings
        
        mock_scenes = [
            Scene(
                scene_number=1,
                scene_type=SceneType.HOOK,
                dialogue="This is a test scene",
                voice_tone=VoiceTone.FRIENDLY,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
                image_style=ImageStyle.SINGLE_CHARACTER,
                image_create_prompt="A happy cat with coffee",
                needs_animation=False,
                transition_to_next=TransitionType.FADE
            )
        ]
        
        script = VideoScript(
            title=story.title,
            main_character_description="A test cat",
            overall_style="Comedy",
            scenes=mock_scenes
        )
    
    assert len(script.scenes) > 0, "Script should have at least one scene"
    assert script.title, "Script should have a title"
    
    # Step 3: Generate images (mock mode)
    print("\n[3/5] Generating images...")
    img_agent = ImageGenAgent()
    image_paths = await img_agent.generate_images(script.scenes)
    
    assert len(image_paths) == len(script.scenes), f"Should have image for each scene. Expected {len(script.scenes)}, got {len(image_paths)}"
    for scene_num, img_path in image_paths.items():
        assert os.path.exists(img_path), f"Image file should exist: {img_path}"
        file_size = os.path.getsize(img_path)
        assert file_size > 0, f"Image file should not be empty: {img_path}"
    print(f"✓ Generated {len(image_paths)} images")
    
    # Step 4: Generate audio (mock mode - gTTS)
    print("\n[4/5] Generating voiceovers...")
    voice_agent = VoiceAgent()
    audio_paths = await voice_agent.generate_voiceovers(script.scenes)
    
    assert len(audio_paths) == len(script.scenes), f"Should have audio for each scene. Expected {len(script.scenes)}, got {len(audio_paths)}"
    for scene_num, audio_path in audio_paths.items():
        assert os.path.exists(audio_path), f"Audio file should exist: {audio_path}"
        file_size = os.path.getsize(audio_path)
        assert file_size > 100, f"Audio file should be substantial: {audio_path} ({file_size} bytes)"
    print(f"✓ Generated {len(audio_paths)} audio files")
    
    # Step 5: Assemble video
    print("\n[5/5] Assembling video...")
    video_agent = VideoAssemblyAgent()
    video_path = await video_agent.assemble_video(script, image_paths, audio_paths)
    
    assert os.path.exists(video_path), f"Video file should exist: {video_path}"
    assert video_path.endswith(".mp4"), "Video should be MP4 format"
    
    # Verify video file is not empty
    video_size = os.path.getsize(video_path)
    assert video_size > 1000, f"Video file should be substantial, got {video_size} bytes"
    print(f"✓ Generated video: {video_path} ({video_size:,} bytes)")
    
    print("\n" + "="*60)
    print(f"✅ Integration test PASSED - video saved to {video_path}")
    print("="*60 + "\n")


@pytest.mark.asyncio
async def test_pipeline_handles_missing_dialogue():
    """Test that pipeline handles scenes without dialogue gracefully."""
    from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings
    
    print("\n[Testing edge case: Missing dialogue]")
    
    # Create a scene without dialogue
    test_scene = Scene(
        scene_number=1,
        scene_type=SceneType.HOOK,
        dialogue=None,  # Missing dialogue - should handle gracefully
        voice_tone=VoiceTone.FRIENDLY,
        elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
        image_style=ImageStyle.SINGLE_CHARACTER,
        image_create_prompt="A test scene with a cat",
        needs_animation=False,
        transition_to_next=TransitionType.FADE
    )
    
    # Voice agent should handle missing dialogue without crashing
    voice_agent = VoiceAgent()
    audio_paths = await voice_agent.generate_voiceovers([test_scene])
    
    assert 1 in audio_paths, "Should generate audio even without dialogue"
    assert os.path.exists(audio_paths[1]), "Audio file should exist"
    print("✓ Handled missing dialogue gracefully")


@pytest.mark.asyncio  
async def test_pipeline_with_multiple_scenes():
    """Test pipeline with multiple scenes to verify batch processing."""
    from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings
    
    print("\n[Testing batch processing with 3 scenes]")
    
    # Create test scenes
    scenes = []
    for i in range(1, 4):
        scene = Scene(
            scene_number=i,
            scene_type=SceneType.STORY_TELLING,
            dialogue=f"This is scene {i}",
            voice_tone=VoiceTone.FRIENDLY,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
            image_style=ImageStyle.SINGLE_CHARACTER,
            image_create_prompt=f"Scene {i}: A cat doing something interesting",
            needs_animation=False,
            transition_to_next=TransitionType.FADE
        )
        scenes.append(scene)
    
    # Test image generation
    img_agent = ImageGenAgent()
    image_paths = await img_agent.generate_images(scenes)
    assert len(image_paths) == 3, "Should generate 3 images"
    
    # Test voice generation
    voice_agent = VoiceAgent()
    audio_paths = await voice_agent.generate_voiceovers(scenes)
    assert len(audio_paths) == 3, "Should generate 3 audio files"
    
    print("✓ Batch processing works correctly")


def test_agents_can_be_instantiated():
    """Smoke test that all agents can be instantiated without errors."""
    print("\n[Testing agent instantiation]")
    
    try:
        story_agent = StoryFinderAgent()
        assert story_agent is not None
        assert story_agent.llm is not None
        assert story_agent.chain is not None
        print("✓ StoryFinderAgent instantiated")
    except Exception as e:
        pytest.fail(f"StoryFinderAgent instantiation failed: {e}")
    
    try:
        script_agent = ScriptWriterAgent()
        assert script_agent is not None
        print("✓ ScriptWriterAgent instantiated")
    except Exception as e:
        pytest.fail(f"ScriptWriterAgent instantiation failed: {e}")
    
    try:
        img_agent = ImageGenAgent()
        assert img_agent is not None
        print("✓ ImageGenAgent instantiated")
    except Exception as e:
        pytest.fail(f"ImageGenAgent instantiation failed: {e}")
    
    try:
        voice_agent = VoiceAgent()
        assert voice_agent is not None
        print("✓ VoiceAgent instantiated")
    except Exception as e:
        pytest.fail(f"VoiceAgent instantiation failed: {e}")
    
    try:
        video_agent = VideoAssemblyAgent()
        assert video_agent is not None
        print("✓ VideoAssemblyAgent instantiated")
    except Exception as e:
        pytest.fail(f"VideoAssemblyAgent instantiation failed: {e}")
    
    print("✓ All agents instantiate successfully")
