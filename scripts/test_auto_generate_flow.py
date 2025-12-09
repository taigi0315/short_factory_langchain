import asyncio
import os
import sys
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.agents.image_gen.agent import ImageGenAgent
from src.agents.video_gen.agent import VideoGenAgent
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings, VideoScript, VisualSegment

async def test_auto_generate_flow():
    print("Testing Auto Generate Flow...")
    
    # 1. Create a dummy script with 6 scenes
    scenes = []
    for i in range(1, 7):
        scenes.append(Scene(
            scene_number=i,
            scene_type=SceneType.EXPLANATION,
            content=[VisualSegment(
                segment_text=f"This is scene {i}",
                image_prompt=f"A beautiful scene number {i}"
            )],
            voice_tone=VoiceTone.CALM,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
            image_style=ImageStyle.CINEMATIC,
            needs_animation=False,
            transition_to_next=TransitionType.NONE
        ))
        
    script = VideoScript(
        title="Auto Gen Test", 
        scenes=scenes,
        main_character_description="A generic character",
        overall_style="Cinematic",
        global_visual_style="Realistic"
    )
    
    # 2. Generate Images (Simulate parallel requests)
    print("Generating images...")
    image_agent = ImageGenAgent()
    
    # Simulate what frontend does: call generate_images for each scene in parallel
    # But ImageGenAgent.generate_images takes a list.
    # The frontend calls API which calls generate_images([scene]).
    
    tasks = []
    for scene in scenes:
        tasks.append(image_agent.generate_images([scene]))
        
    results = await asyncio.gather(*tasks)
    
    # Collect paths
    image_map = {}
    for res in results:
        image_map.update(res)
        
    print(f"Generated {len(image_map)} images.")
    for i in range(1, 7):
        if i in image_map:
            print(f"Scene {i}: {image_map[i]}")
        else:
            print(f"Scene {i}: MISSING")
            
    # 3. Generate Video
    print("Generating video...")
    video_agent = VideoGenAgent()
    
    # Convert image_map to list of paths/placeholders
    # image_map is now Dict[int, List[str]]
    images_list = []
    for scene in scenes:
        paths = image_map.get(scene.scene_number)
        if paths:
            # Take the first image for each scene (or all if video gen supports multiple)
            images_list.append(paths[0] if isinstance(paths, list) else paths)
        else:
            print(f"Warning: No image for scene {scene.scene_number}")
            images_list.append("placeholder.jpg")
            
    # Generate audio (mock)
    audio_map = {} # Empty for now, VideoGen will generate mock audio
    
    video_path = await video_agent.generate_video(
        script=script,
        images=images_list,
        audio_map=audio_map
    )
    
    print(f"Video generated at: {video_path}")
    
if __name__ == "__main__":
    asyncio.run(test_auto_generate_flow())
