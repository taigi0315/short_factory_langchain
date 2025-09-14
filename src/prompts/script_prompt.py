"""
Script Generation Prompt Template for AI-Powered Video Creation
==============================================================

This module contains the comprehensive prompt template for generating
video scripts using LangChain with our custom Pydantic models.
"""

from langchain.prompts import PromptTemplate
from typing import List, Dict, Any


class VideoScriptPromptTemplate:
    """
    Comprehensive prompt template for video script generation.
    
    This class manages the complex prompt structure needed to generate
    complete video scripts with proper scene breakdown, image styles,
    and detailed visual descriptions.
    """
    
    # Available image styles with detailed descriptions
    IMAGE_STYLES = {
        "Scientific Illustration": {
            "description": "Precise, technical, clean line art with scientific accuracy",
            "specs": "detailed cross-sections, blueprint-like precision, technical drawing style",
            "palette": "muted color palette with blues, grays, and white",
            "lighting": "even, diffused lighting with minimal shadows",
            "texture": "clean line art, minimal texture, precise edges"
        },
        "Cosmic Watercolor": {
            "description": "Dreamy watercolor technique with astronomical elements",
            "specs": "soft blended colors, ethereal space-themed illustration", 
            "palette": "deep purples, blues, and cosmic colors with gentle gradients",
            "lighting": "soft, ethereal lighting with glowing effects",
            "texture": "translucent watercolor textures, flowing organic shapes"
        },
        "Futuristic Digital Render": {
            "description": "Sleek, high-resolution 3D render with technological aesthetic",
            "specs": "metallic and glass textures, minimalist design, sharp edges",
            "palette": "cyberpunk-inspired with electric blues and neon accents", 
            "lighting": "dramatic lighting with sharp contrasts and reflections",
            "texture": "glossy metallic surfaces, transparent glass, smooth gradients"
        },
        "Natural History Engraving": {
            "description": "Vintage scientific engraving style with intricate detail",
            "specs": "black and white detailed illustration, etched texture",
            "palette": "monochromatic with sepia tones and aged paper effects",
            "lighting": "classical engraving lighting with fine line shading", 
            "texture": "etched line texture, cross-hatching, vintage paper feel"
        },
        "Minimalist Infographic": {
            "description": "Clean, modern design with geometric shapes",
            "specs": "flat color palette, iconographic representation, data visualization style",
            "palette": "bright, clean colors with strong contrast",
            "lighting": "flat lighting with no shadows, clean presentation",
            "texture": "smooth flat surfaces, geometric precision, no texture"
        },
        "Molecular Abstract": {
            "description": "Microscopic view with molecular and atomic structures",
            "specs": "vibrant color palette, organic geometric shapes, translucent overlapping elements",
            "palette": "bright scientific colors with neon highlights",
            "lighting": "inner glow effects, translucent lighting",
            "texture": "molecular textures, atomic structures, scientific complexity"
        },
        "Retro Scientific Poster": {
            "description": "Vintage 1950s and 1960s scientific poster aesthetic",
            "specs": "bold typography, mid-century modern design, stylized graphic representations",
            "palette": "retro color scheme with earth tones and pastels", 
            "lighting": "vintage poster lighting with soft shadows",
            "texture": "vintage paper texture, retro graphic style"
        },
        "Bioluminescent Fantasy": {
            "description": "Glowing, ethereal scientific imagery with bio-inspired designs",
            "specs": "neon-like colors, soft light effects, dream-like interpretation",
            "palette": "bioluminescent blues, greens, and purples",
            "lighting": "inner glow, luminescent effects, magical lighting",
            "texture": "luminescent textures, organic glow, ethereal surfaces"
        }
    }

    @classmethod
    def get_base_template(cls) -> str:
        """
        Get the base prompt template for video script generation.
        
        Returns:
            Formatted prompt template string
        """
        return """
You are an expert educational video script writer specializing in creating engaging, scientifically accurate short-form content. Your task is to create a complete video script about the given subject that will be used to generate images and video content.

SUBJECT: {subject}

VIDEO REQUIREMENTS:
- Target duration: 40-60 seconds
- Target audience: Science enthusiasts, curious learners, educators (ages 10-35)
- Must have EXACTLY 9-12 total scenes (including hook and conclusion)
- Each scene represents 3-8 seconds of video content
- Content must be scientifically accurate yet accessible

CONTENT GUIDELINES:
- Start with a surprising hook that grabs attention immediately
- Present information in a clear, engaging narrative flow
- Use simple language to explain complex concepts
- Include memorable analogies and visual metaphors
- Build excitement and curiosity throughout
- End with a strong call-to-action encouraging engagement

VISUAL REQUIREMENTS:
- Each scene needs detailed visual descriptions for AI image generation
- Must specify: main subject, positioning, lighting, colors, atmosphere
- Scene descriptions must include foreground, midground, and background elements
- Choose appropriate image styles that enhance the educational content
- Ensure visual continuity and logical progression between scenes

AVAILABLE IMAGE STYLES:
{available_styles}

SCENE STRUCTURE REQUIREMENTS:
1. HOOK (3-4 seconds): Attention-grabbing opening with surprising statement/question
2. MAIN SCENES (7-9 scenes, 4-6 seconds each): Core educational content
3. CONCLUSION (6-8 seconds): Summary with clear call-to-action

MANDATORY OUTPUT FORMAT:
You must respond with a valid JSON object that matches this exact structure:

{{
    "video_title": "Catchy title with emoji that creates curiosity and excitement",
    "video_description": "Brief description highlighting fascinating aspects with emoji",
    "hashtags": ["#hashtag1", "#hashtag2", "#hashtag3", "#hashtag4", "#hashtag5"],
    "hook": {{
        "script": "Attention-grabbing narration with surprising fact or question (20-30 words)",
        "main": "Primary visual subject/character/object for this scene",
        "scene_description": "Extremely detailed visual description including: main subject appearance and positioning, lighting setup and direction, color palette and atmosphere, background elements and depth, spatial arrangement of all elements, camera angle and perspective. Minimum 60 words.",
        "image_to_video": "Specific description of how the static image will be animated (camera movement, object animation, effects)",
        "image_style": {{
            "name": "Choose from available styles",
            "description": "Copy exact description from available styles",
            "technical_specs": "Copy exact specs from available styles", 
            "color_palette": "Copy exact palette from available styles",
            "lighting_style": "Copy exact lighting from available styles",
            "texture_quality": "Copy exact texture from available styles"
        }},
        "duration_seconds": 3.5,
        "visual_emphasis": ["key_element_1", "key_element_2", "key_element_3"]
    }},
    "scenes": [
        {{
            "script": "Educational narration building on previous scene (25-45 words)",
            "main": "Primary visual subject for this scene",
            "scene_description": "Detailed visual description with all required elements (minimum 60 words)",
            "image_to_video": "Animation description for this scene",
            "image_style": {{
                "name": "Style name from available list",
                "description": "Exact description from styles",
                "technical_specs": "Exact specs",
                "color_palette": "Exact palette", 
                "lighting_style": "Exact lighting",
                "texture_quality": "Exact texture"
            }},
            "duration_seconds": 5.0,
            "visual_emphasis": ["element_1", "element_2"]
        }}
        // ... repeat for 7-9 more scenes
    ],
    "conclusion": {{
        "script": "Inspiring conclusion with clear call-to-action: 'Now that you know this, who else do you think should? Tag a friend in the comments who you think would find this fascinating!' (40-60 words)",
        "main": "Final visual that reinforces the key message",
        "scene_description": "Compelling final scene description (minimum 60 words)",
        "image_to_video": "Memorable closing animation",
        "image_style": {{
            "name": "Impactful style for conclusion",
            "description": "Exact description",
            "technical_specs": "Exact specs",
            "color_palette": "Exact palette",
            "lighting_style": "Exact lighting", 
            "texture_quality": "Exact texture"
        }},
        "duration_seconds": 7.0,
        "visual_emphasis": ["final_message", "call_to_action"]
    }},
    "music_suggestion": "Specific music recommendation that fits the content mood",
    "total_estimated_duration": 52.5,
    "target_audience": "Specific audience description",
    "learning_objectives": ["objective_1", "objective_2", "objective_3"]
}}

CRITICAL REQUIREMENTS:
- Total video duration must be between 40-60 seconds
- Must have exactly 9-12 scenes total (hook + main scenes + conclusion)
- Each scene must advance the narrative or explain a new concept
- Image styles must be chosen strategically to enhance understanding
- Scene descriptions must be detailed enough for AI image generation
- All JSON syntax must be perfect and valid
- Every image_style object must contain all 6 required fields with exact content from available styles

CONTENT CREATION STRATEGY:
1. Analyze the subject for the most fascinating/surprising aspects
2. Create a logical narrative flow from hook to conclusion  
3. Choose diverse but coherent image styles that support the content
4. Write scene descriptions that create vivually stunning, educational images
5. Ensure each scene builds excitement and understanding
6. End with inspiration and clear engagement request

Remember: This script will be used to automatically generate images and video content, so precision and detail in visual descriptions is crucial for success.

Generate a complete video script for: {subject}
"""

    @classmethod
    def get_style_descriptions(cls) -> str:
        """
        Generate formatted string of available image styles.
        
        Returns:
            Formatted string listing all available styles with details
        """
        style_text = ""
        for style_name, details in cls.IMAGE_STYLES.items():
            style_text += f"\n'{style_name}':\n"
            style_text += f"  Description: {details['description']}\n"
            style_text += f"  Technical Specs: {details['specs']}\n" 
            style_text += f"  Color Palette: {details['palette']}\n"
            style_text += f"  Lighting: {details['lighting']}\n"
            style_text += f"  Texture: {details['texture']}\n"
        
        return style_text

    @classmethod  
    def create_prompt_template(cls) -> PromptTemplate:
        """
        Create the complete LangChain PromptTemplate.
        
        Returns:
            PromptTemplate configured for video script generation
        """
        template = cls.get_base_template()
        
        return PromptTemplate(
            input_variables=["subject"],
            template=template,
            partial_variables={
                "available_styles": cls.get_style_descriptions()
            },
            template_format="f-string"
        )

    @classmethod
    def create_enhanced_prompt(cls, 
                             subject: str, 
                             additional_context: str = "",
                             target_duration: tuple = (40, 60),
                             min_scenes: int = 9,
                             max_scenes: int = 12) -> str:
        """
        Create enhanced prompt with additional customization.
        
        Args:
            subject: The main topic for the video
            additional_context: Extra context or requirements
            target_duration: Min and max duration in seconds
            min_scenes: Minimum number of scenes
            max_scenes: Maximum number of scenes
            
        Returns:
            Fully formatted prompt string
        """
        base_template = cls.get_base_template()
        
        # Add customization
        enhanced_template = base_template.replace(
            "Target duration: 40-60 seconds",
            f"Target duration: {target_duration[0]}-{target_duration[1]} seconds"
        ).replace(
            "EXACTLY 9-12 total scenes",
            f"EXACTLY {min_scenes}-{max_scenes} total scenes"
        )
        
        if additional_context:
            enhanced_template += f"\n\nADDITIONAL CONTEXT:\n{additional_context}"
        
        return enhanced_template.format(
            subject=subject,
            available_styles=cls.get_style_descriptions()
        )


# Example usage and testing functions
def test_prompt_generation():
    """Test the prompt template generation."""
    
    # Create the prompt template
    prompt_template = VideoScriptPromptTemplate.create_prompt_template()
    
    # Test subjects
    test_subjects = [
        "How octopuses can change color instantly",
        "Why time moves slower near black holes", 
        "How your brain creates dreams",
        "The secret life of quantum particles",
        "Why some animals can regenerate limbs"
    ]
    
    print("🎬 Testing Video Script Prompt Template\n")
    
    for subject in test_subjects:
        print(f"📝 Subject: {subject}")
        formatted_prompt = prompt_template.format(subject=subject)
        print(f"   Prompt length: {len(formatted_prompt)} characters")
        print(f"   Contains styles: {'Scientific Illustration' in formatted_prompt}")
        print(f"   Contains JSON format: {'video_title' in formatted_prompt}")
        print()
    
    print("✅ All prompt tests completed!")


def create_custom_prompt_for_subject(subject: str, **kwargs) -> str:
    """
    Create a custom prompt for a specific subject.
    
    Args:
        subject: The video topic
        **kwargs: Additional customization options
        
    Returns:
        Complete formatted prompt string
    """
    return VideoScriptPromptTemplate.create_enhanced_prompt(
        subject=subject,
        **kwargs
    )


# Production-ready prompt template instance
VIDEO_SCRIPT_PROMPT = VideoScriptPromptTemplate.create_prompt_template()

# Example of how to use with LangChain
"""
from langchain.llms import OpenAI
from langchain.chains import LLMChain

# Initialize LLM and chain
llm = OpenAI(temperature=0.7)
script_generation_chain = LLMChain(
    llm=llm,
    prompt=VIDEO_SCRIPT_PROMPT,
    verbose=True
)

# Generate script
result = script_generation_chain.run(subject="How photosynthesis powers all life on Earth")
"""