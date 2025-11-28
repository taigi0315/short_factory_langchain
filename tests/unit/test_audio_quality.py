import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import json
from src.models.models import VoiceTone, ElevenLabsSettings, Scene, VisualSegment
from src.agents.voice.agent import VoiceAgent
from src.core.config import settings

class TestAudioQuality(unittest.IsolatedAsyncioTestCase):
    def test_distinct_tone_settings(self):
        """Test that different tones return distinct settings."""
        excited = ElevenLabsSettings.for_tone(VoiceTone.EXCITED)
        serious = ElevenLabsSettings.for_tone(VoiceTone.SERIOUS)
        sad = ElevenLabsSettings.for_tone(VoiceTone.SAD)
        
        # Verify differences
        self.assertNotEqual(excited.stability, serious.stability, "Excited and Serious should have different stability")
        self.assertNotEqual(excited.speed, sad.speed, "Excited and Sad should have different speed")
        
        # Verify specific refined values (sanity check)
        self.assertLess(excited.stability, 0.5, "Excited should have low stability")
        self.assertGreater(excited.speed, 1.0, "Excited should be fast")
        self.assertGreater(serious.stability, 0.6, "Serious should have high stability")
        
        print("\n✅ Tone settings are distinct and refined")

    async def test_voice_settings_override(self):
        """Test that config overrides are applied to voice settings."""
        
        # Define override
        override = {
            "excited": {
                "stability": 0.1,
                "speed": 1.5
            }
        }
        override_json = json.dumps(override)
        
        # Mock settings and client
        with patch('src.core.config.settings.VOICE_SETTINGS_OVERRIDE', override_json), \
             patch('src.core.config.settings.USE_REAL_VOICE', True), \
             patch('src.core.config.settings.ELEVENLABS_API_KEY', 'fake_key'):
            
            agent = VoiceAgent()
            agent.client = AsyncMock()
            agent.client.generate_audio.return_value = "path/to/audio.mp3"
            
            # Create scene with EXCITED tone
            scene = Scene(
                scene_number=1,
                scene_type="explanation",
                content=[VisualSegment(segment_text="Hello world", image_prompt="test")],
                voice_tone=VoiceTone.EXCITED,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                image_style="cinematic",
                needs_animation=False,
                transition_to_next="none"
            )
            
            # Run generation
            await agent.generate_voiceovers([scene])
            
            # Verify client call arguments
            call_args = agent.client.generate_audio.call_args
            _, kwargs = call_args
            voice_settings = kwargs.get('voice_settings')
            
            # Check if override was applied
            self.assertEqual(voice_settings['stability'], 0.1, "Stability override not applied")
            self.assertEqual(voice_settings['speed'], 1.5, "Speed override not applied")
            
            # Check if non-overridden values remain
            original_excited = ElevenLabsSettings.for_tone(VoiceTone.EXCITED)
            self.assertEqual(voice_settings['similarity_boost'], original_excited.similarity_boost, "Non-overridden value changed")
            
            print("\n✅ Voice settings override applied correctly")

if __name__ == '__main__':
    unittest.main()
