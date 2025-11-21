import os
from typing import List, Dict
from src.models.models import Scene
from src.core.config import settings
from gtts import gTTS

class VoiceAgent:
    def __init__(self):
        # Use centralized config
        self.mock_mode = not settings.USE_REAL_VOICE
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "audio")
        os.makedirs(self.output_dir, exist_ok=True)

    async def generate_voiceovers(self, scenes: List[Scene]) -> Dict[int, str]:
        """
        Generates audio files for a list of scenes.
        Returns a dictionary mapping scene_number to local_file_path.
        """
        audio_paths = {}
        print(f"Generating voiceovers for {len(scenes)} scenes...")

        for scene in scenes:
            filename = f"scene_{scene.scene_number}.mp3"
            filepath = os.path.join(self.output_dir, filename)
            
            if self.mock_mode:
                # Use gTTS for a free, working fallback
                print(f"  [Mock] Generating audio for Scene {scene.scene_number} using gTTS...")
                text = scene.dialogue if scene.dialogue else "[No dialogue for this scene]"
                tts = gTTS(text=text, lang='en')
                tts.save(filepath)
                audio_paths[scene.scene_number] = filepath
            else:
                # TODO: Implement ElevenLabs API here
                pass
                
        return audio_paths
