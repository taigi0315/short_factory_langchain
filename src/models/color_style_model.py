from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class ImageStyleModel(BaseModel):
    """
    Model representing an image style with detailed characteristics.
    
    Attributes:
        name: The display name of the image style
        description: Detailed description of the visual characteristics
        technical_specs: Technical rendering specifications
        color_palette: Suggested color scheme
        lighting_style: Lighting characteristics
        texture_quality: Surface texture descriptions
    """
    
    name: str = Field(
        ..., 
        description="Display name of the image style",
        example="Scientific Illustration"
    )
    
    description: str = Field(
        ..., 
        description="Detailed description of visual characteristics",
        example="Precise, technical, clean line art with scientific accuracy"
    )
    
    technical_specs: str = Field(
        ..., 
        description="Technical rendering specifications",
        example="detailed cross-sections, blueprint-like precision, technical drawing style"
    )
    
    color_palette: str = Field(
        ..., 
        description="Color scheme characteristics",
        example="muted color palette with blues and grays"
    )
    
    lighting_style: str = Field(
        ..., 
        description="Lighting and atmosphere characteristics",
        example="even, diffused lighting with minimal shadows"
    )
    
    texture_quality: str = Field(
        ..., 
        description="Surface texture and material descriptions",
        example="clean line art, minimal texture, precise edges"
    )

    @field_validator('name')
    def validate_name(cls, v):
        """Validate image style name is not empty and properly formatted."""
        if not v or not v.strip():
            raise ValueError('Image style name cannot be empty')
        return v.strip().title()

    @field_validator('description')
    def validate_description(cls, v):
        """Validate description has sufficient detail and normalize formatting."""
        v = v.strip().capitalize()
        if len(v) < 20:
            raise ValueError('Description must be at least 20 characters long')
        return v


    def get_full_description(self) -> str:
        """
        Get complete style description for image generation.
        
        Returns:
            Combined description with all style characteristics
        """
        return f"{self.description}, {self.technical_specs}, {self.color_palette}, {self.lighting_style}, {self.texture_quality}"

