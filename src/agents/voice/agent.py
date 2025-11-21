import os
import asyncio
import logging
from typing import List, Dict
from src.models.models import Scene, VoiceTone
from src.core.config import settings
from gtts import gTTS
from src.agents.voice.elevenlabs_client import ElevenLabsClient

logger = logging.getLogger(__name__)

# Default ElevenLabs Voice IDs (can be updated with specific voice clones)
# Using standard pre-made voices as defaults
VOICE_MAPPING = {
    VoiceTone.ENTHUSIASTIC: "21m00Tcm4TlvDq8ikWAM", # Rachel
    VoiceTone.CALM: "AZnzlk1XvdvUeBnXmlld",        # Dombi
    VoiceTone.SERIOUS: "29vD33N1CtxCmqQRPOHJ",     # Drew
    VoiceTone.MYSTERIOUS: "2EiwWnXFnvU5JabPnv8n",  # Clyde
    VoiceTone.FRIENDLY: "ThT5KcBeYPX3keUQqHPh",    # Dorothy
    # Fallback for others
    VoiceTone.EXCITED: "21m00Tcm4TlvDq8ikWAM",
    VoiceTone.CURIOUS: "ThT5KcBeYPX3keUQqHPh",
    VoiceTone.SAD: "AZnzlk1XvdvUeBnXmlld",
    VoiceTone.SURPRISED: "zrHiDhphv9ZnVXBqCLjz",
    VoiceTone.CONFIDENT: "29vD33N1CtxCmqQRPOHJ",
    VoiceTone.WORRIED: "AZnzlk1XvdvUeBnXmlld",
    VoiceTone.PLAYFUL: "zrHiDhphv9ZnVXBqCLjz",
    VoiceTone.DRAMATIC: "2EiwWnXFnvU5JabPnv8n",
    VoiceTone.SARCASTIC: "2EiwWnXFnvU5JabPnv8n",
}

class VoiceAgent:
    def __init__(self):
        # Use centralized config
        self.use_real_voice = settings.USE_REAL_VOICE
        self.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "audio")
        os.makedirs(self.output_dir, exist_ok=True)
        
        if self.use_real_voice:
            if not settings.ELEVENLABS_API_KEY:
                logger.warning("USE_REAL_VOICE is True but ELEVENLABS_API_KEY is missing. Falling back to mock.")
                self.use_real_voice = False
                self.client = None
            else:
                self.client = ElevenLabsClient(settings.ELEVENLABS_API_KEY)
                logger.info("VoiceAgent initialized with REAL ElevenLabs client")
        else:
            self.client = None
            logger.info("VoiceAgent initialized in MOCK mode (gTTS)")

    async def generate_voiceovers(self, scenes: List[Scene]) -> Dict[int, str]:
        """
        Generates audio files for a list of scenes.
        Returns a dictionary mapping scene_number to local_file_path.
        """
        logger.info(f"Generating voiceovers for {len(scenes)} scenes...")
        
        tasks = []
        for scene in scenes:
            tasks.append(self._generate_single_voiceover(scene))
            
        results = await asyncio.gather(*tasks)
        
        # Convert list of results to dictionary
        audio_paths = {}
        for scene_num, path in results:
            if path:
                audio_paths[scene_num] = path
                
        return audio_paths

    async def _generate_single_voiceover(self, scene: Scene) -> tuple[int, str]:
        """Generate voiceover for a single scene."""
        filename = f"scene_{scene.scene_number}.mp3"
        filepath = os.path.join(self.output_dir, filename)
        text = scene.dialogue if scene.dialogue else ""
        
        if not text:
            logger.warning(f"Scene {scene.scene_number} has no dialogue. Skipping audio.")
            return scene.scene_number, ""

        try:
            if self.use_real_voice and self.client:
                # Real ElevenLabs generation
                voice_id = VOICE_MAPPING.get(scene.voice_tone, "21m00Tcm4TlvDq8ikWAM") # Default to Rachel
                
                # Convert Pydantic settings to dict
                voice_settings = None
                if hasattr(scene, 'elevenlabs_settings') and scene.elevenlabs_settings:
                    voice_settings = scene.elevenlabs_settings.model_dump()
                
                logger.info(f"Generating real audio for Scene {scene.scene_number} ({scene.voice_tone})...")
                generated_path = await self.client.generate_audio(
                    text=text,
                    voice_id=voice_id,
                    voice_settings=voice_settings
                )
                
                # Copy/Move cached file to final destination if needed, or just return cached path
                # For simplicity, we'll just return the cached path as it's already in generated_assets/audio_cache
                # But to maintain the expected structure, we might want to symlink or copy.
                # Let's just return the cached path for now, as it's a valid path.
                return scene.scene_number, str(generated_path)
                
            else:
                # Mock gTTS generation
                logger.info(f"  [Mock] Generating audio for Scene {scene.scene_number} using gTTS...")
                # Run blocking gTTS in a thread to avoid blocking event loop
                await asyncio.to_thread(self._generate_gtts, text, filepath)
                return scene.scene_number, filepath
                
        except Exception as e:
            logger.error(f"Failed to generate audio for Scene {scene.scene_number}: {e}")
            # Fallback to gTTS on failure if we were trying real voice
            if self.use_real_voice:
                logger.info("Falling back to gTTS...")
                try:
                    await asyncio.to_thread(self._generate_gtts, text, filepath)
                    return scene.scene_number, filepath
                except Exception as fallback_error:
                    logger.error(f"Fallback failed: {fallback_error}")
            return scene.scene_number, ""

    def _generate_gtts(self, text: str, filepath: str):
        """Helper to run gTTS synchronously."""
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)

