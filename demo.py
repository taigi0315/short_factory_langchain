import os
from src.agents.story_finder.agent import StoryFinderAgent
from src.agents.script_writer.agent import ScriptWriterAgent
from src.core.utils import save_json_output

def main():
    print("🚀 Starting ShortFactory Demo")
    
    # 1. Story Finder
    subject = "Coffee"
    print(f"\n🔍 Finding stories for: {subject}")
    story_agent = StoryFinderAgent()
    
    # In a real run, this would call the LLM. 
    # For demo purposes, if no API key is present, we might fail.
    # But let's assume the user has keys or we catch the error.
    try:
        stories = story_agent.find_stories(subject, num_stories=3)
        print(f"✅ Found {len(stories.stories)} stories:")
        for i, story in enumerate(stories.stories, 1):
            print(f"  {i}. {story.title}: {story.hook}")
            
        # Select the first story
        selected_story = stories.stories[0]
        print(f"\n👉 Selected Story: {selected_story.title}")
        
        # 2. Script Writer
        print(f"\n📝 Generating script for: {selected_story.title}")
        script_agent = ScriptWriterAgent()
        script = script_agent.generate_script(selected_story.title)
        
        print(f"✅ Script generated: {script.title}")
        print(f"  - Scenes: {len(script.scenes)}")
        print(f"  - Character: {script.main_character_description}")
        
        # Save output
        save_json_output(script.model_dump(), "demo_script")
        print("\n💾 Script saved to output/ directory")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have set GEMINI_API_KEY in .env")

if __name__ == "__main__":
    main()
