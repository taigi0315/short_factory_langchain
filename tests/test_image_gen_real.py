import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from src.agents.image_gen.agent import ImageGenAgent
from src.models.models import Scene, SceneType, ImageStyle, VoiceTone, TransitionType, ElevenLabsSettings

@pytest.mark.asyncio
class TestImageGenAgent:
    
    def _create_scene(self, number: int, prompt: str) -> Scene:
        return Scene(
            scene_number=number,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
            image_style=ImageStyle.CINEMATIC,
            image_create_prompt=prompt,
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        )

    async def test_prompt_enhancement(self):
        agent = ImageGenAgent()
        scene = self._create_scene(1, "A cat sitting on a wall")
        
        enhanced = agent._enhance_prompt(scene)
        
        assert "A cat sitting on a wall" in enhanced
        assert "cinematic lighting" in enhanced
        assert "8k uhd" in enhanced

    @patch("src.agents.image_gen.agent.NanoBananaClient")
    async def test_generate_images_success(self, mock_client_cls, monkeypatch):
        # Patch settings before creating agent
        from src.core import config
        import shutil
        monkeypatch.setattr(config.settings, "USE_REAL_IMAGE", True)
        monkeypatch.setattr(config.settings, "NANO_BANANA_API_KEY", "test_key")
        
        # Setup mock client
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.generate_image.return_value = "http://example.com/image.png"
        mock_client_cls.return_value = mock_client
        
        # Setup agent (after settings are patched)
        agent = ImageGenAgent()
        
        # Clear cache to ensure fresh generation
        if os.path.exists(agent.cache_dir):
            shutil.rmtree(agent.cache_dir)
        os.makedirs(agent.cache_dir, exist_ok=True)
        
        scenes = [
            self._create_scene(1, "test1"),
            self._create_scene(2, "test2")
        ]
        
        # Mock download_image to create a dummy file
        async def mock_download(url, path):
            with open(path, "wb") as f:
                f.write(b"fake image data")
        mock_client.download_image.side_effect = mock_download
        
        results = await agent.generate_images(scenes)
        
        assert len(results) == 2
        assert results[1].endswith(".png")
        assert results[2].endswith(".png")
        assert os.path.exists(results[1])
        assert os.path.exists(results[2])
        
        # Verify parallel calls
        assert mock_client.generate_image.call_count == 2

    @patch("src.agents.image_gen.agent.NanoBananaClient")
    async def test_fallback_on_failure(self, mock_client_cls):
        # Setup mock client to fail
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.generate_image.side_effect = RuntimeError("API Error")
        mock_client_cls.return_value = mock_client
        
        # Setup agent
        with patch("src.core.config.settings.USE_REAL_IMAGE", True):
            with patch("src.core.config.settings.NANO_BANANA_API_KEY", "test_key"):
                agent = ImageGenAgent()
                
                scenes = [self._create_scene(1, "test")]
                
                # Mock placeholder generation to avoid network call
                agent._generate_placeholder = AsyncMock(return_value="/tmp/placeholder.png")
                
                results = await agent.generate_images(scenes)
                
                assert len(results) == 1
                assert results[1] == "/tmp/placeholder.png"
                
                # Verify error was logged (implicitly by fallback)
                agent._generate_placeholder.assert_called_once()

    async def test_mock_mode(self):
        with patch("src.core.config.settings.USE_REAL_IMAGE", False):
            agent = ImageGenAgent()
            assert agent.mock_mode is True
            
            scenes = [self._create_scene(1, "test")]
            
            # Mock internal mock generation
            agent._generate_mock_images = AsyncMock(return_value={1: "/tmp/mock.png"})
            
            results = await agent.generate_images(scenes)
            assert results[1] == "/tmp/mock.png"

