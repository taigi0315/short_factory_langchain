import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.video_gen.providers.luma import LumaVideoProvider
from src.core.config import settings

async def test_luma():
    print("🎥 Testing Luma Video Generation...")
    
    if not settings.LUMA_API_KEY:
        print("❌ LUMA_API_KEY is not set in config or env vars.")
        print("Please set it in .env or export it to run this test.")
        return

    provider = LumaVideoProvider()
    
    # Use a placeholder image or require one
    image_path = "test_image.jpg"
    if not os.path.exists(image_path):
        print(f"⚠️  {image_path} not found. Please provide a valid image path to test.")
        # Create a dummy image for testing if needed, or just ask user
        # For now, let's just warn
        return

    prompt = "A cinematic camera pan around the subject, 4k quality"
    
    try:
        print(f"🚀 Triggering generation for: {image_path}")
        print(f"📝 Prompt: {prompt}")
        
        video_path = await provider.generate_video(image_path, prompt)
        
        print(f"✅ Video generated successfully: {video_path}")
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_luma())
