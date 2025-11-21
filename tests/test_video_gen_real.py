import unittest
import os
import shutil
import asyncio
from pathlib import Path
from PIL import Image
from gtts import gTTS
from src.agents.video_gen.agent import VideoGenAgent
from src.models.models import VideoScript, Scene, ImageStyle
from src.core.config import settings

class TestVideoGenReal(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.test_dir = Path("test_assets_video")
        self.test_dir.mkdir(exist_ok=True)
        self.agent = VideoGenAgent()
        # Override output dir to test dir
        self.agent.output_dir = self.test_dir

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def create_dummy_image(self, name, color):
        path = self.test_dir / name
        img = Image.new('RGB', (1920, 1080), color=color)
        img.save(path)
        return str(path)

    def create_dummy_audio(self, name, text):
        path = self.test_dir / name
        tts = gTTS(text=text, lang='en')
        tts.save(str(path))
        return str(path)

    async def test_generate_video_end_to_end(self):
        # 1. Setup Assets
        img1 = self.create_dummy_image("scene1.jpg", "red")
        img2 = self.create_dummy_image("scene2.jpg", "blue")
        
        audio1 = self.create_dummy_audio("scene1.mp3", "This is the first scene of the video.")
        audio2 = self.create_dummy_audio("scene2.mp3", "And this is the second scene with blue background.")

        # 2. Setup Script
        from src.models.models import SceneType, VoiceTone, ElevenLabsSettings, TransitionType
        
        default_settings = ElevenLabsSettings(stability=0.5, similarity_boost=0.75, style=0.0, speed=1.0, loudness=0.0)
        
        script = VideoScript(
            title="Test Video",
            main_character_description="A generic character",
            overall_style="educational",
            scenes=[
                Scene(
                    scene_number=1,
                    scene_type=SceneType.HOOK,
                    visual_description="Red background",
                    dialogue="This is the first scene of the video.",
                    text_overlay="Scene 1",
                    voice_tone=VoiceTone.EXCITED,
                    elevenlabs_settings=default_settings,
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="A red background",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE
                ),
                Scene(
                    scene_number=2,
                    scene_type=SceneType.EXPLANATION,
                    visual_description="Blue background",
                    dialogue="And this is the second scene with blue background.",
                    text_overlay="Scene 2",
                    voice_tone=VoiceTone.CALM,
                    elevenlabs_settings=default_settings,
                    image_style=ImageStyle.CINEMATIC,
                    image_create_prompt="A blue background",
                    needs_animation=False,
                    transition_to_next=TransitionType.FADE
                )
            ]
        )

        # 3. Run Generation
        images = [img1, img2]
        audio_map = {1: audio1, 2: audio2}
        
        print("\nGenerating video... this might take a moment.")
        video_path = await self.agent.generate_video(
            script=script,
            images=images,
            audio_map=audio_map,
            style=ImageStyle.CINEMATIC
        )

        # 4. Verify
        print(f"Video generated at: {video_path}")
        self.assertTrue(os.path.exists(video_path))
        self.assertTrue(video_path.endswith(".mp4"))
        self.assertGreater(os.path.getsize(video_path), 1000) # Should be > 1KB

if __name__ == "__main__":
    unittest.main()
