import unittest
from unittest.mock import MagicMock, patch
from src.agents.video_gen.agent import VideoGenAgent
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, ElevenLabsSettings, TransitionType, VisualSegment

class TestVideoSync(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = VideoGenAgent()
        
        # Create a dummy scene
        self.scene = Scene(
            scene_number=1,
            scene_type=SceneType.EXPLANATION,
            content=[VisualSegment(segment_text="Hello world", image_prompt="test prompt")],
            voice_tone=VoiceTone.FRIENDLY,
            elevenlabs_settings=ElevenLabsSettings(stability=0.5, similarity_boost=0.5, style=0.5, speed=1.0, loudness=0.0),
            image_style=ImageStyle.CINEMATIC,
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        )

    @patch('src.agents.video_gen.agent.os.path.exists')
    @patch('src.agents.video_gen.agent.AudioFileClip')
    @patch('src.agents.video_gen.agent.ImageClip')
    async def test_image_sync_with_audio(self, MockImageClip, MockAudioFileClip, MockExists):
        """Test that static image duration matches audio duration"""
        # Setup mocks
        MockExists.return_value = True
        
        mock_audio = MagicMock()
        mock_audio.duration = 5.0
        MockAudioFileClip.return_value = mock_audio
        
        mock_image = MagicMock()
        mock_image.size = (1080, 1920)
        mock_image.w = 1080
        mock_image.h = 1920
        # Mock with_duration to return the same mock (chaining)
        mock_image.with_duration.return_value = mock_image
        mock_image.resized.return_value = mock_image
        mock_image.cropped.return_value = mock_image
        MockImageClip.return_value = mock_image
        
        # Call method
        await self.agent._create_scene_clip(self.scene, "image.png", 5.0, ImageStyle.CINEMATIC)
        
        # Verify
        mock_image.with_duration.assert_called_with(5.0)

    @patch('src.agents.video_gen.agent.concatenate_videoclips')
    @patch('src.agents.video_gen.agent.os.path.exists')
    @patch('src.agents.video_gen.agent.AudioFileClip')
    @patch('src.agents.video_gen.agent.VideoFileClip')
    async def test_video_shorter_than_audio(self, MockVideoFileClip, MockAudioFileClip, MockExists, MockConcat):
        """Test that short video is frozen to match audio duration"""
        # Setup mocks
        MockExists.return_value = True
        
        mock_audio = MagicMock()
        mock_audio.duration = 10.0
        MockAudioFileClip.return_value = mock_audio
        
        mock_video = MagicMock()
        mock_video.duration = 4.0
        mock_video.size = (1920, 1080)
        # Mock methods
        mock_video.resized.return_value = mock_video
        mock_video.cropped.return_value = mock_video
        mock_video.to_ImageClip.return_value = MagicMock() # Frozen frame
        mock_video.to_ImageClip.return_value.with_duration.return_value = MagicMock()
        
        MockVideoFileClip.return_value = mock_video
        
        # Call method with a video file extension
        await self.agent._create_scene_clip(self.scene, "video.mp4", 10.0, ImageStyle.CINEMATIC)
        
        # Verify VideoFileClip was used
        MockVideoFileClip.assert_called_with("video.mp4")
        
        # Verify concatenation was called (freeze logic)
        MockConcat.assert_called()
 

if __name__ == '__main__':
    unittest.main()
