import os
import asyncio
import logging
from typing import List, Dict, Optional
from pathlib import Path
from src.models.models import Scene, VoiceTone
from src.core.config import settings
from gtts import gTTS
from src.agents.voice.elevenlabs_client import ElevenLabsClient

logger = logging.getLogger(__name__)

VOICE_MAPPING = {
    VoiceTone.ENTHUSIASTIC: "21m00Tcm4TlvDq8ikWAM", # Rachel
    VoiceTone.CALM: "AZnzlk1XvdvUeBnXmlld",        # Dombi
    VoiceTone.SERIOUS: "29vD33N1CtxCmqQRPOHJ",     # Drew
    VoiceTone.MYSTERIOUS: "2EiwWnXFnvU5JabPnv8n",  # Clyde
    VoiceTone.FRIENDLY: "ThT5KcBeYPX3keUQqHPh",    # Dorothy
    
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

from src.core.retry import retry_with_backoff
from src.agents.base_agent import BaseAgent

# ... imports ...

class VoiceAgent(BaseAgent):
    def __init__(self) -> None:
        self.client: Optional[ElevenLabsClient] = None
        self.use_real_voice = settings.USE_REAL_VOICE
        super().__init__(
            agent_name="VoiceAgent",
            require_llm=False
        )

    def _setup(self) -> None:
        """Agent-specific setup."""
        super()._setup()
        self.output_dir = Path(settings.GENERATED_ASSETS_DIR) / "audio"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.use_real_voice:
            if not settings.ELEVENLABS_API_KEY:
                logger.warning("ELEVENLABS_API_KEY not set. Falling back to gTTS mock mode.")
                self.use_real_voice = False
            else:
                self.client = ElevenLabsClient(settings.ELEVENLABS_API_KEY)
                logger.info("VoiceAgent initialized with Real ElevenLabs")
        
        self.mock_mode = not self.use_real_voice
        
        if not self.use_real_voice:
            logger.info("VoiceAgent initialized with Mock gTTS")

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
                voice_id = VOICE_MAPPING.get(scene.voice_tone, "21m00Tcm4TlvDq8ikWAM") # Default to Rachel
                
                voice_settings = None
                if hasattr(scene, 'elevenlabs_settings') and scene.elevenlabs_settings:
                    voice_settings = scene.elevenlabs_settings.model_dump()
                    
                    try:
                        import json
                        overrides = json.loads(settings.VOICE_SETTINGS_OVERRIDE)
                        tone_overrides = overrides.get(scene.voice_tone.value, {})
                        if tone_overrides:
                            logger.info(f"Applying voice overrides for {scene.voice_tone}: {tone_overrides}")
                            voice_settings.update(tone_overrides)
                    except Exception as e:
                        logger.warning(f"Failed to apply voice settings override: {e}")
                
                logger.info(f"Generating real audio for Scene {scene.scene_number} ({scene.voice_tone})...")
                
                # Use decorated method for retry logic
                generated_path = await self._generate_elevenlabs_audio_with_retry(
                    text=text,
                    voice_id=voice_id,
                    voice_settings=voice_settings
                )
                
                return scene.scene_number, str(generated_path)
                
            else:
                logger.info(f"  [Mock] Generating audio for Scene {scene.scene_number} using gTTS...")
                await asyncio.to_thread(self._generate_gtts, text, filepath)
                return scene.scene_number, filepath
                
        except Exception as e:
            logger.error(f"Failed to generate audio for Scene {scene.scene_number}: {e}")
            if self.use_real_voice:
                logger.info("Falling back to gTTS...")
                try:
                    await asyncio.to_thread(self._generate_gtts, text, filepath)
                    return scene.scene_number, filepath
                except Exception as fallback_error:
                    logger.error(f"Fallback failed: {fallback_error}")
                    raise fallback_error  # Re-raise fallback error
            raise e # Re-raise original error if not using real voice (or if fallback logic is skipped)

    @retry_with_backoff(operation_name="voice generation")
    async def _generate_elevenlabs_audio_with_retry(self, text: str, voice_id: str, voice_settings: Optional[dict] = None) -> str:
        """Generate audio using ElevenLabs with retry logic."""
        if not self.client:
             raise RuntimeError("ElevenLabs client not initialized")
             
        result = await self.client.generate_audio(
            text=text,
            voice_id=voice_id,
            voice_settings=voice_settings
        )
        return str(result)

    def _generate_gtts(self, text: str, filepath: str) -> None:
        tts = gTTS(text=text, lang='en')
        tts.save(filepath)

