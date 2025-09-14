from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum

from src.models.color_style_model import ImageStyleModel


class SceneModel(BaseModel):
    """
    Model for individual video scenes with detailed visual specifications.
    
    Attributes:
        script: Narration text for the scene
        main: Main character, object, or focal point of the scene
        scene_description: Detailed visual description for image generation
        image_to_video: Animation/movement description for video creation
        image_style: Image style model with complete specifications
        duration_seconds: Expected duration of this scene in seconds
        visual_emphasis: Key visual elements to emphasize
    """
    
    script: str = Field(
        ..., 
        description="Narration text for the scene",
        min_length=10,
        max_length=500
    )
    
    main: str = Field(
        ..., 
        description="Main character, object, or focal point of the scene",
        example="DNA double helix structure"
    )
    
    scene_description: str = Field(
        ..., 
        description="Extremely detailed visual description for AI image generation including positioning, lighting, colors, atmosphere, and spatial arrangement",
        min_length=50
    )
    
    image_to_video: str = Field(
        ..., 
        description="Description of how the static image should be animated or transformed into video",
        example="Camera slowly zooms into the DNA structure while it rotates"
    )
    
    image_style: ImageStyleModel = Field(
        ..., 
        description="Complete image style specification with all visual characteristics"
    )
    
    duration_seconds: Optional[float] = Field(
        default=None,
        description="Expected duration of this scene in seconds",
        ge=1.0,
        le=15.0
    )
    
    visual_emphasis: List[str] = Field(
        default_factory=list,
        description="Key visual elements to emphasize in the scene",
        example=["molecular bonds", "color-coded atoms", "3D structure"]
    )

    @field_validator('script')
    def validate_script_content(cls, v):
        """
        Validate script content for quality and length.

        Note:
            If engagement indicators are missing, only a warning is triggered (not an error).
        """
        if not v or not v.strip():
            raise ValueError('Script cannot be empty')
        
        # Check for basic engagement elements
        engagement_indicators = ['?', '!', 'imagine', 'think', 'see', 'look', 'what if']
        if not any(indicator in v.lower() for indicator in engagement_indicators):
            # This is a warning, not an error - script can still be valid
            pass
        
        return v.strip()

    @field_validator('main')
    def validate_main_subject(cls, v):
        """Validate main subject is descriptive enough."""
        if len(v.split()) < 2:
            raise ValueError('Main subject should be at least 2 words for clarity')
        return v.strip()

    @field_validator('scene_description')
    def validate_scene_description_detail(cls, v):
        """Validate scene description contains essential visual elements."""
        required_elements = [
            'lighting', 'color', 'position', 'background'
        ]
        
        v_lower = v.lower()
        missing_elements = [elem for elem in required_elements 
                          if elem not in v_lower and 
                          elem.replace('ing', '') not in v_lower]
        
        if len(missing_elements) > 2:
            raise ValueError(
                f'Scene description should include more visual details. '
                f'Consider adding: {", ".join(missing_elements)}'
            )
        
        return v

    @field_validator('visual_emphasis')
    def validate_visual_emphasis(cls, v):
        """Validate visual emphasis list."""
        if v and len(v) > 5:
            raise ValueError('Too many visual emphasis points - keep to 5 or fewer for clarity')
        return v

    def get_image_generation_prompt(self) -> str:
        """
        Generate complete prompt for AI image generation.
        
        Returns:
            Formatted prompt combining all visual elements
        """
        emphasis_text = f" Emphasize: {', '.join(self.visual_emphasis)}" if self.visual_emphasis else ""
        
        return (
            f"Main subject: {self.main}. "
            f"Scene: {self.scene_description}. "
            f"Style: {self.image_style.get_full_description()}. "
            f"Animation will be: {self.image_to_video}.{emphasis_text}"
        )

