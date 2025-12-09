import pytest
import os
from src.agents.story_finder.agent import StoryFinderAgent
from src.agents.script_writer.agent import ScriptWriterAgent
from src.agents.image_gen.agent import ImageGenAgent
from src.models.models import Scene, SceneType, VoiceTone, ElevenLabsSettings, ImageStyle, TransitionType
from src.core.config import settings

@pytest.mark.asyncio
class TestVideoGenerationPipeline:
    
    @pytest.fixture
    def story_agent(self):
        return StoryFinderAgent()

    @pytest.fixture
    def script_agent(self):
        return ScriptWriterAgent()

    @pytest.fixture
    def image_agent(self):
        return ImageGenAgent()

    async def test_full_pipeline_mock(self, story_agent, script_agent, image_agent):
        """
        Test the full pipeline using mock data (default config).
        """
        # Force mock mode
        original_llm_mode = settings.USE_REAL_LLM
        settings.USE_REAL_LLM = False
        
        try:
            # 1. Generate Story
            stories = story_agent.find_stories("A funny cat story")
        finally:
            settings.USE_REAL_LLM = original_llm_mode

        assert len(stories.stories) > 0
        assert len(stories.stories) > 0
        selected_story = stories.stories[0]
        assert selected_story.title
        assert selected_story.summary

        # 2. Generate Script
        script_input = f"Title: {selected_story.title}\nPremise: {selected_story.summary}"
        script = await script_agent.generate_script(script_input)
        assert len(script.scenes) > 0
        
        # 3. Generate Images (for first scene only to save time)
        first_scene = script.scenes[0]
        # Ensure all required fields are present (mock data might be missing some if not careful)
        # But ScriptWriterAgent should return valid Scene objects
        
        # Force mock mode for this test even if env is set to real
        original_mode = image_agent.mock_mode
        image_agent.mock_mode = True
        
        try:
            images = await image_agent.generate_images([first_scene])
            assert len(images) == 1
            # images now returns Dict[int, List[str]]
            image_paths = images[first_scene.scene_number]
            assert isinstance(image_paths, list)
            assert len(image_paths) > 0
            assert os.path.exists(image_paths[0])
        finally:
            image_agent.mock_mode = original_mode

    @pytest.mark.skipif(not settings.USE_REAL_LLM, reason="Skipping real LLM test")
    async def test_real_story_generation(self, story_agent):
        """
        Test real story generation with Gemini.
        """
        stories = story_agent.find_stories("The future of AI")
        assert len(stories.stories) > 0
        print(f"Generated real story: {stories.stories[0].title}")

    @pytest.mark.skipif(not settings.USE_REAL_IMAGE, reason="Skipping real image generation test")
    async def test_real_image_generation(self, image_agent):
        """
        Test real image generation with NanoBanana.
        """
        from src.models.models import VisualSegment

        scene = Scene(
            scene_number=999,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.CALM,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
            image_style=ImageStyle.CINEMATIC,
            content=[VisualSegment(
                segment_text="A futuristic scene",
                image_prompt="A futuristic robot painting a canvas, 8k, highly detailed"
            )],
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        )

        images = await image_agent.generate_images([scene])
        assert len(images) == 1
        # images now returns Dict[int, List[str]]
        paths = images[999]
        assert isinstance(paths, list)
        assert len(paths) > 0
        path = paths[0]
        assert os.path.exists(path)
        assert path.endswith(".png")
        assert os.path.getsize(path) > 0

@pytest.mark.asyncio
async def test_video_generation_mock():
    """
    Test video generation endpoint in mock mode.
    """
    from src.api.routes.dev import VideoGenRequest
    from src.agents.video_gen.agent import VideoGenAgent
    
    agent = VideoGenAgent()

    # Test Text to Video
    prompt = "A cinematic shot of a futuristic city"
    video_path = await agent.generate_from_text(prompt)

    assert video_path is not None
    assert os.path.exists(video_path)
    assert video_path.endswith(".mp4")
    
    # Test Image to Video
    # Create a dummy image file first
    dummy_image = "dummy_test_image.png"
    with open(dummy_image, "wb") as f:
        f.write(b"dummy image content")
        
    try:
        video_path_2 = await agent.generate_from_image(dummy_image, "Animate this")
        assert video_path_2 is not None
        assert os.path.exists(video_path_2)
        assert video_path_2.endswith(".mp4")
    finally:
        if os.path.exists(dummy_image):
            os.remove(dummy_image)
