"""
Unit tests for VoiceAgent.

Tests voice generation functionality including:
- Agent initialization
- Mock mode (gTTS) voice generation
- Real mode (ElevenLabs) voice generation
- Voice tone mapping
- Error handling and fallback logic
- Multiple scene processing
"""
import pytest
import os
from unittest.mock import MagicMock, AsyncMock, patch, call
from pathlib import Path
from src.agents.voice.agent import VoiceAgent, VOICE_MAPPING
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings


class TestVoiceAgent:
    """Test suite for VoiceAgent."""
    
    @pytest.fixture
    def agent(self):
        """Create VoiceAgent instance for testing."""
        return VoiceAgent()
    
    @pytest.fixture
    def sample_scene(self):
        """Create a sample scene with dialogue for testing."""
        from src.models.models import VisualSegment
        
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
                    segment_text="This is a test dialogue for voice generation.",
                    image_prompt="Test image prompt"
                )
            ]
        )
    
    def test_initialization(self, agent):
        """Test agent initializes with correct settings."""
        assert agent.agent_name == "VoiceAgent"
        assert agent.output_dir is not None
        assert "audio" in str(agent.output_dir)
        assert isinstance(agent.mock_mode, bool)
        assert isinstance(agent.use_real_voice, bool)
        # Mock mode and use_real_voice should be opposites
        assert agent.mock_mode == (not agent.use_real_voice)
    
    def test_initialization_mock_mode(self):
        """Test agent initializes correctly in mock mode."""
        with patch('src.core.config.settings.USE_REAL_VOICE', False):
            agent = VoiceAgent()
            assert agent.mock_mode is True
            assert agent.use_real_voice is False
            assert agent.client is None
    
    def test_initialization_real_mode_with_api_key(self):
        """Test agent initializes correctly in real mode with API key."""
        with patch('src.core.config.settings.USE_REAL_VOICE', True):
            with patch('src.core.config.settings.ELEVENLABS_API_KEY', 'test_key'):
                with patch('src.agents.voice.agent.ElevenLabsClient'):
                    agent = VoiceAgent()
                    assert agent.mock_mode is False
                    assert agent.use_real_voice is True
                    assert agent.client is not None
    
    def test_initialization_real_mode_without_api_key(self):
        """Test agent falls back to mock mode when API key is missing."""
        with patch('src.core.config.settings.USE_REAL_VOICE', True):
            with patch('src.core.config.settings.ELEVENLABS_API_KEY', None):
                agent = VoiceAgent()
                # Should fall back to mock mode
                assert agent.mock_mode is True
                assert agent.client is None
    
    def test_voice_mapping_coverage(self):
        """Test that all VoiceTone values have a voice mapping."""
        # Get all VoiceTone enum values
        all_tones = [tone for tone in VoiceTone]
        
        # Check that all tones are mapped
        for tone in all_tones:
            assert tone in VOICE_MAPPING, f"VoiceTone.{tone.name} not in VOICE_MAPPING"
            assert isinstance(VOICE_MAPPING[tone], str)
            assert len(VOICE_MAPPING[tone]) > 0
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_mock_mode(self, agent, sample_scene):
        """Test voice generation in mock mode (gTTS)."""
        agent.mock_mode = True
        agent.use_real_voice = False
        
        with patch.object(agent, '_generate_gtts') as mock_gtts:
            result = await agent.generate_voiceovers([sample_scene])
        
        assert 1 in result
        assert isinstance(result[1], str)
        assert "scene_1.mp3" in result[1]
        mock_gtts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_multiple_scenes(self, agent, sample_scene):
        """Test generating voiceovers for multiple scenes."""
        agent.mock_mode = True
        agent.use_real_voice = False
        
        from src.models.models import VisualSegment
        
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
                    segment_text="This is the second scene dialogue.",
                    image_prompt="Test image 2"
                )
            ]
        )
        
        with patch.object(agent, '_generate_gtts'):
            result = await agent.generate_voiceovers([sample_scene, scene2])
        
        assert 1 in result
        assert 2 in result
        assert len(result) == 2
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_empty_dialogue(self, agent):
        """Test handling of scenes with no dialogue."""
        agent.mock_mode = True
        
        scene_no_dialogue = Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
            image_style=ImageStyle.CINEMATIC,
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            content=[]  # Empty content = no dialogue
        )
        
        result = await agent.generate_voiceovers([scene_no_dialogue])
        
        # Should return empty result for scene with no dialogue
        assert 1 not in result or result[1] == ""
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_empty_list(self, agent):
        """Test generating voiceovers for empty scene list."""
        agent.mock_mode = True
        
        result = await agent.generate_voiceovers([])
        
        assert isinstance(result, dict)
        assert len(result) == 0
    
    def test_generate_gtts(self, agent, tmp_path):
        """Test gTTS generation helper."""
        filepath = str(tmp_path / "test_audio.mp3")
        text = "Test text for gTTS"
        
        with patch('src.agents.voice.agent.gTTS') as mock_gtts_class:
            mock_tts_instance = MagicMock()
            mock_gtts_class.return_value = mock_tts_instance
            
            agent._generate_gtts(text, filepath)
            
            mock_gtts_class.assert_called_once_with(text=text, lang='en')
            mock_tts_instance.save.assert_called_once_with(filepath)


class TestVoiceAgentRealMode:
    """Test suite for VoiceAgent in real mode (with mocked ElevenLabs)."""
    
    @pytest.fixture
    def agent(self, tmp_path):
        """Create VoiceAgent instance for testing in real mode."""
        with patch('src.core.config.settings.USE_REAL_VOICE', True):
            with patch('src.core.config.settings.ELEVENLABS_API_KEY', 'test_key'):
                with patch('src.agents.voice.agent.ElevenLabsClient') as mock_client_class:
                    agent = VoiceAgent()
                    agent.output_dir = str(tmp_path / "audio")
                    os.makedirs(agent.output_dir, exist_ok=True)
                    return agent
    
    @pytest.fixture
    def sample_scene(self):
        """Create a sample scene for testing."""
        from src.models.models import VisualSegment
        
        return Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            voice_tone=VoiceTone.ENTHUSIASTIC,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.ENTHUSIASTIC),
            image_style=ImageStyle.CINEMATIC,
            needs_animation=False,
            transition_to_next=TransitionType.FADE,
            content=[
                VisualSegment(
                    segment_text="This is a test dialogue.",
                    image_prompt="Test image"
                )
            ]
        )
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_real_mode_success(self, agent, sample_scene, tmp_path):
        """Test voice generation in real mode with successful API call."""
        agent.use_real_voice = True
        agent.mock_mode = False
        
        # Mock the ElevenLabs client
        mock_client = MagicMock()
        audio_path = str(tmp_path / "cached_audio.mp3")
        Path(audio_path).write_bytes(b"fake audio data")
        mock_client.generate_audio = AsyncMock(return_value=Path(audio_path))
        agent.client = mock_client
        
        result = await agent.generate_voiceovers([sample_scene])
        
        assert 1 in result
        assert isinstance(result[1], str)
        mock_client.generate_audio.assert_called_once()
        
        # Verify correct voice_id was used
        call_args = mock_client.generate_audio.call_args
        assert call_args[1]['voice_id'] == VOICE_MAPPING[VoiceTone.ENTHUSIASTIC]
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_real_mode_with_settings(self, agent, sample_scene, tmp_path):
        """Test voice generation uses ElevenLabs settings from scene."""
        agent.use_real_voice = True
        agent.mock_mode = False
        
        mock_client = MagicMock()
        audio_path = str(tmp_path / "cached_audio.mp3")
        Path(audio_path).write_bytes(b"fake audio data")
        mock_client.generate_audio = AsyncMock(return_value=Path(audio_path))
        agent.client = mock_client
        
        result = await agent.generate_voiceovers([sample_scene])
        
        # Verify voice_settings were passed
        call_args = mock_client.generate_audio.call_args
        assert 'voice_settings' in call_args[1]
        assert call_args[1]['voice_settings'] is not None
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_fallback_on_error(self, agent, sample_scene):
        """Test fallback to gTTS when ElevenLabs fails."""
        agent.use_real_voice = True
        agent.mock_mode = False
        
        # Mock client to raise exception
        mock_client = MagicMock()
        mock_client.generate_audio = AsyncMock(side_effect=Exception("API Error"))
        agent.client = mock_client
        
        with patch.object(agent, '_generate_gtts') as mock_gtts:
            result = await agent.generate_voiceovers([sample_scene])
        
        # Should fall back to gTTS
        assert 1 in result
        mock_gtts.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_fallback_also_fails(self, agent, sample_scene):
        """Test when both ElevenLabs and gTTS fallback fail."""
        agent.use_real_voice = True
        agent.mock_mode = False
        
        # Mock client to raise exception
        mock_client = MagicMock()
        mock_client.generate_audio = AsyncMock(side_effect=Exception("API Error"))
        agent.client = mock_client
        
        with patch.object(agent, '_generate_gtts', side_effect=Exception("gTTS Error")):
            result = await agent.generate_voiceovers([sample_scene])
        
        # Should return empty result when both fail
        assert 1 not in result or result[1] == ""
    
    @pytest.mark.asyncio
    async def test_generate_voiceovers_different_voice_tones(self, agent, tmp_path):
        """Test that different voice tones use different voice IDs."""
        agent.use_real_voice = True
        agent.mock_mode = False
        
        mock_client = MagicMock()
        audio_path = str(tmp_path / "cached_audio.mp3")
        Path(audio_path).write_bytes(b"fake audio data")
        mock_client.generate_audio = AsyncMock(return_value=Path(audio_path))
        agent.client = mock_client
        
        # Create scenes with different tones
        scenes = []
        tones = [VoiceTone.ENTHUSIASTIC, VoiceTone.CALM, VoiceTone.MYSTERIOUS]
        for i, tone in enumerate(tones, 1):
            from src.models.models import VisualSegment
            
            scene = Scene(
                scene_number=i,
                scene_type=SceneType.EXPLANATION,
                voice_tone=tone,
                elevenlabs_settings=ElevenLabsSettings.for_tone(tone),
                image_style=ImageStyle.CINEMATIC,
                needs_animation=False,
                transition_to_next=TransitionType.FADE,
                content=[
                    VisualSegment(
                        segment_text=f"Dialogue {i}",
                        image_prompt="Test"
                    )
                ]
            )
            scenes.append(scene)
        
        result = await agent.generate_voiceovers(scenes)
        
        # Verify all scenes generated
        assert len(result) == 3
        
        # Verify different voice IDs were used
        calls = mock_client.generate_audio.call_args_list
        voice_ids_used = [call[1]['voice_id'] for call in calls]
        
        # Should have used the correct voice ID for each tone
        assert voice_ids_used[0] == VOICE_MAPPING[VoiceTone.ENTHUSIASTIC]
        assert voice_ids_used[1] == VOICE_MAPPING[VoiceTone.CALM]
        assert voice_ids_used[2] == VOICE_MAPPING[VoiceTone.MYSTERIOUS]


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
