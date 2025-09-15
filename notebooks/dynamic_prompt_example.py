"""
Example of using dynamic prompt with Pydantic models
Copy this code into your notebook cells
"""

import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from prompts.scrip_writer_agent import SCRIPT_WRITER_AGENT_TEMPLATE, VIDEO_SCRIPT_PARSER

# Load environment variables
load_dotenv()

def test_dynamic_prompt():
    """
    Test the dynamic prompt with Pydantic models
    """
    print("🧪 Testing dynamic prompt with Pydantic models...")
    
    # Initialize LLM
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key:
        print("❌ GEMINI_API_KEY not found")
        return
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=gemini_api_key,
        temperature=0.7
    )
    
    # Create chain with dynamic prompt and parser
    chain = SCRIPT_WRITER_AGENT_TEMPLATE | llm | VIDEO_SCRIPT_PARSER
    
    # Test with a simple subject
    test_subject = "Why do cats purr?"
    test_language = "English"
    test_max_scenes = 3
    
    print(f"📝 Generating script for: {test_subject}")
    
    try:
        # Generate structured output
        result = chain.invoke({
            "subject": test_subject,
            "language": test_language,
            "max_video_scenes": test_max_scenes
        })
        
        print("✅ Dynamic prompt with Pydantic parser successful!")
        print(f"📄 Result type: {type(result)}")
        print(f"📄 Title: {result.title}")
        print(f"📄 Character: {result.main_character_description}")
        print(f"📄 Total scenes: {result.total_scene_count}")
        
        # Show some scene details
        print("\n🎬 Scene details:")
        for i, scene in enumerate(result.all_scenes[:3], 1):
            print(f"  Scene {i}: {scene.scene_type.value} - {scene.voice_tone.value}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def show_available_options():
    """
    Show all available options from Pydantic models
    """
    from models.models import SceneType, ImageStyle, VoiceTone, TransitionType, HookTechnique
    
    print("📋 Available Options from Pydantic Models:")
    print("\n🎬 Scene Types:")
    for scene_type in SceneType:
        print(f"  - {scene_type.value}")
    
    print("\n🎨 Image Styles:")
    for image_style in ImageStyle:
        print(f"  - {image_style.value}")
    
    print("\n🎤 Voice Tones:")
    for voice_tone in VoiceTone:
        print(f"  - {voice_tone.value}")
    
    print("\n🔄 Transition Types:")
    for transition_type in TransitionType:
        print(f"  - {transition_type.value}")
    
    print("\n🎯 Hook Techniques:")
    for hook_technique in HookTechnique:
        print(f"  - {hook_technique.value}")

def demonstrate_dynamic_update():
    """
    Demonstrate how adding new enum values automatically updates the prompt
    """
    print("\n🔄 Dynamic Update Demonstration:")
    print("1. When you add new enum values to models.py")
    print("2. The prompt automatically includes them")
    print("3. No manual prompt updates needed!")
    print("4. LangChain's PydanticOutputParser handles the rest")
    
    # Show current prompt length
    prompt_text = SCRIPT_WRITER_AGENT_TEMPLATE.template
    print(f"\n📝 Current prompt length: {len(prompt_text)} characters")
    print(f"📋 Format instructions length: {len(VIDEO_SCRIPT_PARSER.get_format_instructions())} characters")

if __name__ == "__main__":
    print("🚀 Dynamic Prompt with Pydantic Models Example")
    print("=" * 60)
    
    # Show available options
    show_available_options()
    
    # Demonstrate dynamic update concept
    demonstrate_dynamic_update()
    
    # Test the dynamic prompt
    print("\n" + "=" * 60)
    result = test_dynamic_prompt()
    
    if result:
        print("\n✅ Success! The dynamic prompt works perfectly with Pydantic models.")
        print("🎯 Key Benefits:")
        print("  - Automatic prompt updates when models change")
        print("  - Type-safe output parsing")
        print("  - No manual prompt maintenance needed")
        print("  - LangChain handles all the complexity")
