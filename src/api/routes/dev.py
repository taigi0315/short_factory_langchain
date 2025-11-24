from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.video_gen.agent import VideoGenAgent
from src.core.config import settings
import os
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings, VideoScript
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

@router.get("/retry-config")
async def get_retry_config():
    """Get image generation retry configuration for frontend."""
    return {
        "max_retries": settings.IMAGE_GENERATION_MAX_RETRIES,
        "retry_delays_seconds": settings.IMAGE_GENERATION_RETRY_DELAYS,
        "scene_delay_seconds": settings.IMAGE_GENERATION_SCENE_DELAY
    }

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
            video_path = await agent.generate_from_text(request.prompt)
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
class ScriptVideoRequest(BaseModel):
    script: dict
    image_map: dict[int, str] = {} # scene_number -> image_url/path

@router.post("/generate-video-from-script")
async def generate_video_from_script(request: ScriptVideoRequest):
    """
    Generate a full video from a script and optional images.
    """
    import structlog
    from PIL import Image as PILImage
    logger = structlog.get_logger()
    logger.info("Received request to generate video for script", title=request.script.get('title', 'Untitled'))
    
    agent = VideoGenAgent()
    
    try:
        # Parse script dict back to VideoScript model
        logger.info("Parsing script model...")
        script = VideoScript(**request.script)
        logger.info("Script parsed successfully", scene_count=len(script.scenes))
        
        # Convert image URLs back to absolute paths
        real_image_map = {}
        images_list = []
        validation_errors = []
        
        # Initialize images list with placeholders
        sorted_scenes = sorted(script.scenes, key=lambda s: s.scene_number)
        
        for scene in sorted_scenes:
            img_url = request.image_map.get(scene.scene_number)
            if img_url:
                # Remove /generated_assets/ prefix if present
                if img_url.startswith("/generated_assets/"):
                    rel_path = img_url.replace("/generated_assets/", "")
                    abs_path = os.path.join(settings.GENERATED_ASSETS_DIR, rel_path)
                    
                    # Validate image file exists and is valid
                    if not os.path.exists(abs_path):
                        error_msg = f"Scene {scene.scene_number}: Image file not found at {abs_path}"
                        logger.error(error_msg)
                        validation_errors.append(error_msg)
                        images_list.append("placeholder.jpg")
                    else:
                        # Check if it's a valid image file
                        try:
                            with PILImage.open(abs_path) as img:
                                img.verify()
                            logger.info(f"Scene {scene.scene_number}: Image validated", path=abs_path)
                            images_list.append(abs_path)
                        except Exception as img_error:
                            error_msg = f"Scene {scene.scene_number}: Invalid/corrupted image file: {str(img_error)}"
                            logger.error(error_msg, path=abs_path)
                            validation_errors.append(error_msg)
                            images_list.append("placeholder.jpg")
                else:
                    images_list.append(img_url) # Assume it's a path or placeholder
            else:
                logger.warning("No image found for scene, using placeholder", scene_number=scene.scene_number)
                images_list.append("placeholder.jpg") # Agent will handle this
        
        # If there are validation errors, return them to the user
        if validation_errors:
            error_summary = f"Image validation failed for {len(validation_errors)} scene(s):\n" + "\n".join(validation_errors)
            logger.error("Image validation failed", errors=validation_errors)
            raise HTTPException(
                status_code=400, 
                detail=error_summary
            )
        
        logger.info("Prepared images for generation", count=len(images_list), valid_images=sum(1 for img in images_list if img != "placeholder.jpg"))
        
        # Generate audio for scenes
        logger.info("Generating audio for scenes...")
        try:
            from src.agents.voice.agent import VoiceAgent
            voice_agent = VoiceAgent()
            audio_map = await voice_agent.generate_voiceovers(script.scenes)
            logger.info("Audio generation complete", audio_count=len(audio_map))
        except Exception as audio_error:
            logger.warning("Audio generation failed, continuing without audio",
                         error=str(audio_error),
                         error_type=type(audio_error).__name__)
            audio_map = {}
        
        logger.info("Starting video generation agent...")
        video_path = await agent.generate_video(
            script=script,
            images=images_list,
            audio_map=audio_map,
            style=ImageStyle.CINEMATIC # Default
        )
        logger.info("Video generation completed", video_path=video_path)
        
        # Prepare response - wrap in try-catch to ensure we return success even if path conversion has issues
        try:
            # Convert absolute path to relative URL for frontend
            relative_path = os.path.relpath(video_path, settings.GENERATED_ASSETS_DIR)
            video_url = f"/generated_assets/{relative_path}"
            
            response_data = {"video_url": video_url, "video_path": video_path}
            logger.info("Sending success response to frontend", response=response_data)
            
            return response_data
            
        except Exception as path_error:
            # If path conversion fails, still return the absolute path
            logger.warning("Path conversion failed, using absolute path", error=str(path_error))
            return {"video_url": f"/generated_assets/videos/{os.path.basename(video_path)}", "video_path": video_path}
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error("Video generation failed", exc_info=True, error_type=type(e).__name__, error_message=str(e))
        raise HTTPException(status_code=500, detail=f"Video generation failed: {str(e)}")
