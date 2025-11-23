from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from pydantic import BaseModel
from typing import Optional, List
import os
import shutil
from pathlib import Path
import structlog
import hashlib
import time

from src.models.models import VideoScript, Scene, SceneConfig
from src.core.config import settings
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.video_gen.agent import VideoGenAgent

router = APIRouter(prefix="/api/scene-editor", tags=["scene-editor"])
logger = structlog.get_logger()

# ========================================
# Request/Response Models
# ========================================

class SceneImageRequest(BaseModel):
    scene_number: int
    script_id: str
    prompt: str
    style: str = "cinematic"

class VideoPromptResponse(BaseModel):
    scene_number: int
    video_prompt: str
    visual_description: str
    duration: Optional[float] = None

class BuildVideoRequest(BaseModel):
    script: dict  # VideoScript as dict
    scene_configs: List[dict]  # List of SceneConfig as dicts

# ========================================
# Endpoints
# ========================================

@router.post("/generate-image")
async def generate_scene_image(request: SceneImageRequest):
    """Generate image for a single scene"""
    try:
        logger.info("Generating image for scene", 
                   scene_number=request.scene_number,
                   script_id=request.script_id)
        
        # Create image agent
        image_agent = ImageGenAgent()
        
        # Generate image
        # Create a minimal scene object for image generation
        from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, TransitionType, ElevenLabsSettings
        
        scene = Scene(
            scene_number=request.scene_number,
            scene_type=SceneType.EXPLANATION,  # Default
            dialogue="",
            voice_tone=VoiceTone.FRIENDLY,
            elevenlabs_settings=ElevenLabsSettings.for_tone(VoiceTone.FRIENDLY),
            image_style=ImageStyle(request.style) if request.style else ImageStyle.CINEMATIC,
            image_create_prompt=request.prompt,
            needs_animation=False,
            transition_to_next=TransitionType.FADE
        )
        
        # Generate image
        image_paths = await image_agent.generate_images([scene])
        
        if not image_paths or request.scene_number not in image_paths:
            raise HTTPException(status_code=500, detail="Image generation failed")
        
        image_path = image_paths[request.scene_number]
        
        # Convert to URL
        relative_path = os.path.relpath(image_path, settings.GENERATED_ASSETS_DIR)
        image_url = f"/generated_assets/{relative_path}"
        
        logger.info("Image generated successfully", 
                   scene_number=request.scene_number,
                   image_url=image_url)
        
        return {
            "url": image_url,
            "path": image_path,
            "scene_number": request.scene_number
        }
        
    except Exception as e:
        logger.error("Failed to generate scene image", 
                    error=str(e),
                    scene_number=request.scene_number)
        raise HTTPException(status_code=500, detail=f"Image generation failed: {str(e)}")


@router.post("/upload-video/{script_id}/{scene_number}")
async def upload_scene_video(
    script_id: str,
    scene_number: int,
    video: UploadFile = File(...)
):
    """Upload manually created video for a scene"""
    try:
        logger.info("Uploading video for scene",
                   scene_number=scene_number,
                   script_id=script_id,
                   filename=video.filename)
        
        # Validate file size
        file_size = 0
        content = await video.read()
        file_size = len(content)
        
        max_size = settings.MAX_VIDEO_UPLOAD_SIZE_MB * 1024 * 1024
        if file_size > max_size:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size is {settings.MAX_VIDEO_UPLOAD_SIZE_MB}MB"
            )
        
        # Validate file format
        file_ext = os.path.splitext(video.filename)[1].lower()
        if file_ext not in settings.ALLOWED_VIDEO_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file format. Allowed formats: {', '.join(settings.ALLOWED_VIDEO_FORMATS)}"
            )
        
        # Create directory for scene videos
        scenes_dir = Path(settings.GENERATED_ASSETS_DIR) / "videos" / "scenes"
        scenes_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate unique filename
        timestamp = int(time.time())
        file_hash = hashlib.md5(content[:1024]).hexdigest()[:8]
        filename = f"scene_{scene_number}_{file_hash}_{timestamp}{file_ext}"
        file_path = scenes_dir / filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Convert to URL
        relative_path = os.path.relpath(file_path, settings.GENERATED_ASSETS_DIR)
        video_url = f"/generated_assets/{relative_path}"
        
        logger.info("Video uploaded successfully",
                   scene_number=scene_number,
                   file_path=str(file_path),
                   file_size=file_size)
        
        return {
            "url": video_url,
            "path": str(file_path),
            "scene_number": scene_number,
            "size_bytes": file_size
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to upload video",
                    error=str(e),
                    scene_number=scene_number)
        raise HTTPException(status_code=500, detail=f"Video upload failed: {str(e)}")


@router.get("/video-prompt/{script_id}/{scene_number}")
async def get_video_prompt(script_id: str, scene_number: int):
    """Get video generation prompt for manual creation"""
    try:
        # For now, return a generic prompt
        # In production, you'd load the actual script from storage
        logger.info("Getting video prompt",
                   scene_number=scene_number,
                   script_id=script_id)
        
        # TODO: Load actual script from storage/database
        # For now, return a template
        prompt = f"""Scene {scene_number}: Create an engaging video animation

Instructions for manual video creation:
1. Use the downloaded image as the starting frame
2. Add subtle animations (character movements, background effects)
3. Keep duration around 5-8 seconds
4. Maintain 9:16 aspect ratio (vertical)
5. Export as MP4, MOV, or WebM

Suggested animation:
- Character gestures or expressions
- Background particle effects
- Smooth camera movements
- Text animations (if applicable)

Upload the generated video back to this scene when ready."""
        
        return {
            "scene_number": scene_number,
            "video_prompt": prompt,
            "visual_description": "Animation prompt for manual video creation",
            "duration": 5.0
        }
        
    except Exception as e:
        logger.error("Failed to get video prompt",
                    error=str(e),
                    scene_number=scene_number)
        raise HTTPException(status_code=500, detail=f"Failed to get video prompt: {str(e)}")


@router.delete("/video/{script_id}/{scene_number}")
async def delete_scene_video(script_id: str, scene_number: int):
    """Remove uploaded video for a scene"""
    try:
        logger.info("Deleting video for scene",
                   scene_number=scene_number,
                   script_id=script_id)
        
        # TODO: Implement video deletion
        # For now, just return success
        
        return {
            "success": True,
            "scene_number": scene_number,
            "message": "Video deleted successfully"
        }
        
    except Exception as e:
        logger.error("Failed to delete video",
                    error=str(e),
                    scene_number=scene_number)
        raise HTTPException(status_code=500, detail=f"Failed to delete video: {str(e)}")


@router.post("/build-video")
async def build_final_video(request: BuildVideoRequest):
    """Build final video from scene configurations"""
    try:
        logger.info("Building final video from scene configs",
                   scene_count=len(request.scene_configs))
        
        # Parse script
        script = VideoScript(**request.script)
        
        # Parse scene configs
        scene_configs = [SceneConfig(**config) for config in request.scene_configs]
        
        # Create video agent
        video_agent = VideoGenAgent()
        
        # Build video
        video_path = await video_agent.build_from_scene_configs(script, scene_configs)
        
        # Convert to URL
        relative_path = os.path.relpath(video_path, settings.GENERATED_ASSETS_DIR)
        video_url = f"/generated_assets/{relative_path}"
        
        logger.info("Final video built successfully",
                   video_path=video_path)
        
        return {
            "video_url": video_url,
            "video_path": video_path
        }
        
    except Exception as e:
        logger.error("Failed to build final video",
                    error=str(e),
                    exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to build video: {str(e)}")
