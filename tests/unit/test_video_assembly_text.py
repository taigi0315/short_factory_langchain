import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Ensure src is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from src.agents.video_assembly.agent import VideoAssemblyAgent

class TestVideoAssemblyText(unittest.TestCase):
    def setUp(self):
        with patch('src.agents.video_assembly.agent.settings') as mock_settings:
            mock_settings.GENERATED_ASSETS_DIR = "/tmp"
            self.agent = VideoAssemblyAgent()

    @patch('src.agents.video_assembly.agent.ImageClip')
    @patch('src.agents.video_assembly.agent.Image')
    @patch('src.agents.video_assembly.agent.ImageDraw')
    @patch('src.agents.video_assembly.agent.ImageFont')
    def test_create_title_overlay_duration(self, mock_font_cls, mock_draw, mock_image, mock_clip):
        # Setup mocks
        mock_img = MagicMock()
        mock_image.new.return_value = mock_img
        mock_d = MagicMock()
        mock_draw.Draw.return_value = mock_d
        
        # Mock font
        mock_font = MagicMock()
        mock_font_cls.truetype.return_value = mock_font
        mock_font_cls.load_default.return_value = mock_font
        
        # Mock textlength/bbox
        mock_d.textlength.return_value = 100
        mock_d.textbbox.return_value = (0, 0, 100, 50)
        
        # Mock ImageClip behavior
        img_clip_instance = MagicMock()
        mock_clip.return_value = img_clip_instance
        img_clip_instance.with_effects.return_value = img_clip_instance
        
        # Test 10s video - should be 3s
        self.agent._create_title_overlay("Test Title", 1080, 1920, 10.0)
        _, kwargs = mock_clip.call_args
        self.assertEqual(kwargs.get('duration'), 3.0)
        
        # Test 1s video - should be 1s
        self.agent._create_title_overlay("Test Title", 1080, 1920, 1.0)
        _, kwargs = mock_clip.call_args
        self.assertEqual(kwargs.get('duration'), 1.0)

    @patch('src.agents.video_assembly.agent.ImageClip')
    @patch('src.agents.video_assembly.agent.Image')
    @patch('src.agents.video_assembly.agent.ImageDraw')
    def test_fit_font_logic_ported(self, mock_draw, mock_image, mock_clip):
        # Verify helper methods exist
        self.assertTrue(hasattr(self.agent, '_fit_font_to_width'))
        self.assertTrue(hasattr(self.agent, '_wrap_text'))
        self.assertTrue(hasattr(self.agent, '_load_font'))

if __name__ == '__main__':
    unittest.main()
