from fastapi import APIRouter, HTTPException
from src.api.schemas.videos import VideoGenerationRequest
from src.api.schemas.scripts import ScriptGenerationResponse
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.voice.agent import VoiceAgent
from src.agents.video_assembly.agent import VideoAssemblyAgent

router = APIRouter()

@router.post("/generate", response_model=ScriptGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    try:
        script = request.script
        # Generate assets
        image_agent = ImageGenAgent()
        voice_agent = VoiceAgent()
        assembly_agent = VideoAssemblyAgent()
        image_paths = await image_agent.generate_images(script.scenes)
        audio_paths = await voice_agent.generate_voiceovers(script.scenes)
        video_path = await assembly_agent.assemble_video(script, image_paths, audio_paths)
        # Return path (relative to project root) for frontend to fetch
        return ScriptGenerationResponse(script=script, video_path=video_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
