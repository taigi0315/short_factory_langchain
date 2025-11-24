from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class SceneType(str, Enum):
    EXPLANATION = "explanation"  # Character explaining concepts
    VISUAL_DEMO = "visual_demo"  # Visual demonstration/example scene
    COMPARISON = "comparison"    # Comparison explanation scene
    STORY_TELLING = "story_telling"  # Story-telling scene
    HOOK = "hook"  # Opening hook scene
    CONCLUSION = "conclusion"  # Closing/summary scene

class ImageStyle(str, Enum):
    # Basic styles
    SINGLE_CHARACTER = "single_character"
    CHARACTER_WITH_BACKGROUND = "character_with_background"
    
    # Educational styles
    INFOGRAPHIC = "infographic"
    DIAGRAM_EXPLANATION = "diagram_explanation"
    BEFORE_AFTER_COMPARISON = "before_after_comparison"
    STEP_BY_STEP_VISUAL = "step_by_step_visual"
    
    # Comic/Story styles
    FOUR_CUT_CARTOON = "four_cut_cartoon"
    COMIC_PANEL = "comic_panel"
    SPEECH_BUBBLE = "speech_bubble"
    
    # Cinematic styles
    CINEMATIC = "cinematic"
    CLOSE_UP_REACTION = "close_up_reaction"
    WIDE_ESTABLISHING_SHOT = "wide_establishing_shot"
    VISUAL_SURPRISE = "visual_surprise"
    
    # Special effects
    SPLIT_SCREEN = "split_screen"
    OVERLAY_GRAPHICS = "overlay_graphics"
    CUTAWAY_ILLUSTRATION = "cutaway_illustration"

class VoiceTone(str, Enum):
    # Basic emotions
    EXCITED = "excited"
    CURIOUS = "curious"
    SERIOUS = "serious"
    FRIENDLY = "friendly"
    
    # Additional emotions
    SAD = "sad"
    MYSTERIOUS = "mysterious"
    SURPRISED = "surprised"
    CONFIDENT = "confident"
    WORRIED = "worried"
    PLAYFUL = "playful"
    DRAMATIC = "dramatic"
    CALM = "calm"
    ENTHUSIASTIC = "enthusiastic"
    SARCASTIC = "sarcastic"

class TransitionType(str, Enum):
    FADE = "fade"
    SLIDE_LEFT = "slide_left"
    SLIDE_RIGHT = "slide_right"
    ZOOM_IN = "zoom_in"
    ZOOM_OUT = "zoom_out"
    DISSOLVE = "dissolve"
    WIPE = "wipe"
    PUSH = "push"
    SPIN = "spin"
    FLIP = "flip"
    NONE = "none"  # Direct connection without transition

class HookTechnique(str, Enum):
    SHOCKING_FACT = "shocking_fact"  # "The water you drink daily contains dinosaur urine"
    INTRIGUING_QUESTION = "intriguing_question"  # "Why is the ocean salty but rain is not?"
    VISUAL_SURPRISE = "visual_surprise"  # Unexpected visual element
    CONTRADICTION = "contradiction"  # "Truth that contradicts common sense"
    MYSTERY_SETUP = "mystery_setup"  # "There's a secret that nobody knows..."

class ElevenLabsSettings(BaseModel):
    stability: float = Field(ge=0.0, le=1.0, description="Consistency vs emotional expression")
    similarity_boost: float = Field(ge=0.0, le=1.0, description="Closeness to reference voice")
    style: float = Field(ge=0.0, le=1.0, description="Expressiveness (exaggeration)")
    speed: float = Field(ge=0.5, le=2.0, description="Speech delivery rate")
    loudness: float = Field(ge=-1.0, le=1.0, description="Audio output volume")
    
    @classmethod
    def for_tone(cls, tone: VoiceTone) -> 'ElevenLabsSettings':
        """Return recommended settings for each voice tone"""
        settings_map = {
            # High Energy / Excitement
            VoiceTone.EXCITED: cls(stability=0.3, similarity_boost=0.85, style=0.85, speed=1.25, loudness=0.15),
            VoiceTone.ENTHUSIASTIC: cls(stability=0.35, similarity_boost=0.8, style=0.8, speed=1.2, loudness=0.1),
            VoiceTone.DRAMATIC: cls(stability=0.4, similarity_boost=0.75, style=0.9, speed=1.0, loudness=0.2),
            VoiceTone.SURPRISED: cls(stability=0.3, similarity_boost=0.7, style=0.75, speed=1.3, loudness=0.15),
            
            # Emotional / Soft
            VoiceTone.SAD: cls(stability=0.7, similarity_boost=0.7, style=0.6, speed=0.9, loudness=-0.2),
            VoiceTone.WORRIED: cls(stability=0.5, similarity_boost=0.75, style=0.65, speed=1.0, loudness=-0.1),
            
            # Neutral / Professional (lower style for clarity)
            VoiceTone.CALM: cls(stability=0.65, similarity_boost=0.75, style=0.4, speed=1.1, loudness=0.0),
            VoiceTone.SERIOUS: cls(stability=0.7, similarity_boost=0.8, style=0.35, speed=1.05, loudness=0.0),
            VoiceTone.CONFIDENT: cls(stability=0.55, similarity_boost=0.85, style=0.7, speed=1.15, loudness=0.1),
            
            # Engaging / Friendly (higher style for personality)
            VoiceTone.FRIENDLY: cls(stability=0.5, similarity_boost=0.8, style=0.75, speed=1.15, loudness=0.1),
            VoiceTone.CURIOUS: cls(stability=0.45, similarity_boost=0.7, style=0.8, speed=1.1, loudness=0.0),
            VoiceTone.PLAYFUL: cls(stability=0.35, similarity_boost=0.8, style=0.85, speed=1.2, loudness=0.1),
            
            # Special (high style for character)
            VoiceTone.MYSTERIOUS: cls(stability=0.55, similarity_boost=0.6, style=0.8, speed=0.8, loudness=-0.2),
            VoiceTone.SARCASTIC: cls(stability=0.45, similarity_boost=0.6, style=0.75, speed=1.0, loudness=0.0)
        }
        return settings_map.get(tone, cls(stability=0.5, similarity_boost=0.75, style=0.5, speed=1.0, loudness=0.0))

class VideoGenerationPrompt(BaseModel):
    """
    Detailed prompt for video generation including character movements, 
    background animations, and visual effects
    """
    base_description: str = Field(description="Basic description of what should happen in the video")
    
    # Character movement/gesture
    character_gesture: Optional[str] = Field(default=None, description="Character gestures: 'pointing at screen', 'nodding enthusiastically', 'looking surprised'")
    character_expression: Optional[str] = Field(default=None, description="Character facial expression: 'excited smile', 'thoughtful frown', 'wide-eyed wonder'")
    
    # Background/environment movement
    background_animation: Optional[str] = Field(default=None, description="Background animations: 'floating particles', 'gentle waves', 'rotating gears'")
    environmental_effects: Optional[str] = Field(default=None, description="Environmental effects: 'wind blowing leaves', 'bubbles rising', 'sparkles appearing'")
    
    # Camera/visual effects
    camera_behavior: Optional[str] = Field(default=None, description="Camera movements: 'slow zoom into character face', 'pan across the scene'")
    visual_emphasis: Optional[str] = Field(default=None, description="Visual emphasis: 'highlight important text', 'glow effect on key objects'")
    
    # Purpose of video generation
    animation_purpose: str = Field(description="Why animation is needed: 'to show emotion change', 'to demonstrate concept', 'to maintain engagement'")

class Scene(BaseModel):
    scene_number: int
    scene_type: SceneType
    
    # Dialogue/narration
    dialogue: Optional[str] = Field(default=None, description="What the character will say")
    text_overlay: Optional[str] = Field(default=None, description="Text to display on screen (e.g. key points, title)")
    voice_tone: VoiceTone
    elevenlabs_settings: ElevenLabsSettings
    
    # Image related
    image_style: ImageStyle
    image_create_prompt: str = Field(description="Detailed prompt for image generation - be very specific about visual elements, lighting, composition, and style")
    character_pose: Optional[str] = Field(default=None, description="Character pose: 'pointing', 'thinking', 'surprised'")
    background_description: Optional[str] = Field(default=None, description="Background setting description")
    
    # Video related (8 seconds fixed duration)
    needs_animation: bool = Field(description="Whether this scene needs video animation or static image is enough")
    video_prompt: Optional[str] = Field(default=None, description="Detailed video generation prompt if animation is needed")
    
    # Scene connectivity
    transition_to_next: TransitionType = Field(description="How to transition to the next scene")
    
    # Hook technique (only for first scene)
    hook_technique: Optional[HookTechnique] = Field(default=None, description="Specific hook technique used (only for hook scenes)")
    video_importance: int = Field(default=5, ge=0, le=10, description="Importance score for video generation (0-10)")
    
    # Manual workflow fields (TICKET-023)
    uploaded_video_path: Optional[str] = Field(default=None, description="Path to manually uploaded video file")
    selected_effect: str = Field(default="ken_burns_zoom_in", description="User-selected video effect for image animation")
    image_path: Optional[str] = Field(default=None, description="Path to generated image file")
    audio_path: Optional[str] = Field(default=None, description="Path to generated audio file")
    
    # VideoEffectAgent recommendations (TICKET-025)
    recommended_effect: Optional[str] = Field(default=None, description="AI-recommended video effect")
    recommended_ai_video: Optional[bool] = Field(default=None, description="Whether AI video generation is recommended")
    effect_reasoning: Optional[str] = Field(default=None, description="Reasoning for effect recommendation")

    @field_validator('scene_type', mode='before')
    @classmethod
    def validate_scene_type(cls, v):
        if isinstance(v, SceneType):
            return v
        if not isinstance(v, str):
            return v
            
        # Try to match enum directly
        try:
            return SceneType(v)
        except ValueError:
            pass
            
        # Common fixes
        fixes = {
            "climax": SceneType.CONCLUSION,
            "rising_action": SceneType.EXPLANATION,
            "development": SceneType.EXPLANATION,
            "resolution": SceneType.CONCLUSION,
            "introduction": SceneType.HOOK,
            "narrative": SceneType.STORY_TELLING,
            "opening": SceneType.HOOK,
        }
        
        if v in fixes:
            logger.warning(f"Fixed invalid scene_type: '{v}' -> '{fixes[v].value}'")
            return fixes[v]
            
        # Default fallback
        logger.warning(f"Invalid scene_type '{v}' not found in fixes. Defaulting to EXPLANATION.")
        return SceneType.EXPLANATION

    @field_validator('voice_tone', mode='before')
    @classmethod
    def validate_voice_tone(cls, v):
        if isinstance(v, VoiceTone):
            return v
        if not isinstance(v, str):
            return v
            
        try:
            return VoiceTone(v)
        except ValueError:
            pass
            
        fixes = {
            "explanation": VoiceTone.SERIOUS,
            "narrative": VoiceTone.CALM,
            "climax": VoiceTone.DRAMATIC,
            "development": VoiceTone.CURIOUS,
            "rising_action": VoiceTone.EXCITED,
            "informative": VoiceTone.SERIOUS,
            "conclusion": VoiceTone.CONFIDENT,
            "hook": VoiceTone.EXCITED,
        }
        
        if v in fixes:
            logger.warning(f"Fixed invalid voice_tone: '{v}' -> '{fixes[v].value}'")
            return fixes[v]
            
        logger.warning(f"Invalid voice_tone '{v}' not found in fixes. Defaulting to SERIOUS.")
        return VoiceTone.SERIOUS

    @field_validator('image_style', mode='before')
    @classmethod
    def validate_image_style(cls, v):
        if isinstance(v, ImageStyle):
            return v
        if not isinstance(v, str):
            return v
            
        try:
            return ImageStyle(v)
        except ValueError:
            pass
            
        fixes = {
            "comparison": ImageStyle.BEFORE_AFTER_COMPARISON,
            "split": ImageStyle.SPLIT_SCREEN,
            "character": ImageStyle.CHARACTER_WITH_BACKGROUND,
            "diagram": ImageStyle.DIAGRAM_EXPLANATION,
            "infograph": ImageStyle.INFOGRAPHIC,
            "comic": ImageStyle.COMIC_PANEL,
            "closeup": ImageStyle.CLOSE_UP_REACTION,
            "wide": ImageStyle.WIDE_ESTABLISHING_SHOT,
            "visual_demo": ImageStyle.STEP_BY_STEP_VISUAL,
        }
        
        if v in fixes:
            logger.warning(f"Fixed invalid image_style: '{v}' -> '{fixes[v].value}'")
            return fixes[v]
            
        logger.warning(f"Invalid image_style '{v}' not found in fixes. Defaulting to CINEMATIC.")
        return ImageStyle.CINEMATIC

class SceneConfig(BaseModel):
    """Configuration for building video from a scene"""
    scene_number: int
    use_uploaded_video: bool = False
    video_path: Optional[str] = None
    effect: str = "ken_burns_zoom_in"
    image_path: Optional[str] = None
    audio_path: Optional[str] = None

class VideoScript(BaseModel):
    """
    Complete video script with scenes in order
    First scene is always the hook scene
    """
    title: str
    main_character_description: str = Field(description="Consistent character description for all scenes")
    overall_style: str = Field(description="Overall video style: 'educational', 'entertaining', 'documentary'")
    global_visual_style: str = Field(description="Consistent visual style for all images (e.g., 'Pixar-style 3D', 'Cinematic lighting', 'Watercolor')")
    
    # All scenes in order
    scenes: List[Scene] = Field(description="All scenes in order, first scene is always the hook scene")
    
    @property
    def all_scenes(self) -> List[Scene]:
        """Return all scenes in order"""
        return self.scenes
    
    @property
    def total_scene_count(self) -> int:
        """Return total number of scenes"""
        return len(self.scenes)
    
    @property
    def hook_scene(self) -> Scene:
        """Return the first scene (hook scene)"""
        return self.scenes[0] if self.scenes else None
    
    def get_scene_by_number(self, scene_number: int) -> Optional[Scene]:
        """Get scene by its number"""
        for scene in self.scenes:
            if scene.scene_number == scene_number:
                return scene
        return None
    
    @field_validator('scenes')
    @classmethod
    def validate_scene_count(cls, v):
        """
        Validate that scene count is within MIN_SCENES and MAX_SCENES.
        
        This validator ensures that generated scripts meet the minimum
        and maximum scene requirements defined in settings.
        """
        from src.core.config import settings
        
        scene_count = len(v)
        
        if scene_count < settings.MIN_SCENES:
            raise ValueError(
                f"Script must have at least {settings.MIN_SCENES} scenes, "
                f"got {scene_count}. Please generate more scenes."
            )
        
        if scene_count > settings.MAX_SCENES:
            raise ValueError(
                f"Script must have at most {settings.MAX_SCENES} scenes, "
                f"got {scene_count}. Please reduce the number of scenes."
            )
        
        return v

# Animation decision guidelines for Agent 1
ANIMATION_GUIDELINES = """
USE ANIMATION when:
- Showing emotional changes (surprising fact reveal)
- Explaining complex concepts visually
- Need to focus viewer attention
- Character gestures help content understanding
- Demonstrating processes or movements
- Creating dramatic emphasis

USE STATIC IMAGE when:
- Simple information delivery
- Text or diagram-focused explanations
- Calm tone explanations
- Character is just speaking without emphasis
- Background information scenes
"""

# Video prompt examples for Agent 1
VIDEO_PROMPT_EXAMPLES = """
Good video_prompt examples:
- "Character starts with curious expression, then eyes widen with realization as floating salt molecules appear around them"
- "Character points enthusiastically at a diagram while gentle ocean waves move in background"
- "Character looks directly at camera with serious expression, background slowly darkens for dramatic effect"
- "Character nods thoughtfully while abstract thought bubbles float above their head"
- "Character gestures excitedly as colorful particles swirl around them to illustrate the concept"
"""