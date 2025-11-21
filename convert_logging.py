#!/usr/bin/env python3
"""Convert f-string logging to structured logging format."""

import re
import sys

def convert_logging(filepath):
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Pattern 1: logger.info(f"Text {var}")
    # Convert to: logger.info("Text", var=var)
    
    # Simple replacements for common patterns
    replacements = [
        (r'logger\.info\(f"Generating video for script: \{script\.title\}"\)',
         'logger.info("Generating video for script", title=script.title)'),
        
        (r'logger\.warning\(f"Not enough images \(\{len\(images\)\}\) for scenes \(\{len\(sorted_scenes\)\}\)\. Reusing last image\."\)',
         'logger.warning("Not enough images for scenes. Reusing last image.", image_count=len(images), scene_count=len(sorted_scenes))'),
        
        (r'logger\.warning\(f"Missing audio for scene \{scene\.scene_number\}\. Using default duration\."\)',
         'logger.warning("Missing audio for scene. Using default duration.", scene_number=scene.scene_number)'),
        
        (r'logger\.info\(f"Rendering video to \{output_path\}\.\.\."\)',
         'logger.info("Rendering video...", output_path=str(output_path))'),
        
        (r'logger\.info\(f"Video generated successfully: \{output_path\}"\)',
         'logger.info("Video generated successfully", output_path=str(output_path))'),
        
        (r'logger\.error\(f"Video generation failed: \{e\}"',
         'logger.error("Video generation failed"'),
        
        (r'logger\.warning\(f"Image not found: \{image_path\}\. Using color placeholder\."\)',
         'logger.warning("Image not found. Using color placeholder.", image_path=image_path)'),
        
        (r'logger\.warning\(f"Failed to create text overlay: \{e\}"\)',
         'logger.warning("Failed to create text overlay", error=str(e))'),
        
        (r'logger\.info\(f"Generating video from text: \{prompt\}"\)',
         'logger.info("Generating video from text", prompt=prompt)'),
        
        (r'logger\.error\(f"Failed to generate text video: \{e\}"\)',
         'logger.error("Failed to generate text video", exc_info=True)'),
        
        (r'logger\.info\(f"Generating video from image: \{image_path\}"\)',
         'logger.info("Generating video from image", image_path=image_path)'),
        
        (r'logger\.error\(f"Failed to generate image video: \{e\}"\)',
         'logger.error("Failed to generate image video", exc_info=True)'),
        
        # ImageGenAgent patterns
        (r'logger\.info\(f"Generating images for \{len\(scenes\)\} scenes\.\.\."\)',
         'logger.info("Generating images for scenes", count=len(scenes))'),
        
        (r'logger\.error\(f"Image generation failed for scene \{scene\.scene_number\}: \{result\}"\)',
         'logger.error("Image generation failed for scene", scene_number=scene.scene_number, error=str(result))'),
        
        (r'logger\.info\(f"✓ Using cached image for scene \{scene\.scene_number\}"\)',
         'logger.info("Using cached image for scene", scene_number=scene.scene_number)'),
        
        (r'logger\.info\(f"Generating image for scene \{scene\.scene_number\}"\)',
         'logger.info("Generating image for scene", scene_number=scene.scene_number)'),
        
        (r'logger\.debug\(f"Prompt: \{enhanced_prompt\}"\)',
         'logger.debug("Image prompt", prompt=enhanced_prompt)'),
        
        (r'logger\.info\(f"✓ Image saved: \{filepath\}"\)',
         'logger.info("Image saved", filepath=filepath)'),
        
        (r'logger\.error\(f"Image generation failed: \{e\}"\)',
         'logger.error("Image generation failed", error=str(e))'),
        
        (r'logger\.error\(f"Failed to download mock image: \{e\}"\)',
         'logger.error("Failed to download mock image", error=str(e))'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    with open(filepath, 'w') as f:
        f.write(content)
    
    print(f"✓ Converted {filepath}")

if __name__ == "__main__":
    convert_logging("src/agents/video_gen/agent.py")
    convert_logging("src/agents/image_gen/agent.py")
