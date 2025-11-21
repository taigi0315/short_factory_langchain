from pydantic import BaseModel
from typing import List, Optional

class StoryGenerationRequest(BaseModel):
    topic: str
    mood: Optional[str] = "Neutral"
    category: Optional[str] = "General"

class StoryIdeaResponse(BaseModel):
    title: str
    premise: str
    genre: str
    target_audience: str
    estimated_duration: str
