import unittest
from unittest.mock import MagicMock, patch, AsyncMock
from src.agents.director.agent import DirectorAgent
from src.models.models import VideoScript, Scene, SceneType, VoiceTone, ImageStyle, VisualSegment, ElevenLabsSettings, TransitionType
from src.agents.director.models import DirectedScript, DirectedScene, CinematicDirection
from src.agents.director.cinematic_language import ShotType, CameraMovement

class TestDirectorAgent(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.agent = DirectorAgent()
        # Mock LLM
        self.agent.llm = MagicMock()
        self.agent.llm.invoke = MagicMock()

    async def test_analyze_script_structure(self):
        """Test that analyze_script returns a valid DirectedScript structure"""
        # Create a dummy script
        scene1 = Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            voice_tone=VoiceTone.EXCITED,
            image_style=ImageStyle.CINEMATIC,
            content=[
                VisualSegment(segment_text="Hello world", image_prompt="A person saying hello")
            ],
            elevenlabs_settings=ElevenLabsSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                speed=1.0,
                loudness=0.0
            ),
            needs_animation=False,
            transition_to_next=TransitionType.FADE
        )
        script = VideoScript(
            title="Test Video",
            overall_style="Cinematic",
            global_visual_style="Realistic",
            main_character_description="A developer",
            scenes=[scene1, scene1, scene1, scene1] # Duplicate scenes to satisfy min count
        )

        # Mock LLM response
        mock_response_content = """
        {
            "shot_type": "medium",
            "camera_movement": "static",
            "camera_angle": "eye_level",
            "lighting_mood": "soft",
            "composition": "rule_of_thirds",
            "emotional_purpose": "Intro",
            "narrative_function": "Setup",
            "enhanced_image_prompt": "Enhanced prompt",
            "visual_segments": [
                {"image_prompt": "Super enhanced prompt for hello"}
            ],
            "director_notes": "Notes"
        }
        """
        self.agent.llm.invoke.return_value.content = mock_response_content

        # Run analysis
        directed_script = await self.agent.analyze_script(script)

        # Verify
        self.assertIsInstance(directed_script, DirectedScript)
        self.assertEqual(len(directed_script.directed_scenes), 4)
        
        directed_scene = directed_script.directed_scenes[0]
        self.assertIsInstance(directed_scene, DirectedScene)
        self.assertEqual(directed_scene.direction.shot_type, ShotType.MEDIUM)
        
        # Verify visual segments
        self.assertEqual(len(directed_scene.visual_segments), 1)
        self.assertEqual(directed_scene.visual_segments[0].image_prompt, "Super enhanced prompt for hello")

    async def test_fallback_logic(self):
        """Test fallback when LLM fails"""
        scene1 = Scene(
            scene_number=1,
            scene_type=SceneType.HOOK,
            voice_tone=VoiceTone.EXCITED,
            image_style=ImageStyle.CINEMATIC,
            content=[
                VisualSegment(segment_text="Hello", image_prompt="Basic prompt")
            ],
            elevenlabs_settings=ElevenLabsSettings(
                stability=0.5,
                similarity_boost=0.75,
                style=0.0,
                speed=1.0,
                loudness=0.0
            ),
            needs_animation=False,
            transition_to_next=TransitionType.FADE
        )
        script = VideoScript(
            title="Test Video",
            overall_style="Cinematic",
            global_visual_style="Realistic",
            main_character_description="A developer",
            scenes=[scene1, scene1, scene1, scene1] # Duplicate scenes to satisfy min count
        )

        # Mock LLM to raise exception
        self.agent.llm.invoke.side_effect = Exception("LLM Error")

        # Run analysis
        directed_script = await self.agent.analyze_script(script)

        # Verify fallback
        self.assertIsInstance(directed_script, DirectedScript)
        directed_scene = directed_script.directed_scenes[0]
        self.assertEqual(directed_scene.direction.director_notes, "Fallback direction for mysterious emotion")  # Hook scenes map to mysterious
        
        # Verify fallback segments (should use original prompt)
        self.assertEqual(len(directed_scene.visual_segments), 1)
        self.assertEqual(directed_scene.visual_segments[0].image_prompt, "Basic prompt")

if __name__ == '__main__':
    unittest.main()
