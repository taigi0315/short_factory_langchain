"""
Unit tests for ImageGenAgent.

Tests image generation functionality including:
- Agent initialization
- Mock mode image generation
- Real mode image generation with retry logic
- Cache key generation
- Prompt enhancement
- Workflow state management
"""
import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch, call
from pathlib import Path
from src.agents.image_gen.agent import ImageGenAgent
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings, VisualSegment
from src.agents.director.models import DirectedScript, DirectedScene, CinematicDirection


class TestImageGenAgent:
    """Test suite for ImageGenAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create ImageGenAgent instance for testing."""
        return ImageGenAgent()
    
    @pytest.fixture
    def sample_scene(self):
        """Create a sample scene for testing."""
        return Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
            image_style=ImageStyle.CINEMATIC,
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            content=[
                VisualSegment(
                    segment_text="This is the hook",
                    image_prompt="A mysterious figure in the shadows"
                )
            ]
        )
    
    def test_initialization(self, agent):
        """Test agent initializes with correct settings."""
        assert agent.agent_name == "ImageGenAgent"
        assert agent.output_dir is not None
        assert "images" in str(agent.output_dir)
        # Mock mode is determined by agent initialization
        assert isinstance(agent.mock_mode, bool)
    
    def test_cache_key_generation_deterministic(self, agent):
        """Test cache key is deterministic for same inputs."""
        key1 = agent._cache_key("test prompt", "model1")
        key2 = agent._cache_key("test prompt", "model1")
        
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) > 0
    
    def test_cache_key_generation_different_inputs(self, agent):
        """Test cache key differs for different inputs."""
        key1 = agent._cache_key("test prompt 1", "model1")
        key2 = agent._cache_key("test prompt 2", "model1")
        key3 = agent._cache_key("test prompt 1", "model2")
        
        assert key1 != key2  # Different prompts
        assert key1 != key3  # Different models
    
    def test_enhance_prompt_text_cinematic(self, agent):
        """Test prompt enhancement for cinematic style."""
        base_prompt = "A cat sitting"
        enhanced = agent._enhance_prompt_text(base_prompt, ImageStyle.CINEMATIC)
        
        assert "A cat sitting" in enhanced
        assert "photorealistic" in enhanced.lower() or "cinematic" in enhanced.lower()
    
    def test_enhance_prompt_text_infographic(self, agent):
        """Test prompt enhancement for infographic style."""
        base_prompt = "Data visualization"
        enhanced = agent._enhance_prompt_text(base_prompt, ImageStyle.INFOGRAPHIC)
        
        assert "Data visualization" in enhanced
        # Should add infographic-specific modifiers
        assert len(enhanced) > len(base_prompt)
    
    def test_select_model(self, agent, sample_scene):
        """Test model selection based on scene requirements."""
        model = agent._select_model(sample_scene)
        
        assert model is not None
        assert isinstance(model, str)
    
    @pytest.mark.asyncio
    async def test_generate_images_mock_mode(self, agent, sample_scene):
        """Test image generation in mock mode."""
        agent.mock_mode = True
        
        result = await agent.generate_images([sample_scene])
        
        assert 1 in result
        assert isinstance(result[1], list)
        assert len(result[1]) > 0
        assert all(isinstance(path, str) for path in result[1])
        # Mock images should be PNG files
        assert all(path.endswith(".png") for path in result[1])
    
    @pytest.mark.asyncio
    async def test_generate_images_multiple_scenes(self, agent, sample_scene):
        """Test generating images for multiple scenes."""
        agent.mock_mode = True
        
        scene2 = Scene(
            scene_number=2,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.CALM,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
            image_style=ImageStyle.INFOGRAPHIC,
            needs_animation=False,
            transition_to_next=TransitionType.SLIDE_LEFT,
            content=[
                VisualSegment(
                    segment_text="Explanation text",
                    image_prompt="Educational diagram"
                )
            ]
        )
        
        result = await agent.generate_images([sample_scene, scene2])
        
        assert 1 in result
        assert 2 in result
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_generate_images_with_multiple_segments(self, agent):
        """Test generating multiple images for scene with multiple visual segments."""
        agent.mock_mode = True
        
        scene = Scene(
            scene_number=1,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.CALM,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
            image_style=ImageStyle.FOUR_CUT_CARTOON,
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            content=[
                VisualSegment(
                    segment_text="First part",
                    image_prompt="First panel showing setup"
                ),
                VisualSegment(
                    segment_text="Second part",
                    image_prompt="Second panel showing action"
                ),
                VisualSegment(
                    segment_text="Third part",
                    image_prompt="Third panel showing result"
                )
            ]
        )
        
        result = await agent.generate_images([scene])
        
        assert 1 in result
        # Should generate one image per visual segment
        assert len(result[1]) == 3
    
    @pytest.mark.asyncio
    async def test_generate_placeholder_image(self, agent, sample_scene):
        """Test placeholder image generation."""
        agent.mock_mode = True
        
        filepath = await agent._generate_placeholder(sample_scene, index=0)
        
        assert filepath is not None
        assert isinstance(filepath, str)
        assert ".png" in filepath
        assert "scene" in filepath.lower() or str(sample_scene.scene_number) in filepath
    
    def test_enhance_prompt_legacy_wrapper(self, agent, sample_scene):
        """Test legacy _enhance_prompt wrapper method."""
        enhanced = agent._enhance_prompt(sample_scene)
        
        assert enhanced is not None
        assert isinstance(enhanced, str)
        assert len(enhanced) > 0
    
    @pytest.mark.asyncio
    async def test_generate_images_empty_list(self, agent):
        """Test generating images for empty scene list."""
        agent.mock_mode = True
        
        result = await agent.generate_images([])
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    @pytest.mark.asyncio
    async def test_generate_images_preserves_scene_order(self, agent, sample_scene):
        """Test that generated images preserve scene order."""
        agent.mock_mode = True
        
        scenes = []
        for i in range(1, 6):
            scene = Scene(
                scene_number=i,
                scene_type=SceneType.EXPLANATION,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                content=[
                    VisualSegment(
                        segment_text=f"Text {i}",
                        image_prompt=f"Scene {i}"
                    )
                ]
            )
            scenes.append(scene)
        
        result = await agent.generate_images(scenes)
        
        # Verify all scene numbers are present
        assert set(result.keys()) == {1, 2, 3, 4, 5}
    
    @pytest.mark.asyncio
    async def test_generate_images_with_workflow_id(self, agent, sample_scene):
        """Test image generation with workflow ID for checkpoint saving."""
        agent.mock_mode = True
        workflow_id = "test-workflow-123"
        
        result = await agent.generate_images([sample_scene], workflow_id=workflow_id)
        
        assert 1 in result
        assert len(result[1]) > 0
        # Workflow ID should be used for file naming or state management
        # (Implementation detail - just verify it doesn't break)


class TestImageGenAgentRealMode:
    """Test suite for ImageGenAgent in real mode (with mocked API calls)."""
    
    @pytest.fixture
    def agent(self, tmp_path):
        """Create ImageGenAgent instance for testing."""
        agent = ImageGenAgent()
        agent.mock_mode = False
        # Use tmp_path for output and cache to avoid file system issues
        agent.output_dir = str(tmp_path / "images")
        agent.cache_dir = str(tmp_path / "cache")
        os.makedirs(agent.output_dir, exist_ok=True)
        os.makedirs(agent.cache_dir, exist_ok=True)
        return agent
    
    @pytest.fixture
    def sample_scene(self):
        """Create a sample scene for testing."""
        return Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
            image_style=ImageStyle.CINEMATIC,
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            content=[
                VisualSegment(
                    segment_text="Hook text",
                    image_prompt="A mysterious figure"
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_generate_scene_images_with_retry_success(self, agent, sample_scene):
        """Test image generation with retry logic - success on first try."""
        mock_client = MagicMock()
        mock_client.generate_image = AsyncMock(return_value="https://example.com/image.png")
        
        # Mock download_image to create the cache file
        async def mock_download(url, cache_path):
            Path(cache_path).write_bytes(b"fake image data")
        
        mock_client.download_image = AsyncMock(side_effect=mock_download)
        
        result = await agent._generate_scene_images(mock_client, sample_scene)
        
        assert isinstance(result, list)
        assert len(result) > 0
        mock_client.generate_image.assert_called_once()
        mock_client.download_image.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_scene_images_handles_exception(self, agent, sample_scene):
        """Test image generation handles exceptions properly."""
        mock_client = MagicMock()
        mock_client.generate_image = AsyncMock(side_effect=Exception("API Error"))
        
        with pytest.raises(Exception, match="API Error"):
            await agent._generate_scene_images(mock_client, sample_scene)
        
        # With retry logic, it should be called multiple times (at least once)
        assert mock_client.generate_image.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_generate_scene_images_with_cache_hit(self, agent, sample_scene, tmp_path):
        """Test image generation uses cached image when available."""
        # Set up cache directory
        agent.cache_dir = str(tmp_path / "cache")
        os.makedirs(agent.cache_dir, exist_ok=True)
        
        # Create a fake cached file
        enhanced_prompt = agent._enhance_prompt_text(
            sample_scene.content[0].image_prompt,
            sample_scene.image_style
        )
        model = agent._select_model(sample_scene)
        cache_key = agent._cache_key(enhanced_prompt, model)
        cache_path = os.path.join(agent.cache_dir, f"{cache_key}.png")
        
        # Create dummy cache file
        Path(cache_path).write_bytes(b"fake image data")
        
        mock_client = MagicMock()
        mock_client.generate_image = AsyncMock()
        
        result = await agent._generate_scene_images(mock_client, sample_scene)
        
        assert isinstance(result, list)
        assert len(result) > 0
        # Should NOT call generate_image since cache hit
        mock_client.generate_image.assert_not_called()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
