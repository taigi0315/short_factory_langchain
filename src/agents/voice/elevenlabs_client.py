import aiohttp
import hashlib
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from src.core.config import settings

logger = logging.getLogger(__name__)

class ElevenLabsClient:
    """Async client for ElevenLabs text-to-speech API."""
    
    BASE_URL = "https://api.elevenlabs.io/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.cache_dir = Path(settings.GENERATED_ASSETS_DIR) / "audio_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_audio(
        self,
        text: str,
        voice_id: str,
        model_id: str = "eleven_monolingual_v1",
        voice_settings: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Generate audio from text using ElevenLabs API."""
        
        # Check cache first
        cache_key = self._get_cache_key(text, voice_id, model_id, voice_settings)
        cached_path = self.cache_dir / f"{cache_key}.mp3"
        
        if cached_path.exists():
            logger.info(f"Cache hit for audio: {cache_key[:8]}...")
            return cached_path
        
        # Call ElevenLabs API
        url = f"{self.BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "text": text,
            "model_id": model_id,
            "voice_settings": voice_settings or {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        audio_data = await response.read()
                        cached_path.write_bytes(audio_data)
                        
                        # Log cost (approximate)
                        cost = self._calculate_cost(text)
                        logger.info(f"Generated audio: {len(text)} chars -> {len(audio_data)} bytes. Est. Cost: ${cost:.4f}")
                        
                        return cached_path
                    else:
                        error = await response.text()
                        raise Exception(f"ElevenLabs API error: {response.status} - {error}")
        except Exception as e:
            logger.error(f"ElevenLabs generation failed: {e}")
            raise

    def _get_cache_key(self, text: str, voice_id: str, model_id: str, voice_settings: Optional[Dict[str, Any]]) -> str:
        """Generate cache key from text and voice parameters."""
        # Include voice settings in cache key if provided
        settings_str = str(sorted(voice_settings.items())) if voice_settings else "default"
        content = f"{text}|{voice_id}|{model_id}|{settings_str}"
        return hashlib.sha256(content.encode()).hexdigest()

    def _calculate_cost(self, text: str) -> float:
        """Calculate approximate cost for voice generation."""
        # Approximate cost: $0.30 per 1,000 characters (standard tier)
        COST_PER_1K_CHARS = 0.30
        char_count = len(text)
        return (char_count / 1000) * COST_PER_1K_CHARS
