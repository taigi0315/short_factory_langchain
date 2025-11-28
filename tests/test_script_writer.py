import unittest
from unittest.mock import MagicMock, patch
from src.agents.script_writer.agent import ScriptWriterAgent
from src.models.models import VideoScript, Scene, SceneType, ImageStyle, VoiceTone, TransitionType, ElevenLabsSettings

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

class TestScriptWriterAgent(unittest.TestCase):
    @patch('src.agents.base_agent.ChatGoogleGenerativeAI')
    def test_generate_script(self, mock_llm_class):
        # Setup mock
        mock_llm = MagicMock()
        mock_llm_class.return_value = mock_llm
        
        agent = ScriptWriterAgent()
        
        # Create a dummy response
        dummy_script = VideoScript(
            title="Test Video",
            main_character_description="A test character",
            overall_style="Educational",
            global_visual_style="Cinematic",
            scenes=[
                Scene(
                    scene_number=1,
                    scene_type=SceneType.HOOK,
                    voice_tone=VoiceTone.EXCITED,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 1",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                ),
                Scene(
                    scene_number=2,
                    scene_type=SceneType.EXPLANATION,
                    voice_tone=VoiceTone.CALM,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 2",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                ),
                Scene(
                    scene_number=3,
                    scene_type=SceneType.EXPLANATION,
                    voice_tone=VoiceTone.CALM,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 3",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                ),
                Scene(
                    scene_number=4,
                    scene_type=SceneType.CONCLUSION,
                    voice_tone=VoiceTone.CONFIDENT,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CONFIDENT),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Conclusion prompt",
                    needs_animation=False,
                    transition_to_next=TransitionType.NONE,
                    content=[]
                )
            ]
        )
        
        # Mock the chain's invoke method
        agent.chain = MagicMock()
        agent.chain.invoke.return_value = dummy_script
        
        # Run method
        result = agent.generate_script("coffee", max_scenes=1)
        
        # Verify
        self.assertEqual(result.title, "Test Video")
        agent.chain.invoke.assert_called_once()

class TestScriptWriterRouter(unittest.TestCase):
    @patch('src.agents.base_agent.ChatGoogleGenerativeAI')
    def test_router_selection(self, mock_llm_class):
        # Setup mock LLM
        mock_llm = MagicMock(spec=ChatGoogleGenerativeAI)
        mock_llm_class.return_value = mock_llm
        
        # Mock response to avoid validation errors
        dummy_script = VideoScript(
            title="Test Video",
            main_character_description="A test character",
            overall_style="Educational",
            global_visual_style="Cinematic",
            scenes=[
                Scene(
                    scene_number=1,
                    scene_type=SceneType.HOOK,
                    voice_tone=VoiceTone.EXCITED,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 1",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                ),
                Scene(
                    scene_number=2,
                    scene_type=SceneType.EXPLANATION,
                    voice_tone=VoiceTone.CALM,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 2",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                ),
                Scene(
                    scene_number=3,
                    scene_type=SceneType.EXPLANATION,
                    voice_tone=VoiceTone.CALM,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 3",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                ),
                Scene(
                    scene_number=4,
                    scene_type=SceneType.EXPLANATION,
                    voice_tone=VoiceTone.CALM,
                    elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="Test prompt 4",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE,
                    content=[]
                )
            ]
        )
        
        # Mock the LLM response to be an AIMessage
        mock_llm.invoke.return_value = AIMessage(content=dummy_script.model_dump_json())
        
        # Initialize agent
        agent = ScriptWriterAgent()
        
        # Test Case 1: News Category -> Should trigger Real Story Prompt
        try:
            agent.generate_script(subject="Test News", category="News", max_scenes=4)
            
            # Verify LLM was called
            mock_llm.invoke.assert_called()
            
            # Get the prompt passed to LLM
            # call_args[0][0] is the PromptValue
            prompt_value = mock_llm.invoke.call_args[0][0]
            prompt_text = prompt_value.to_string()
            
            # Check for Real Story persona
            self.assertIn("BBC/Netflix Documentary Director", prompt_text)
            self.assertIn("Strictly 8K Photorealism", prompt_text)
            
        except Exception as e:
            self.fail(f"Test 1 failed: {e}")

        # Test Case 2: Educational Category -> Should trigger Educational Prompt
        try:
            agent.generate_script(subject="Test Edu", category="Educational", max_scenes=4)
            
            prompt_value = mock_llm.invoke.call_args[0][0]
            prompt_text = prompt_value.to_string()
            
            # Check for Educational persona
            self.assertIn("Lead Animator for a high-end Tech Explainer channel", prompt_text)
            self.assertIn("3D Isometric Renders", prompt_text)
            
        except Exception as e:
            self.fail(f"Test 2 failed: {e}")

        # Test Case 3: Creative Category (Default) -> Should trigger Creative Prompt
        try:
            agent.generate_script(subject="Test Creative", category="Fiction", max_scenes=4)
            
            prompt_value = mock_llm.invoke.call_args[0][0]
            prompt_text = prompt_value.to_string()
            
            # Check for Creative persona
            self.assertIn("Movie Director", prompt_text)
            self.assertIn("Artistic freedom allowed", prompt_text)
            
        except Exception as e:
            self.fail(f"Test 3 failed: {e}")

if __name__ == '__main__':
    unittest.main()
