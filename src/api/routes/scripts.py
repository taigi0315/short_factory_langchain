from fastapi import APIRouter
from src.api.schemas.scripts import ScriptGenerationRequest, ScriptGenerationResponse
from src.agents.script_writer.agent import ScriptWriterAgent
from src.api.error_handling import with_fallback
from src.api.mock_data import get_mock_script

router = APIRouter()


@router.post("/generate", response_model=ScriptGenerationResponse)
@with_fallback(lambda request: get_mock_script(request))
async def generate_script(request: ScriptGenerationRequest):
    """
    Generate video script using LLM.
    Falls back to mock data if LLM unavailable.
    """
    # Instantiate the agent
    agent = ScriptWriterAgent()
    
    # Prepare comprehensive subject for script writer
    full_subject = (
        f"Title: {request.story_title}\n"
        f"Premise: {request.story_premise}\n"
        f"Genre: {request.story_genre}\n"
        f"Target Audience: {request.story_audience}\n"
        f"Duration: {request.duration}"
    )
    
    # Generate the script
    script = agent.generate_script(full_subject)
    
    return ScriptGenerationResponse(script=script)
