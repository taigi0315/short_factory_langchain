import unittest
import os
from src.agents.script_writer.agent import ScriptWriterAgent
from src.models.models import VideoScript, SceneType
from src.core.config import settings

class TestScriptPromptRegression(unittest.TestCase):
    def setUp(self):
        # Ensure we are in a mode that allows testing (Mock or Real)
        # For regression of the PROMPT, we ideally want Real LLM, but for CI/CD we might use Mock.
        # Here we will check if we can run a generation.
        self.agent = ScriptWriterAgent()

    def test_script_structure_compliance(self):
        """
        Test that the generated script complies with the new structural requirements:
        1. Valid JSON parsing (implied by successful return)
        2. 5-8 scenes (as per config)
        3. First scene is a HOOK
        4. Image prompts are detailed (> 50 chars)
        """
        # Use a standard subject
        subject = "The history of coffee"
        
        try:
            script: VideoScript = self.agent.generate_script(subject)
            
            # 1. Validate basic structure
            self.assertIsInstance(script, VideoScript)
            self.assertTrue(len(script.scenes) >= settings.MIN_SCENES, f"Script has {len(script.scenes)} scenes, expected >= {settings.MIN_SCENES}")
            self.assertTrue(len(script.scenes) <= settings.MAX_SCENES, f"Script has {len(script.scenes)} scenes, expected <= {settings.MAX_SCENES}")
            
            # 2. Validate Story Arc (First scene MUST be Hook)
            first_scene = script.scenes[0]
            # Note: The model defines SceneType.HOOK, but the prompt might use it or just use the hook_technique field.
            # The new prompt requirement says "First scene is ALWAYS the hook scene".
            # We check if hook_technique is present.
            self.assertIsNotNone(first_scene.hook_technique, "First scene must have a hook_technique")
            
            # 3. Validate Image Prompts
            for i, scene in enumerate(script.scenes):
                self.assertTrue(len(scene.image_create_prompt) > 50, f"Scene {i+1} image prompt is too short: {len(scene.image_create_prompt)} chars")
                
            print(f"\n✅ Regression Test Passed for subject: {subject}")
            print(f"Title: {script.title}")
            print(f"Scenes: {len(script.scenes)}")
            print(f"Hook: {first_scene.hook_technique}")
            
        except Exception as e:
            # If it fails, it might be due to LLM or parsing
            self.fail(f"Script generation failed: {str(e)}")

if __name__ == '__main__':
    unittest.main()
