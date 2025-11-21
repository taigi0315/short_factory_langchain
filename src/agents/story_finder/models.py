from pydantic import BaseModel, Field
from typing import List

class StoryIdea(BaseModel):
    """A specific story angle or idea derived from a broad subject."""
    title: str = Field(..., description="Catchy title for the story")
    summary: str = Field(..., description="Brief summary of the story (2-3 sentences)")
    hook: str = Field(..., description="The interesting fact or angle that makes this story unique")
    keywords: List[str] = Field(..., description="Keywords related to this story")

class StoryList(BaseModel):
    """List of generated story ideas."""
    stories: List[StoryIdea] = Field(..., description="List of story ideas")
