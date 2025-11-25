from fastapi import APIRouter
from src.api.schemas.scripts import ScriptGenerationRequest, ScriptGenerationResponse
from src.agents.script_writer.agent import ScriptWriterAgent
from src.agents.director import DirectorAgent
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
    
    # TICKET-035: Analyze script with Director Agent
    director = DirectorAgent()
    directed_script = await director.analyze_script(script)
    
    logger.info("Cinematic direction generated", 
                directed_scenes=len(directed_script.directed_scenes))
    
    # TICKET-035: For backward compatibility with frontend, we still return the original script
    # but with Director's enhanced prompts applied to scenes
    # The full DirectedScript is used internally by ImageGen and VideoAssembly
    for directed_scene in directed_script.directed_scenes:
        scene_idx = directed_scene.original_scene.scene_number - 1
        if scene_idx < len(script.scenes):
            scene = script.scenes[scene_idx]
            direction = directed_scene.direction
            
            # Store Director's recommendations in scene for frontend display
            scene.recommended_effect = director.get_effect_name(direction.camera_movement)
            scene.selected_effect = scene.recommended_effect
            scene.recommended_ai_video = director.recommend_ai_video(directed_scene)
            scene.effect_reasoning = direction.director_notes
            
            # Use Director's enhanced prompts (for display/debugging)
            scene.image_create_prompt = direction.enhanced_image_prompt
            if direction.enhanced_video_prompt:
                scene.video_prompt = direction.enhanced_video_prompt
            
            # TICKET-035: Update scene content with Director's enhanced visual segments
            if directed_scene.visual_segments:
                scene.content = directed_scene.visual_segments
    
    return ScriptGenerationResponse(script=script)

