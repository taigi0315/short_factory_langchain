import unittest
from src.agents.image_gen.agent import ImageGenAgent
from src.models.models import ImageStyle

class TestGlobalVisualStyle(unittest.TestCase):
    def setUp(self):
        self.agent = ImageGenAgent()
    
    def test_enhance_prompt_with_global_style(self):
        """Test that global_visual_style is appended to enhanced prompts."""
        base_prompt = "A cat sitting on a chair"
        style = ImageStyle.CINEMATIC
        global_visual_style = "Pixar 3D animation style, vibrant colors"
        
        enhanced = self.agent._enhance_prompt_text(base_prompt, style, global_visual_style)
        
        # Verify base prompt is included
        self.assertIn("A cat sitting on a chair", enhanced)
        
        # Verify global visual style is appended
        self.assertIn("Pixar 3D animation style, vibrant colors", enhanced)
        
        # Verify style enhancers are still included
        self.assertIn("photorealistic", enhanced.lower())
    
    def test_enhance_prompt_without_global_style(self):
        """Test that prompts work without global_visual_style."""
        base_prompt = "A dog running"
        style = ImageStyle.WIDE_ESTABLISHING_SHOT
        
        enhanced = self.agent._enhance_prompt_text(base_prompt, style)
        
        # Verify base prompt is included
        self.assertIn("A dog running", enhanced)
        
        # Verify style enhancers are included
        self.assertIn("wide", enhanced.lower())
    
    def test_global_style_consistency(self):
        """Test that the same global style is used across multiple prompts."""
        global_style = "Watercolor painting style, soft pastel colors"
        
        prompt1 = self.agent._enhance_prompt_text("Scene 1", ImageStyle.CINEMATIC, global_style)
        prompt2 = self.agent._enhance_prompt_text("Scene 2", ImageStyle.CLOSE_UP_REACTION, global_style)
        
        # Both should include the global style
        self.assertIn(global_style, prompt1)
        self.assertIn(global_style, prompt2)

if __name__ == '__main__':
    unittest.main()
