# TICKET-013: Implement Real ElevenLabs Voice Synthesis

**Created:** 2025-01-21  
**Status:** APPROVED (Pre-approved by Architect)  
**Priority:** HIGH  
**Effort:** 1-2 days  
**Owner:** Backend Engineer

---

## Problem Statement

Currently, the `VideoGenAgent` uses mock voice synthesis (gTTS or silent audio). For production-quality videos, we need professional voice synthesis with multiple tones and emotions using ElevenLabs API.

**Current State:**
- Mock voice generation using gTTS (Google Text-to-Speech)
- Limited voice quality and tone options
- No caching or cost tracking
- Suitable for development only

**Desired State:**
- Real ElevenLabs API integration
- Multiple voice tones (enthusiastic, calm, serious, etc.)
- High-quality, natural-sounding voices
- Caching to reduce costs
- Cost tracking per audio generation

---

## Proposed Solution

### 1. ElevenLabs API Integration

Create `src/agents/voice_gen/elevenlabs_client.py`:

```python
import aiohttp
import hashlib
from pathlib import Path
from typing import Optional
from src.core.config import settings

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
        voice_settings: Optional[dict] = None
    ) -> Path:
        """Generate audio from text using ElevenLabs API."""
        
        # Check cache first
        cache_key = self._get_cache_key(text, voice_id, model_id)
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
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as response:
                if response.status == 200:
                    audio_data = await response.read()
                    cached_path.write_bytes(audio_data)
                    logger.info(f"Generated audio: {len(text)} chars -> {len(audio_data)} bytes")
                    return cached_path
                else:
                    error = await response.text()
                    raise Exception(f"ElevenLabs API error: {response.status} - {error}")
    
    def _get_cache_key(self, text: str, voice_id: str, model_id: str) -> str:
        """Generate cache key from text and voice parameters."""
        content = f"{text}|{voice_id}|{model_id}"
        return hashlib.sha256(content.encode()).hexdigest()
```

### 2. Voice Tone Mapping

Map `VoiceTone` enum to ElevenLabs voice IDs:

```python
# Voice ID mapping (use actual ElevenLabs voice IDs)
VOICE_TONE_MAPPING = {
    VoiceTone.ENTHUSIASTIC: "voice_id_enthusiastic",
    VoiceTone.CALM: "voice_id_calm",
    VoiceTone.SERIOUS: "voice_id_serious",
    VoiceTone.MYSTERIOUS: "voice_id_mysterious",
    VoiceTone.UPBEAT: "voice_id_upbeat"
}
```

### 3. Update VideoGenAgent

Modify `src/agents/video_gen/agent.py`:

```python
class VideoGenAgent:
    def __init__(self, use_real: bool = False):
        self.use_real = use_real
        if use_real:
            api_key = settings.ELEVENLABS_API_KEY
            if not api_key:
                raise ValueError("ELEVENLABS_API_KEY required for real voice synthesis")
            self.voice_client = ElevenLabsClient(api_key)
        else:
            self.voice_client = None
    
    async def generate_voice(self, text: str, tone: VoiceTone) -> Path:
        """Generate voice audio from text."""
        if self.use_real and self.voice_client:
            voice_id = VOICE_TONE_MAPPING.get(tone, VOICE_TONE_MAPPING[VoiceTone.CALM])
            return await self.voice_client.generate_audio(text, voice_id)
        else:
            # Fallback to gTTS
            return self._generate_mock_voice(text)
```

### 4. Configuration

Add to `.env`:

```bash
# ElevenLabs Voice Synthesis
USE_REAL_VOICE=true
ELEVENLABS_API_KEY=your_api_key_here
```

Add to `src/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Voice synthesis
    USE_REAL_VOICE: bool = Field(default=False)
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None)
```

### 5. Cost Tracking

Log cost per audio generation:

```python
# Approximate costs (check ElevenLabs pricing)
COST_PER_1K_CHARS = 0.30  # Example: $0.30 per 1,000 characters

def calculate_voice_cost(text: str) -> float:
    """Calculate approximate cost for voice generation."""
    char_count = len(text)
    return (char_count / 1000) * COST_PER_1K_CHARS

# In generate_audio:
cost = calculate_voice_cost(text)
logger.info(f"Voice generation cost: ${cost:.4f}")
```

---

## Success Criteria

- [ ] ElevenLabs API integration working end-to-end
- [ ] All `VoiceTone` enum values mapped to appropriate voices
- [ ] Audio quality suitable for production (manual QA)
- [ ] Caching works (same text + tone = cached audio)
- [ ] Cost per audio generation tracked and logged
- [ ] Fallback to gTTS works on API failure
- [ ] Integration test passes with real API
- [ ] Documentation updated in `docs/agents/README.md`

---

## Testing Plan

### Unit Tests

```python
# tests/agents/test_voice_gen.py

@pytest.mark.asyncio
async def test_elevenlabs_client():
    """Test ElevenLabs client integration."""
    client = ElevenLabsClient(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    text = "This is a test of voice synthesis."
    voice_id = "test_voice_id"
    
    audio_path = await client.generate_audio(text, voice_id)
    
    assert audio_path.exists()
    assert audio_path.suffix == ".mp3"
    assert audio_path.stat().st_size > 0

@pytest.mark.asyncio
async def test_voice_caching():
    """Test that identical requests use cache."""
    client = ElevenLabsClient(api_key=os.getenv("ELEVENLABS_API_KEY"))
    
    text = "Cache test"
    voice_id = "test_voice_id"
    
    # First call
    path1 = await client.generate_audio(text, voice_id)
    
    # Second call (should use cache)
    path2 = await client.generate_audio(text, voice_id)
    
    assert path1 == path2
    assert path1.exists()
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_video_gen_with_real_voice():
    """Test VideoGenAgent with real voice synthesis."""
    agent = VideoGenAgent(use_real=True)
    
    text = "Welcome to our amazing video!"
    tone = VoiceTone.ENTHUSIASTIC
    
    audio_path = await agent.generate_voice(text, tone)
    
    assert audio_path.exists()
    assert audio_path.suffix == ".mp3"
    
    # Verify audio duration is reasonable
    # (use librosa or similar to check duration)
```

### Manual Testing

1. **Voice Quality Check**:
   - Generate audio for each `VoiceTone`
   - Listen to quality, naturalness, emotion
   - Verify tone matches expected emotion

2. **Cost Tracking**:
   - Generate multiple audio clips
   - Verify cost calculations are accurate
   - Check cache reduces costs

3. **Error Handling**:
   - Test with invalid API key
   - Test with network timeout
   - Verify fallback to gTTS works

---

## Implementation Steps

1. **Create ElevenLabs Client** (2 hours)
   - Implement `ElevenLabsClient` class
   - Add caching logic
   - Add error handling and retries

2. **Voice Tone Mapping** (1 hour)
   - Research ElevenLabs voice library
   - Map each `VoiceTone` to appropriate voice ID
   - Test each voice for quality

3. **Update VideoGenAgent** (1 hour)
   - Integrate `ElevenLabsClient`
   - Update `generate_voice` method
   - Add cost tracking

4. **Configuration** (30 minutes)
   - Add environment variables
   - Update `Settings` class
   - Update `.env.example`

5. **Testing** (2 hours)
   - Write unit tests
   - Write integration tests
   - Manual QA for voice quality

6. **Documentation** (1 hour)
   - Update `docs/agents/README.md`
   - Add voice synthesis section
   - Document voice tone mapping

---

## Dependencies

- **Completed**: TICKET-007 (config consolidation) ✅
- **Parallel with**: TICKET-009 (image generation)
- **Blocks**: TICKET-014 (video generation - needs audio)

---

## Risks & Mitigation

### Risk: High API Costs

**Mitigation:**
- Implement aggressive caching (same text + tone = cache hit)
- Use character limits (max 500 chars per audio)
- Daily spending limits with alerts

### Risk: Voice Quality Issues

**Mitigation:**
- Manual QA for first 50 audio clips
- A/B testing different voices
- Fallback to different voice if quality poor

### Risk: API Rate Limits

**Mitigation:**
- Implement exponential backoff
- Queue-based processing if needed
- Monitor rate limit headers

---

## References

- ElevenLabs API Docs: https://docs.elevenlabs.io/
- ElevenLabs Voice Library: https://elevenlabs.io/voice-library
- Python async HTTP: https://docs.aiohttp.org/

---

## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent  
**Review Date:** 2025-01-21  
**Decision:** ✅ APPROVED (Pre-approved)

**Strategic Rationale:**
- **Critical for Production Quality**: Professional voice synthesis is essential for engaging videos
- **Similar Pattern to Images**: Follows proven caching and cost tracking patterns from TICKET-009
- **Blocks Video Assembly**: Audio is required input for final video generation
- **Well-Scoped**: Clear implementation with fallback strategy

**Implementation Phase:** Phase 1, Week 1-2  
**Sequence Order:** #2 (Can run in parallel with TICKET-009)

**Architectural Guidance:**
- **Reuse Caching Pattern**: Follow same SHA256-based caching as image generation
- **Cost Tracking**: Log cost per audio and aggregate per video
- **Graceful Degradation**: Fall back to gTTS seamlessly on API failure
- **Voice Selection**: Curate high-quality voices, not just first available

**Estimated Timeline:** 1-2 days  
**Recommended Owner:** Backend engineer (can be same as TICKET-009)

---

**Priority: HIGH** - Required for production-quality videos, blocks video assembly
