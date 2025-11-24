"""
Director Agent Data Models

Defines data structures for cinematic direction, shot lists, and directed scripts.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from src.models.models import Scene, VideoScript
from src.agents.director.cinematic_language import (
    ShotType, CameraMovement, CameraAngle, LightingMood, CompositionRule
)


class CinematicDirection(BaseModel):
    """Cinematic direction for a single scene"""
    
    # Shot composition
    shot_type: ShotType = Field(description="Type of camera shot")
    camera_movement: CameraMovement = Field(description="Camera movement type")
    camera_angle: CameraAngle = Field(description="Camera angle relative to subject")
    lighting_mood: LightingMood = Field(description="Lighting style and mood")
    composition: CompositionRule = Field(description="Composition and framing rule")
    
    # Narrative purpose
    emotional_purpose: str = Field(description="What emotion this shot should evoke")
    narrative_function: str = Field(description="How this shot serves the story")
    
    # Visual continuity
    connection_from_previous: Optional[str] = Field(
        default=None,
        description="How this shot connects visually to the previous scene"
    )
    connection_to_next: Optional[str] = Field(
        default=None,
        description="How this shot sets up the next scene"
    )
    
    # Enhanced prompts
    enhanced_image_prompt: str = Field(
        description="Detailed image generation prompt with cinematic direction"
    )
    enhanced_video_prompt: Optional[str] = Field(
        default=None,
        description="Detailed video generation prompt with camera work and purpose"
    )
    
    # Director's notes
    director_notes: str = Field(
        description="Director's reasoning for these choices"
    )


class DirectedScene(BaseModel):
    """A scene with both script content and cinematic direction"""
    
    # Original scene data
    original_scene: Scene
    
    # Cinematic direction
    direction: CinematicDirection
    
    # Story beat
    story_beat: str = Field(
        description="Narrative beat this scene represents (e.g., 'Hook - Mystery Introduction')"
    )


class DirectedScript(BaseModel):
    """A complete script with cinematic direction for all scenes"""
    
    # Original script
    original_script: VideoScript
    
    # Directed scenes
    directed_scenes: List[DirectedScene]
    
    # Overall direction
    visual_theme: str = Field(
        description="Overall visual theme and style for the video"
    )
    emotional_arc: str = Field(
        description="Description of the emotional journey through the video"
    )
    pacing_notes: str = Field(
        description="Notes on pacing and rhythm"
    )
    
    # Director's vision
    director_vision: str = Field(
        description="Director's overall vision and approach for this video"
    )


class StoryBeat(BaseModel):
    """Represents a narrative beat in the story"""
    
    beat_name: str = Field(description="Name of the story beat")
    scene_numbers: List[int] = Field(description="Scenes that belong to this beat")
    purpose: str = Field(description="Purpose of this beat in the narrative")
    emotional_tone: str = Field(description="Emotional tone of this beat")


class EmotionalArc(BaseModel):
    """Maps the emotional journey through the video"""
    
    beats: List[StoryBeat]
    overall_arc: str = Field(description="Description of the complete emotional journey")
    peak_moment: int = Field(description="Scene number of the emotional peak")
