from pydantic import BaseModel
from typing import List, Optional
from src.models.models import VideoScript

class ScriptGenerationRequest(BaseModel):
    story_title: str
    story_premise: str
    story_genre: str
    story_audience: str
    duration: str

class ScriptGenerationResponse(BaseModel):
    script: VideoScript
