from pydantic import BaseModel
from src.models.models import VideoScript

class VideoGenerationRequest(BaseModel):
    script: VideoScript
