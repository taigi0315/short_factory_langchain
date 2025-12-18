from fastapi import APIRouter, Depends
from src.api.schemas.scripts import ScriptGenerationRequest, ScriptGenerationResponse
from src.agents.script_writer.agent import ScriptWriterAgent
from src.agents.director.agent import DirectorAgent
from src.api.error_handling import with_fallback
from src.api.mock_data import get_mock_script
from src.core.dependencies import get_script_writer, get_director
import structlog

router = APIRouter()
logger = structlog.get_logger()


@router.post("/generate", response_model=ScriptGenerationResponse)
@with_fallback(lambda request: get_mock_script(request))
async def generate_script(
    request: ScriptGenerationRequest,
    script_agent: ScriptWriterAgent = Depends(get_script_writer),
    director: DirectorAgent = Depends(get_director)
) -> ScriptGenerationResponse:
    """
    Generate video script using LLM.
    Falls back to mock data if LLM unavailable.
    """

    full_subject = (
        f"Title: {request.story_title}\n"
        f"Premise: {request.story_premise}\n"
        f"Genre: {request.story_genre}\n"
        f"Target Audience: {request.story_audience}\n"
        f"Duration: {request.duration}"
    )


    script = await script_agent.generate_script(full_subject)

    logger.info("Script generated", title=script.title, scenes=len(script.scenes))

    # TICKET-035: Analyze script with Director Agent
    directed_script = await director.analyze_script(script)
    
    logger.info("Cinematic direction generated",
                directed_scenes=len(directed_script.directed_scenes))

    # TICKET-035: For backward compatibility with frontend, we still return the original script
    # but with Director's enhanced prompts applied to scenes
    # The full DirectedScript is used internally by ImageGen and VideoAssembly
    logger.info("Starting scene update loop", total_scenes=len(script.scenes))

    for i, directed_scene in enumerate(directed_script.directed_scenes):
        logger.info(f"Processing directed scene {i+1}/{len(directed_script.directed_scenes)}",
                   scene_number=directed_scene.original_scene.scene_number)

        scene_idx = directed_scene.original_scene.scene_number - 1
        if scene_idx < len(script.scenes):
            scene = script.scenes[scene_idx]
            direction = directed_scene.direction

            logger.info("Updating scene properties", scene_number=scene.scene_number)

            # Store Director's recommendations in scene for frontend display
            scene.recommended_effect = director.get_effect_name(direction.camera_movement)
            scene.selected_effect = scene.recommended_effect
            scene.recommended_ai_video = director.recommend_ai_video(directed_scene)
            scene.effect_reasoning = direction.director_notes

            # TICKET-035: Update scene content with Director's enhanced visual segments
            # Note: image_create_prompt is now a @property derived from content, so we don't set it directly
            if directed_scene.visual_segments:
                logger.info("Updating visual segments",
                           scene_number=scene.scene_number,
                           segment_count=len(directed_scene.visual_segments))
                scene.content = directed_scene.visual_segments


            if direction.enhanced_video_prompt:
                scene.video_prompt = direction.enhanced_video_prompt

            logger.info(f"Scene {scene.scene_number} updated successfully")

    logger.info("Scene update loop complete")

    # Verify computed fields are working
    if script.scenes:
        first_scene = script.scenes[0]
        logger.info("Verifying scene data", 
                   scene_1_content=len(first_scene.content) if first_scene.content else 0,
                   scene_1_prompt=first_scene.image_create_prompt[:50] + "..." if first_scene.image_create_prompt else "None",
                   scene_1_dialogue=first_scene.dialogue[:50] + "..." if first_scene.dialogue else "None")
        
        if first_scene.content:
            first_segment = first_scene.content[0]
            logger.info("Verifying segment type", 
                       segment_type=type(first_segment).__name__,
                       segment_data=str(first_segment))

    try:
        logger.info("Creating ScriptGenerationResponse...")
        response = ScriptGenerationResponse(script=script)
        
        logger.info("Validating response model...")
        # Explicitly validate to catch errors here instead of letting FastAPI do it silently
        ScriptGenerationResponse.model_validate(response)
        
        logger.info("Response validation successful. Returning response.")
        return response
    except Exception as e:
        logger.error("Failed to create or serialize response",
                    error=str(e),
                    error_type=type(e).__name__,
                    exc_info=True)

        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Response validation failed: {str(e)}")

