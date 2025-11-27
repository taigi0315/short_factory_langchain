from fastapi import APIRouter, HTTPException
from src.api.schemas.videos import VideoGenerationRequest
from src.api.schemas.scripts import ScriptGenerationResponse
from src.agents.director.agent import DirectorAgent
from src.agents.image_gen.agent import ImageGenAgent
from src.agents.voice.agent import VoiceAgent
from src.agents.video_assembly.agent import VideoAssemblyAgent
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=ScriptGenerationResponse)
async def generate_video(request: VideoGenerationRequest):
    """
    Generate video from script using the new DirectedScript architecture (TICKET-035).
    
    Flow:
    1. Script Writer generates script (already done, passed in request)
    2. Director Agent analyzes script and creates DirectedScript
    3. Image Gen uses Director's enhanced visual segments
    4. Voice Gen uses original script dialogue
    5. Video Assembly uses Director's camera movements for effects
    """
    try:
        script = request.script
        

        logger.info("Analyzing script with Director Agent", title=script.title)
        director = DirectorAgent()
        directed_script = await director.analyze_script(script)
        logger.info("Director analysis complete", directed_scenes=len(directed_script.directed_scenes))
        

        image_agent = ImageGenAgent()
        voice_agent = VoiceAgent()
        assembly_agent = VideoAssemblyAgent()
        

        logger.info("Generating images from directed script")
        image_paths = await image_agent.generate_images_from_directed_script(directed_script)
        
        # Voice generation still uses original script (dialogue doesn't need direction)
        logger.info("Generating voiceovers")
        audio_paths = await voice_agent.generate_voiceovers(script.scenes)
        

        logger.info("Assembling video with Director's cinematic direction")
        video_path = await assembly_agent.assemble_video_from_directed_script(
            directed_script, image_paths, audio_paths
        )
        
        logger.info("Video generation complete", video_path=video_path)
        
        # Return path (relative to project root) for frontend to fetch
        return ScriptGenerationResponse(script=script, video_path=video_path)
    except Exception as e:
        logger.error("Video generation failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
