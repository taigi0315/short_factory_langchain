import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.script_writer.agent import ScriptWriterAgent
from src.core.config import settings
from src.models.models import VideoScript

async def test_global_visual_style():
    print("🚀 Testing TICKET-024: Global Visual Style Generation")
    
    # Initialize agent (mock mode is fine if mock supports it, but we modified the PROMPT which is used by LLM)
    # If we are in mock mode, the agent returns a fixed mock response. 
    # We need to check if the mock response includes the new field, OR if we are using real LLM.
    # The user environment seems to have REAL LLM enabled based on logs.
    
    agent = ScriptWriterAgent()
    
    # If using mock, we need to ensure the mock data has the field.
    # Let's check if we are using real LLM.
    if settings.USE_REAL_LLM:
        print("Using REAL LLM for generation...")
        try:
            script = agent.generate_script(
                subject="The history of coffee",
                language="English",
                max_scenes=4
            )
            
            print(f"\n✅ Script Generated: {script.title}")
            print(f"🎨 Global Visual Style: {getattr(script, 'global_visual_style', 'MISSING')}")
            
            if hasattr(script, 'global_visual_style') and script.global_visual_style:
                print("✅ global_visual_style is present and populated.")
            else:
                print("❌ global_visual_style is MISSING or empty.")
                
            # Check if scene prompts use it (heuristic check)
            print("\nChecking scene prompts for style reference...")
            for i, scene in enumerate(script.scenes):
                print(f"Scene {i+1} Prompt: {scene.image_create_prompt[:100]}...")
                
        except Exception as e:
            print(f"❌ Error during generation: {e}")
    else:
        print("⚠️ Using MOCK mode. Please ensure Mock data is updated if needed.")
        # We haven't updated the mock data generator, so this might fail if it validates the model strictly
        # and the mock data is missing the field.
        # However, Pydantic models usually allow missing fields if Optional, but we made it required (str).
        # So Mock generation might fail if we didn't update the mock return.
        
        # Let's try to generate and see.
        try:
            script = await agent.generate_script(
                subject="Test Subject",
                language="English",
                max_scenes=4
            )
            print(f"Mock Script Style: {getattr(script, 'global_visual_style', 'MISSING')}")
        except Exception as e:
            print(f"❌ Mock generation failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_global_visual_style())
