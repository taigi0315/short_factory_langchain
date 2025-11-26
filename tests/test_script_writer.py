import unittest
from unittest.mock import MagicMock, patch
from src.agents.script_writer.agent import ScriptWriterAgent
from src.models.models import VideoScript, Scene, SceneType, ImageStyle, VoiceTone, TransitionType, ElevenLabsSettings

class TestScriptWriterAgent(unittest.TestCase):
    @patch('src.agents.script_writer.agent.ChatGoogleGenerativeAI')
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
            ],
            conclusion=Scene(
                scene_number=5,
                scene_type=SceneType.CONCLUSION,
                voice_tone=VoiceTone.CALM,
                elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
                image_style=ImageStyle.CINEMATIC,
                image_create_prompt="Conclusion prompt",
                needs_animation=False,
                transition_to_next=TransitionType.NONE,
                content=[]
            ),
            music_suggestion="Happy music",
            video_description="Description",
            hashtags=["#test"],
            hook=Scene(
                 scene_number=1,
                 scene_type=SceneType.HOOK,
                 voice_tone=VoiceTone.EXCITED,
                 elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.EXCITED),
                 image_style=ImageStyle.CINEMATIC,
                 image_create_prompt="Test prompt",
                 needs_animation=False,
                 transition_to_next=TransitionType.FADE,
                 content=[]
            )
        )
        
        # Mock the chain's invoke method
        agent.chain = MagicMock()
        agent.chain.invoke.return_value = dummy_script
        
        # Run method
        result = agent.generate_script("coffee", max_scenes=1)
        
        # Verify
        self.assertEqual(result.title, "Test Video")
        agent.chain.invoke.assert_called_once()

if __name__ == '__main__':
    unittest.main()
