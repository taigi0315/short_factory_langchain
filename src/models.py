# Pydantic data models for Script and Scene.
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

class ImageStyle(str, Enum):
    """Available image styles for video generation."""
    SCIENTIFIC_ILLUSTRATION = "Scientific Illustration"
    COSMIC_WATERCOLOR = "Cosmic Watercolor"
    FUTURISTIC_DIGITAL_RENDER = "Futuristic Digital Render"
    # ... add all styles from your list

class SceneModel(BaseModel):
    """Model for individual video scenes."""
    script: str = Field(..., description="Narration text for the scene")
    image_keywords: List[str] = Field(..., description="Keywords for image generation")
    scene_description: str = Field(..., description="Detailed visual description")
    image_to_video: str = Field(..., description="Animation description")
    image_style_name: ImageStyle = Field(..., description="Selected image style")

class VideoScriptModel(BaseModel):
    """Complete video script structure."""
    video_title: str = Field(..., description="Catchy video title with emoji")
    video_description: str = Field(..., description="Brief video description")
    hashtags: List[str] = Field(..., description="Relevant hashtags")
    hook: SceneModel = Field(..., description="Opening hook scene")
    scenes: List[SceneModel] = Field(..., min_items=7, description="Main content scenes")
    conclusion: SceneModel = Field(..., description="Closing scene with CTA")
    music_suggestion: str = Field(..., description="Background music recommendation")