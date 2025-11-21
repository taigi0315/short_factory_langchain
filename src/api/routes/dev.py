from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.video_gen.agent import VideoGenAgent
from src.core.config import settings
import os
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings
from typing import Optional

router = APIRouter()

class ImageGenerationRequest(BaseModel):
    prompt: str
    style: ImageStyle = ImageStyle.CINEMATIC
    scene_number: int = 1

class ImageGenerationResponse(BaseModel):
    image_path: str
    url: str  # Local URL for frontend

@router.post("/generate-image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest):
    """Generate a single image for dev testing."""
    agent = ImageGenAgent()
    
    # Create a minimal scene object for the agent
    scene = Scene(
        scene_number=request.scene_number,
        scene_type=SceneType.EXPLANATION,
        voice_tone=VoiceTone.CALM, # Default
        elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.CALM),
        image_style=request.style,
        image_create_prompt=request.prompt,
        needs_animation=False,
        transition_to_next=TransitionType.NONE
    )
    
    try:
        # Agent returns dict {scene_num: path}
        result = await agent.generate_images([scene])
        path = result.get(request.scene_number)
        
        if not path:
            raise HTTPException(status_code=500, detail="Image generation failed")
            
        # Convert absolute path to relative URL for frontend
        # Assuming generated_assets is served statically
        relative_path = path.split("generated_assets/")[-1]
        url = f"/generated_assets/{relative_path}"
        
        return ImageGenerationResponse(image_path=path, url=url)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Placeholder for other endpoints (Audio, Assembly)
# They will follow a similar pattern
class VideoGenRequest(BaseModel):
    type: str  # "text" or "image"
    prompt: str
    image_url: Optional[str] = None

@router.post("/generate-video")
async def generate_video(request: VideoGenRequest):
    """
    Generate a video from text or image.
    """
    agent = VideoGenAgent()
    
    try:
        if request.type == "text":
            video_path = agent.generate_from_text(request.prompt)
        elif request.type == "image":
            if not request.image_url:
                raise HTTPException(status_code=400, detail="Image URL is required for image-to-video generation")
            # For mock, we just use the URL as a reference, in real implementation we'd download it
            video_path = agent.generate_from_image(request.image_url, request.prompt)
        else:
            raise HTTPException(status_code=400, detail="Invalid generation type")
            
        # Convert absolute path to relative URL for frontend
        relative_path = os.path.relpath(video_path, settings.GENERATED_ASSETS_DIR)
        video_url = f"/generated_assets/{relative_path}"
        
        return {"video_url": video_url, "video_path": video_path}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
