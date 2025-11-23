from fastapi import APIRouter
from src.api.schemas.scripts import ScriptGenerationRequest, ScriptGenerationResponse
from src.agents.script_writer.agent import ScriptWriterAgent
from src.agents.video_effect.agent import VideoEffectAgent
from src.api.error_handling import with_fallback
from src.api.mock_data import get_mock_script
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=ScriptGenerationResponse)
@with_fallback(lambda request: get_mock_script(request))
async def generate_script(request: ScriptGenerationRequest):
    """
    Generate video script using LLM.
    Falls back to mock data if LLM unavailable.
    """
    # Instantiate the script writer agent
    script_agent = ScriptWriterAgent()
    
    # Prepare comprehensive subject for script writer
    full_subject = (
        f"Title: {request.story_title}\n"
        f"Premise: {request.story_premise}\n"
        f"Genre: {request.story_genre}\n"
        f"Target Audience: {request.story_audience}\n"
        f"Duration: {request.duration}"
    )
    
    # Generate the script
    script = script_agent.generate_script(full_subject)
    
    logger.info("Script generated", title=script.title, scenes=len(script.scenes))
    
    # Analyze script with VideoEffectAgent
    effect_agent = VideoEffectAgent()
    recommendations = effect_agent.analyze_script(script, max_ai_videos=2)
    
    logger.info("Video effects analyzed", 
                ai_videos=sum(1 for r in recommendations if r.recommend_ai_video))
    
    # Apply recommendations to scenes
    for rec in recommendations:
        scene = script.scenes[rec.scene_number - 1]
        # Store recommendations in scene (will add these fields to model)
        scene.recommended_effect = rec.effect
        scene.recommended_ai_video = rec.recommend_ai_video
        scene.effect_reasoning = rec.reasoning
        
        # Enhance video prompt if available
        if rec.video_prompt:
            scene.video_prompt = rec.video_prompt
    
    return ScriptGenerationResponse(script=script)
