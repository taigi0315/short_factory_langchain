import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import os
from src.agents.video_gen.agent import VideoGenAgent
from src.agents.video_gen.providers.mock import MockVideoProvider
from src.models.models import Scene, SceneType, VoiceTone, ElevenLabsSettings, ImageStyle, TransitionType, VisualSegment
from src.core.config import settings

class TestVideoGenProvider(unittest.IsolatedAsyncioTestCase):
    
    @patch('src.agents.video_gen.agent.settings')
    async def test_mock_provider_integration(self, mock_settings):
        """Test that VideoGenAgent uses the MockVideoProvider."""
        
        # Configure settings to use mock provider
        mock_settings.VIDEO_GENERATION_PROVIDER = "mock"
        mock_settings.VIDEO_RESOLUTION = "1080p"
        mock_settings.VIDEO_FPS = 30
        mock_settings.VIDEO_QUALITY = "medium"
        mock_settings.GENERATED_ASSETS_DIR = "/tmp/test_assets"
        mock_settings.USE_REAL_LLM = False
        mock_settings.DEFAULT_SCENE_DURATION = 2.0
        mock_settings.MAX_AI_VIDEOS_PER_SCRIPT = 5
        
        # Initialize agent
        agent = VideoGenAgent()
        
        # Verify provider is MockVideoProvider
        self.assertIsInstance(agent.video_provider, MockVideoProvider)
        
        # Create a scene that needs animation
        scene = Scene(
            scene_number=1,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.CALM,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
            image_style=ImageStyle.CINEMATIC,
            content=[VisualSegment(segment_text="test", image_prompt="test image")],
            needs_animation=True, # Triggers AI video gen
            video_prompt="A cinematic shot of a robot",
            transition_to_next=TransitionType.NONE
        )
        
        # Mock the provider's generate_video method
        agent.video_provider.generate_video = AsyncMock(return_value="test_video.mp4")
        
        # Mock os.path.exists to return True for the "generated" video
        with patch('os.path.exists') as mock_exists:
            def side_effect(path):
                if path == "test_video.mp4":
                    return True
                if path == "test_image.jpg":
                    return True
                if path.endswith(".mp4"): # Allow checking if it's a video file
                    return True
                return False # Default
            
            mock_exists.side_effect = side_effect
            
            # Call _create_scene_clip directly
            # We need to mock ColorClip or whatever it returns to avoid MoviePy dependency issues in test
            # But _create_scene_clip returns a VideoClip.
            # Let's just verify the provider was called.
            
            # We need to mock the MoviePy imports inside the agent or the return value
            # Since _create_scene_clip does a lot of MoviePy stuff, it might fail if we don't mock MoviePy.
            # However, if we just want to check if generate_video was called, we can try.
            
            # Actually, let's mock the entire _create_scene_clip logic EXCEPT the provider call?
            # No, that's hard.
            # Let's just run it and expect it to fail on MoviePy but check if provider was called?
            # Or better, mock the MoviePy objects.
            
            with patch('src.agents.video_gen.agent.VideoFileClip') as MockVideoFileClip, \
                 patch('src.agents.video_gen.agent.ColorClip') as MockColorClip:
                
                # Setup mock return for VideoFileClip
                mock_clip = MagicMock()
                mock_clip.duration = 5.0
                mock_clip.size = (1920, 1080)
                mock_clip.w = 1920
                mock_clip.h = 1080
                mock_clip.resized.return_value = mock_clip
                mock_clip.cropped.return_value = mock_clip
                mock_clip.subclipped.return_value = mock_clip
                MockVideoFileClip.return_value = mock_clip
                
                await agent._create_scene_clip(scene, "test_image.jpg", 2.0, ImageStyle.CINEMATIC, force_ai_video=True)
                
                # Verify generate_video was called
                agent.video_provider.generate_video.assert_called_once_with("test_image.jpg", "A cinematic shot of a robot")
                print("\n✅ Video provider called correctly")

if __name__ == '__main__':
    unittest.main()
