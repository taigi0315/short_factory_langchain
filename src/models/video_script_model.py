from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum

from src.models.scene_model import SceneModel

class VideoScriptModel(BaseModel):
    """
    Complete video script structure with metadata and all scenes.
    
    Attributes:
        video_title: Catchy video title with emoji
        video_description: Brief description highlighting interesting aspects
        hashtags: Relevant hashtags for social media
        hook: Opening hook scene to grab attention
        scenes: Main content scenes (minimum 7 required)
        conclusion: Closing scene with call-to-action
        music_suggestion: Background music recommendation
        total_estimated_duration: Calculated total video duration
        target_audience: Specific target audience description
        learning_objectives: What viewers should learn/understand
    """
    
    video_title: str = Field(
        ..., 
        description="Catchy and intriguing video title with emoji included",
        min_length=10,
        max_length=100
    )
    
    video_description: str = Field(
        ..., 
        description="Brief description highlighting fun and interesting aspects with emoji",
        min_length=20,
        max_length=300
    )
    
    hashtags: List[str] = Field(
        ..., 
        description="Relevant hashtags for social media discovery",
        min_items=3,
        max_items=10
    )
    
    hook: SceneModel = Field(
        ..., 
        description="Opening hook scene designed to grab attention immediately (4-8 seconds)"
    )
    
    scenes: List[SceneModel] = Field(
        ..., 
        description="Main content scenes explaining the concept",
        min_items=7,
        max_items=30
    )
    
    conclusion: SceneModel = Field(
        ..., 
        description="Closing scene with clear call-to-action encouraging engagement"
    )
    
    music_suggestion: str = Field(
        ..., 
        description="Background music recommendation that fits the mood",
        example="upbeat, curious, and engaging electronic music"
    )
    
    total_estimated_duration: Optional[float] = Field(
        default=None,
        description="Calculated total video duration in seconds",
        ge=30.0,
        le=600.0
    )
    
    target_audience: str = Field(
        default="Science enthusiasts, curious learners, educators aged 10-35",
        description="Specific target audience description"
    )
    
    learning_objectives: List[str] = Field(
        default_factory=list,
        description="What viewers should learn or understand from this video",
        max_items=5
    )

    from pydantic import field_validator

    @field_validator('video_title')
    def validate_title_engagement(cls, v):
        """Validate title has engagement elements."""
        if not any(char in v for char in '!?😀🎉🔥💡🌟'):
            # Suggest but don't enforce emoji usage
            pass
        return v.strip()

    @field_validator('hashtags')
    def validate_hashtags_format(cls, v):
        """Validate hashtag format and content."""
        validated_tags = []
        for tag in v:
            # Remove # if present and validate
            clean_tag = tag.strip().lstrip('#').lower()
            if not clean_tag:
                continue
            if ' ' in clean_tag:
                raise ValueError(f'Hashtag "{tag}" cannot contain spaces')
            if len(clean_tag) > 30:
                raise ValueError(f'Hashtag "{tag}" is too long')
            validated_tags.append(f"#{clean_tag}")
        
        return validated_tags

    @field_validator('scenes')
    def validate_scene_flow(cls, v):
        """Validate logical flow between scenes."""
        if len(v) < 7:
            raise ValueError('Must have at least 7 main content scenes')
        
        # Check for reasonable scene length distribution
        if len(v) > 12:
            raise ValueError('Too many scenes may make video too long or rushed')
        
        return v

    def calculate_total_duration(self) -> float:
        """
        Calculate estimated total video duration.
        
        Returns:
            Total estimated duration in seconds
        """
        total = 0.0
        
        # Hook scene: 2-4 seconds
        total += self.hook.duration_seconds or 3.0
        
        # Main scenes: estimate based on script length
        for scene in self.scenes:
            if scene.duration_seconds:
                total += scene.duration_seconds
            else:
                # Estimate 0.15 seconds per character (average reading speed)
                estimated = len(scene.script) * 0.15
                total += max(3.0, min(8.0, estimated))  # Between 3-8 seconds
        
        # Conclusion scene
        total += self.conclusion.duration_seconds or 5.0
        
        self.total_estimated_duration = total
        return total

    def get_all_scenes(self) -> List[SceneModel]:
        """
        Get all scenes in order (hook, main scenes, conclusion).
        
        Returns:
            List of all scenes in video order
        """
        return [self.hook] + self.scenes + [self.conclusion]

    def get_style_distribution(self) -> Dict[str, int]:
        """
        Analyze distribution of image styles across scenes.
        
        Returns:
            Dictionary with style names and their usage count
        """
        style_count = {}
        for scene in self.get_all_scenes():
            style_name = scene.image_style.name
            style_count[style_name] = style_count.get(style_name, 0) + 1
        
        return style_count

    def validate_duration_target(self, min_duration: float = 40.0, max_duration: float = 60.0) -> bool:
        """
        Validate if video duration meets target range.
        
        Args:
            min_duration: Minimum acceptable duration in seconds
            max_duration: Maximum acceptable duration in seconds
            
        Returns:
            True if duration is within target range
        """
        total_duration = self.calculate_total_duration()
        return min_duration <= total_duration <= max_duration