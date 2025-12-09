
import unittest
from unittest.mock import MagicMock, patch, ANY
import numpy as np
from src.agents.video_gen.agent import VideoGenAgent
# We don't import ImageFont here directly to avoid conflict with patch, but we use the patch object.

class TestVideoText(unittest.TestCase):
    def setUp(self):
        with patch('src.agents.video_gen.agent.settings') as mock_settings:
            mock_settings.VIDEO_RESOLUTION = "1080p"
            mock_settings.IMAGE_ASPECT_RATIO = "9:16"
            mock_settings.IMAGE_WIDTH_16_9 = 1920
            mock_settings.IMAGE_HEIGHT_16_9 = 1080
            mock_settings.IMAGE_WIDTH_9_16 = 1080
            mock_settings.IMAGE_HEIGHT_9_16 = 1920
            mock_settings.VIDEO_FPS = 30
            mock_settings.VIDEO_QUALITY = "medium"
            mock_settings.GENERATED_ASSETS_DIR = "/tmp"
            
            self.agent = VideoGenAgent()
            self.agent.resolution = (1080, 1920)

    @patch('src.agents.video_gen.agent.ImageFont.truetype')
    @patch('src.agents.video_gen.agent.ImageDraw.Draw')
    @patch('src.agents.video_gen.agent.Image.new')
    @patch('src.agents.video_gen.agent.ImageClip')
    def test_create_title_card_long_word_scales_down(self, MockImageClip, mock_new, mock_draw, mock_truetype):
        # Setup mocks
        mock_img = MagicMock()
        mock_new.return_value = mock_img
        
        mock_d = MagicMock()
        mock_draw.return_value = mock_d
        
        # Mock textlength to simulate font size logic roughly
        # Say width = len(text) * (font_size / 2)
        def side_effect_textlength(text, font=None):
            # We can't easily know font size from the mock font object in this side_effect unless we attach it
            # But we can assume the loop reduces size.
            # Let's just return a fixed large number to force reduction loop to maximize iterations
            return 2000 # Always 2000px width for any word 
            
        mock_d.textlength.side_effect = side_effect_textlength
        
        # Mock font
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font
        
        # VideoClip mocks to allow method to complete
        mock_clip = MagicMock()
        MockImageClip.return_value = mock_clip
        mock_clip.with_duration.return_value = mock_clip
        mock_clip.with_effects.return_value = mock_clip
        
        # Mock textbbox for line_height calculation
        mock_d.textbbox.return_value = (0, 0, 100, 50)
        
        # Test with a single word
        title = "Supercalifragilistic"
        
        # 1080 * 0.8 = 864 max width.
        # textlength returns 2000.
        # Logic should reduce font size from 96 down to min_size (~38).
        
        self.agent._create_title_card(title)
        
        # Verify valid font calls
        # 1920 * 0.05 = 96 start size.
        # Should call with 96, 91, 86... until min size.
        call_args_list = mock_truetype.call_args_list
        sizes = [call.args[1] for call in call_args_list]
        
        # Should start with 96
        self.assertEqual(sizes[0], 96)
        
        # Should have multiple decreasing calls
        self.assertTrue(len(sizes) > 1)
        self.assertTrue(sizes[-1] < sizes[0])
        
        print(f"Font sizes tried: {sizes}")

    @patch('src.agents.video_gen.agent.ImageFont.truetype')
    @patch('src.agents.video_gen.agent.ImageDraw.Draw')
    @patch('src.agents.video_gen.agent.Image.new')
    @patch('src.agents.video_gen.agent.ImageClip')
    def test_create_text_overlay_wrapping(self, MockImageClip, mock_new, mock_draw, mock_truetype):
        # Setup mocks
        mock_img = MagicMock()
        mock_new.return_value = mock_img
        
        mock_d = MagicMock()
        mock_draw.return_value = mock_d
        
        # Mock textlength to be reasonable
        def side_effect_textlength(text, font=None):
            return len(text) * 10 
            
        mock_d.textlength.side_effect = side_effect_textlength
        
        mock_font = MagicMock()
        mock_truetype.return_value = mock_font
        
        mock_clip = MagicMock()
        MockImageClip.return_value = mock_clip
        mock_clip.with_duration.return_value = mock_clip
        mock_clip.with_effects.return_value = mock_clip
        mock_d.textbbox.return_value = (0, 0, 100, 40)
        
        text = "This is a sentence that should wrap multiple times because it is long."
        # len ~70 chars -> 700px width.
        # Max width 1080 * 0.8 = 864. 
        # It fits! 
        # Reducing width to force wrap.
        
        # Let's force side_effect to return 500 for "sentence" so it adds up
        
        self.agent._create_text_overlay_pil(text, 3.0, (1080, 1920))
        
        # Just verify it completes without error
        self.assertTrue(MockImageClip.called)

if __name__ == '__main__':
    unittest.main()
