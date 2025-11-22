import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.models.models import VoiceTone, Scene, ElevenLabsSettings, SceneType, TransitionType, ImageStyle
from src.agents.voice.agent import VoiceAgent
from src.core.config import settings

async def generate_gallery():
    print("🎨 Generating Voice Gallery...")
    print(f"Output Directory: {settings.GENERATED_ASSETS_DIR}/voice_gallery")
    
    agent = VoiceAgent()
    
    # Override output dir for gallery
    agent.output_dir = os.path.join(settings.GENERATED_ASSETS_DIR, "voice_gallery")
    os.makedirs(agent.output_dir, exist_ok=True)
    
    test_sentence = "I can't believe what I'm seeing! This is absolutely incredible."
    
    scenes = []
    for i, tone in enumerate(VoiceTone):
        print(f"Preparing scene for: {tone.value}")
        scene = Scene(
            scene_number=i + 1,
            scene_type=SceneType.EXPLANATION,
            dialogue=f"[{tone.value.upper()}] {test_sentence}",
            voice_tone=tone,
            elevenlabs_settings=ElevenLabsSettings.for_tone(tone),
            image_style=ImageStyle.CINEMATIC,
            image_create_prompt="test",
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        )
        scenes.append(scene)
    
    print(f"\n🚀 Starting generation for {len(scenes)} tones...")
    if not settings.USE_REAL_VOICE:
        print("⚠️  WARNING: Running in MOCK mode (gTTS). Set USE_REAL_VOICE=True and ELEVENLABS_API_KEY for real audio.")
    
    results = await agent.generate_voiceovers(scenes)
    
    print("\n✅ Generation Complete!")
    for scene_num, path in results.items():
        tone = scenes[scene_num-1].voice_tone.value
        print(f"  - {tone}: {path}")

if __name__ == "__main__":
    asyncio.run(generate_gallery())
