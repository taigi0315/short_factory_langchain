import unittest
from unittest.mock import MagicMock, patch
from src.models.models import Scene, VisualSegment, SceneType, ImageStyle, VoiceTone, ElevenLabsSettings, TransitionType
from src.agents.video_assembly.agent import VideoAssemblyAgent

class TestVisualSegmentation(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = VideoAssemblyAgent()

    def test_scene_model_visual_segments(self):
        """Test Scene model with VisualSegments."""
        seg1 = VisualSegment(segment_text="Hello world.", image_prompt="A waving hand")
        seg2 = VisualSegment(segment_text="This is a test.", image_prompt="A test tube")
        
        scene = Scene(
            scene_number=1,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings(stability=0.5, similarity_boost=0.5, style=0.5, speed=1.0, loudness=0.0),
            image_style=ImageStyle.CINEMATIC,
            content=[seg1, seg2],
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        )
        
        # Test derived properties
        self.assertEqual(scene.dialogue, "Hello world. This is a test.")
        self.assertEqual(scene.image_prompts, ["A waving hand", "A test tube"])
        self.assertEqual(scene.image_create_prompt, "A waving hand")

    def test_calculate_segment_durations(self):
        """Test duration calculation logic."""
        total_duration = 10.0
        segments = ["abcde", "fghij"] # 5 chars each
        durations = self.agent._calculate_segment_durations(total_duration, segments)
        self.assertEqual(durations, [5.0, 5.0])
        
        segments = ["a", "bbb"] # 1 vs 3 chars. Total 4.
        durations = self.agent._calculate_segment_durations(total_duration, segments)
        self.assertEqual(durations, [2.5, 7.5])
        
        # Edge case: empty text
        segments = ["", ""]
        durations = self.agent._calculate_segment_durations(total_duration, segments)
        self.assertEqual(durations, [5.0, 5.0])

    @patch('src.agents.video_assembly.agent.ImageClip')
    @patch('src.agents.video_assembly.agent.AudioFileClip')
    @patch('src.agents.video_assembly.agent.concatenate_videoclips')
    async def test_assemble_video_segments(self, mock_concat, mock_audio_clip, mock_image_clip):
        """Test assemble_video logic with visual segments."""
        # Setup mocks
        mock_audio_instance = MagicMock()
        mock_audio_instance.duration = 10.0
        mock_audio_clip.return_value = mock_audio_instance
        
        mock_img_instance = MagicMock()
        mock_image_clip.return_value = mock_img_instance
        mock_img_instance.with_duration.return_value = mock_img_instance
        mock_img_instance.with_effects.return_value = mock_img_instance
        mock_img_instance.size = (1920, 1080)
        
        mock_concat_instance = MagicMock()
        mock_concat.return_value = mock_concat_instance
        mock_concat_instance.with_audio.return_value = mock_concat_instance

        # Create scene with segments
        seg1 = VisualSegment(segment_text="Short.", image_prompt="Img1")
        seg2 = VisualSegment(segment_text="This is a longer segment.", image_prompt="Img2")
        
        scene = Scene(
            scene_number=1,
            scene_type=SceneType.EXPLANATION,
            voice_tone=VoiceTone.EXCITED,
            elevenlabs_settings=ElevenLabsSettings(stability=0.5, similarity_boost=0.5, style=0.5, speed=1.0, loudness=0.0),
            image_style=ImageStyle.CINEMATIC,
            content=[seg1, seg2],
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        )
        
        script = MagicMock()
        script.scenes = [scene]
        script.title = "Test Video"
        
        image_paths = {1: ["path/to/img1.png", "path/to/img2.png"]}
        audio_paths = {1: "path/to/audio.mp3"}
        
        await self.agent.assemble_video(script, image_paths, audio_paths)
        
        # Verify calls
        self.assertEqual(mock_image_clip.call_count, 2)
        self.assertEqual(mock_concat.call_count, 2) # Once for scene, once for final
        
        # Check durations
        # "Short." = 6 chars
        # "This is a longer segment." = 25 chars
        # Total = 31 chars
        # Duration 1 = 10.0 * (6/31) = 1.935...
        # Duration 2 = 10.0 * (25/31) = 8.064...
        
        # We can inspect the calls to with_duration
        # Since we reuse the mock instance, we check call_args_list of the mock instance's method
        # But wait, we mocked the class, so each instantiation returns the SAME mock instance?
        # Yes, mock_image_clip.return_value = mock_img_instance
        
        # Let's check the arguments passed to with_duration
        calls = mock_img_instance.with_duration.call_args_list
        self.assertEqual(len(calls), 2)
        
        dur1 = calls[0][0][0]
        dur2 = calls[1][0][0]
        
        self.assertAlmostEqual(dur1 + dur2, 10.0)
        self.assertTrue(dur1 < dur2)

if __name__ == '__main__':
    unittest.main()
