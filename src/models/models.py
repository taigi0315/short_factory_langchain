from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from enum import Enum

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
    speed: float = Field(ge=0.7, le=1.2, description="Speech delivery rate")
    loudness: float = Field(ge=-1.0, le=1.0, description="Audio output volume")
    
    @classmethod
    def for_tone(cls, tone: VoiceTone) -> 'ElevenLabsSettings':
        """Return recommended settings for each voice tone"""
        settings_map = {
            # High Energy / Expressive
            VoiceTone.EXCITED: cls(stability=0.35, similarity_boost=0.9, style=0.65, speed=1.15, loudness=0.2),
            VoiceTone.ENTHUSIASTIC: cls(stability=0.3, similarity_boost=0.8, style=0.7, speed=1.2, loudness=0.3),
            VoiceTone.SURPRISED: cls(stability=0.25, similarity_boost=0.75, style=0.8, speed=1.1, loudness=0.1),
            VoiceTone.DRAMATIC: cls(stability=0.4, similarity_boost=0.8, style=0.6, speed=0.9, loudness=0.2),
            
            # Low Energy / Somber
            VoiceTone.SAD: cls(stability=0.8, similarity_boost=0.7, style=0.2, speed=0.8, loudness=-0.2),
            VoiceTone.WORRIED: cls(stability=0.5, similarity_boost=0.8, style=0.4, speed=0.9, loudness=-0.1),
            
            # Neutral / Professional
            VoiceTone.SERIOUS: cls(stability=0.8, similarity_boost=0.8, style=0.1, speed=0.95, loudness=0.0),
            VoiceTone.CONFIDENT: cls(stability=0.7, similarity_boost=0.9, style=0.35, speed=1.0, loudness=0.1),
            VoiceTone.CALM: cls(stability=0.9, similarity_boost=0.9, style=0.0, speed=0.9, loudness=-0.1),
            
            # Engaging / Friendly
            VoiceTone.FRIENDLY: cls(stability=0.6, similarity_boost=0.85, style=0.4, speed=1.05, loudness=0.1),
            VoiceTone.CURIOUS: cls(stability=0.5, similarity_boost=0.8, style=0.5, speed=1.0, loudness=0.0),
            VoiceTone.PLAYFUL: cls(stability=0.4, similarity_boost=0.8, style=0.6, speed=1.1, loudness=0.1),
            
            # Special
            VoiceTone.MYSTERIOUS: cls(stability=0.6, similarity_boost=0.6, style=0.5, speed=0.8, loudness=-0.2),
            VoiceTone.SARCASTIC: cls(stability=0.5, similarity_boost=0.5, style=0.8, speed=0.85, loudness=0.0)
        }
        return settings_map.get(tone, cls(stability=0.5, similarity_boost=0.75, style=0.0, speed=1.0, loudness=0.0))

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
    hook_technique: Optional[HookTechnique] = Field(default=None, description="Hook technique used if this is the first scene")

class VideoScript(BaseModel):
    """
    Complete video script with scenes in order
    First scene is always the hook scene
    """
    title: str
    main_character_description: str = Field(description="Consistent character description for all scenes")
    overall_style: str = Field(description="Overall video style: 'educational', 'entertaining', 'documentary'")
    
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