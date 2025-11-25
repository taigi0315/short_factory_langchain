from fastapi import APIRouter
from src.api.schemas.stories import StoryGenerationRequest, StoryIdeaResponse
from src.agents.story_finder.agent import StoryFinderAgent
from src.api.error_handling import with_fallback
from src.api.mock_data import get_mock_stories
from typing import List

router = APIRouter()


@router.post("/generate", response_model=List[StoryIdeaResponse])
@with_fallback(lambda request: get_mock_stories(request))
async def generate_stories(request: StoryGenerationRequest):
    """
    Generate story ideas using LLM.
    Falls back to mock data if LLM unavailable.
    """
    # Instantiate the agent
    agent = StoryFinderAgent()
    
    # Generate stories with dynamic routing
    story_list = agent.find_stories(
        subject=request.topic,
        category=request.category,
        mood=request.mood
    )
    
    # Map internal model to API response
    return [
        StoryIdeaResponse(
            title=story.title,
            premise=story.summary,
            genre=request.category,
            target_audience="General",
            estimated_duration="30-60s"
        ) for story in story_list.stories
    ]
