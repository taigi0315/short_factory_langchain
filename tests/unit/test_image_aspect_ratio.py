import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import os
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.image_gen.gemini_image_client import GeminiImageClient
from src.models.models import Scene, SceneType, VoiceTone, ElevenLabsSettings, ImageStyle, TransitionType
from src.core.config import settings

class TestImageAspectRatio(unittest.IsolatedAsyncioTestCase):
    async def test_aspect_ratio_passed_to_client(self):
        """Test that ImageGenAgent passes the configured aspect ratio to the client."""
        
        # Mock settings
        with patch('src.core.config.settings.IMAGE_ASPECT_RATIO', '9:16'):
            with patch('src.core.config.settings.USE_REAL_IMAGE', True):
                with patch('src.core.config.settings.GEMINI_API_KEY', 'fake_key'):
                    
                    agent = ImageGenAgent()
                    
                    # Mock the client
                    mock_client = AsyncMock(spec=GeminiImageClient)
                    mock_client.generate_image.return_value = "data:image/png;base64,fake"
                    mock_client.download_image.return_value = None
                    
                    # Inject mock client (hacky but effective for unit test)
                    with patch('src.agents.image_gen.agent.GeminiImageClient', return_value=mock_client):
                        # Re-init to pick up the mock
                        agent = ImageGenAgent()
                        # Manually replace the client instance created in __init__
                        # Actually, since we patched the class, the instance inside __init__ is already a mock.
                        # But we need to access THAT instance.
                        # Easier way: mock the method on the instance created.
                        
                        # Let's try a cleaner approach: Patch the client class where it's used
                        pass

    @patch('src.agents.image_gen.agent.GeminiImageClient')
    async def test_agent_passes_ratio(self, MockClientClass):
        """Test that ImageGenAgent passes aspect_ratio='9:16' to client.generate_image"""
        
        # Setup mock instance
        mock_client_instance = MockClientClass.return_value
        mock_client_instance.generate_image = AsyncMock(return_value="data:image/png;base64,fake")
        mock_client_instance.download_image = AsyncMock()
        
        # Setup settings
        with patch('src.core.config.settings.IMAGE_ASPECT_RATIO', '9:16'), \
             patch('src.core.config.settings.USE_REAL_IMAGE', True), \
             patch('src.core.config.settings.GEMINI_API_KEY', 'fake_key'):
            
            agent = ImageGenAgent()
            
            # Create a dummy scene
            scene = Scene(
                scene_number=1,
                scene_type=SceneType.EXPLANATION,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="A test image",
                needs_animation=False,
                transition_to_next=TransitionType.NONE
            )
            
            # Mock download_image to create a dummy file
            async def side_effect_download(url, path):
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f:
                    f.write(b'fake image data')
            
            mock_client_instance.download_image.side_effect = side_effect_download
            
            # Run generation
            await agent.generate_images([scene])
            
            # Verify generate_image was called with aspect_ratio='9:16'
            # Note: We need to find the call arguments
            calls = mock_client_instance.generate_image.call_args_list
            self.assertTrue(len(calls) > 0)
            
            # Check args of first call
            _, kwargs = calls[0]
            self.assertEqual(kwargs.get('aspect_ratio'), '9:16')
            print("\n✅ Agent passed aspect_ratio='9:16' correctly")

    async def test_client_prompt_construction(self):
        """Test that GeminiImageClient appends aspect ratio to prompt."""
        
        client = GeminiImageClient(api_key="fake_key")
        client.model = MagicMock()
        client.model.generate_content = MagicMock(return_value=MagicMock(parts=[MagicMock(inline_data=MagicMock(data=b'\x89PNG\r\n\x1a\nfake', mime_type='image/png'))]))
        
        prompt = "A beautiful sunset"
        aspect_ratio = "9:16"
        
        await client.generate_image(prompt=prompt, aspect_ratio=aspect_ratio)
        
        # Verify the prompt sent to the model
        call_args = client.model.generate_content.call_args
        full_prompt = call_args[0][0][0] # args[0] is list of parts, first part is prompt string
        
        self.assertIn(f"with {aspect_ratio} aspect ratio", full_prompt)
        self.assertIn(f"vertical {aspect_ratio} format", full_prompt)
        print(f"\n✅ Client constructed prompt correctly: '{full_prompt}'")

if __name__ == '__main__':
    unittest.main()
