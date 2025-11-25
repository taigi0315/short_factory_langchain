from pydantic import BaseModel, Field
from typing import List

class StoryIdea(BaseModel):
    """A specific story angle or idea derived from a broad subject."""
    title: str = Field(..., description="Catchy title for the story")
    summary: str = Field(..., description="Brief summary of the story concept")
    hook: str = Field(..., description="The 'hook' - why this is interesting/surprising")
    keywords: List[str] = Field(..., description="Keywords for search/categorization")
    category: str = Field(..., description="Category of the story (News, Real Story, Educational, Fiction)")
    mood: str = Field(..., description="Mood of the story (e.g., Exciting, Mysterious, Informative)")

class StoryList(BaseModel):
    """List of generated story ideas."""
    stories: List[StoryIdea] = Field(..., description="List of generated story ideas")
