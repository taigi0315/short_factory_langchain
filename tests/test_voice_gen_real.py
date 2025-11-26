import pytest
import os
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path
from src.agents.voice.agent import VoiceAgent
from src.agents.voice.elevenlabs_client import ElevenLabsClient
from src.models.models import Scene, VoiceTone, SceneType, TransitionType, ImageStyle, ElevenLabsSettings
from src.core.config import settings

# Test data
MOCK_SCENE = Scene(
    scene_number=1,
    scene_type=SceneType.EXPLANATION,
    voice_tone=VoiceTone.ENTHUSIASTIC,
    elevenlabs_settings=ElevenLabsSettings(
        stability=0.5, similarity_boost=0.75, style=0.0, speed=1.0, loudness=0.0
    ),
    image_style=ImageStyle.CINEMATIC,
    image_create_prompt="test prompt",
    needs_animation=False,
    transition_to_next=TransitionType.FADE,
    content=[]
)

@pytest.fixture
def mock_settings(monkeypatch):
    monkeypatch.setattr(settings, "USE_REAL_VOICE", True)
    monkeypatch.setattr(settings, "ELEVENLABS_API_KEY", "fake_key")
    monkeypatch.setattr(settings, "GENERATED_ASSETS_DIR", "/tmp/test_assets")
    return settings

@pytest.mark.asyncio
class TestElevenLabsClient:
    async def test_generate_audio_cache_hit(self, tmp_path):
        # Setup
        client = ElevenLabsClient("fake_key")
        client.cache_dir = tmp_path
        
        # Create a fake cached file
        text = "test text"
        voice_id = "voice123"
        cache_key = client._get_cache_key(text, voice_id, "eleven_monolingual_v1", None)
        cached_file = tmp_path / f"{cache_key}.mp3"
        cached_file.write_bytes(b"cached audio")
        
        # Execute
        result = await client.generate_audio(text, voice_id)
        
        # Verify
        assert result == cached_file
        assert result.read_bytes() == b"cached audio"

    @patch("aiohttp.ClientSession.post")
    async def test_generate_audio_api_call(self, mock_post, tmp_path):
        # Setup
        client = ElevenLabsClient("fake_key")
        client.cache_dir = tmp_path
        
        # Mock API response
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.read.return_value = b"new audio"
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Execute
        result = await client.generate_audio("new text", "voice123")
        
        # Verify
        assert result.exists()
        assert result.read_bytes() == b"new audio"
        mock_post.assert_called_once()

@pytest.mark.asyncio
class TestVoiceAgent:
    async def test_init_real_mode(self, mock_settings):
        agent = VoiceAgent()
        assert agent.use_real_voice is True
        assert isinstance(agent.client, ElevenLabsClient)

    async def test_init_mock_mode(self, monkeypatch):
        monkeypatch.setattr(settings, "USE_REAL_VOICE", False)
        agent = VoiceAgent()
        assert agent.use_real_voice is False
        assert agent.client is None

    async def test_generate_voiceovers_real(self, mock_settings):
        agent = VoiceAgent()
        
        # Mock client.generate_audio
        agent.client.generate_audio = AsyncMock(return_value=Path("/tmp/audio.mp3"))
        
        results = await agent.generate_voiceovers([MOCK_SCENE])
        
        assert 1 in results
        assert results[1] == "/tmp/audio.mp3"
        agent.client.generate_audio.assert_called_once()

    async def test_generate_voiceovers_fallback(self, mock_settings):
        agent = VoiceAgent()
        
        # Mock client.generate_audio to fail
        agent.client.generate_audio = AsyncMock(side_effect=Exception("API Error"))
        
        # Mock gTTS fallback
        with patch("src.agents.voice.agent.gTTS") as mock_gtts:
            mock_tts_instance = MagicMock()
            mock_gtts.return_value = mock_tts_instance
            
            results = await agent.generate_voiceovers([MOCK_SCENE])
            
            # Should still return a path (fallback path)
            assert 1 in results
            assert "scene_1.mp3" in results[1]
            # Verify gTTS was called
            mock_gtts.assert_called_once()

    async def test_generate_voiceovers_mock_mode(self, monkeypatch):
        monkeypatch.setattr(settings, "USE_REAL_VOICE", False)
        agent = VoiceAgent()
        
        with patch("src.agents.voice.agent.gTTS") as mock_gtts:
            mock_tts_instance = MagicMock()
            mock_gtts.return_value = mock_tts_instance
            
            results = await agent.generate_voiceovers([MOCK_SCENE])
            
            assert 1 in results
            mock_gtts.assert_called_once()
