# Models Documentation

**Last Updated:** 2025-11-25  
**Version:** 1.0

## Overview

The `src/models/` directory contains Pydantic data models that define the structure of all data flowing through the ShortFactory video generation pipeline. These models provide type safety, validation, and serialization for scripts, scenes, and configuration.

### Purpose

This folder provides:
- **Type-safe Data Structures**: Pydantic models with automatic validation
- **Shared Schemas**: Common data models used across all agents
- **Enum Definitions**: Standardized enumerations for scene types, voice tones, etc.
- **Validation Logic**: Business rules and constraints
- **Serialization**: JSON conversion for API responses and storage

### When to Work Here

You'll work in this folder when:
- Adding new data fields to scenes or scripts
- Creating new enum types (scene types, transitions, etc.)
- Modifying validation rules
- Adding computed properties
- Debugging data validation errors

---

## Architecture

The models follow a **hierarchical structure**:

```
VideoScript
    ├── title
    ├── main_character_description
    ├── scenes: List[Scene]
    │   ├── scene_number
    │   ├── scene_type: SceneType (enum)
    │   ├── content: List[VisualSegment]
    │   │   ├── segment_text
    │   │   └── image_prompt
    │   ├── voice_tone: VoiceTone (enum)
    │   ├── image_style: ImageStyle (enum)
    │   ├── needs_animation: bool
    │   └── video_prompt: Optional[VideoGenerationPrompt]
    └── transitions: List[TransitionType]
```

---

## File Inventory

| File | Purpose | Key Components |
|------|---------|----------------|
| `models.py` | All data models and enums | `VideoScript`, `Scene`, `VisualSegment`, enums |

---

## Key Components

### 1. Enumerations

#### SceneType

**Purpose**: Categorizes scenes by their narrative function.

```python
class SceneType(str, Enum):
    EXPLANATION = "explanation"  # Provide context and background
    VISUAL_DEMO = "visual_demo"  # Show visual examples
    COMPARISON = "comparison"  # Compare/contrast elements
    STORY_TELLING = "story_telling"  # Narrative storytelling
    HOOK = "hook"  # Grab attention (first 3 seconds)
    CONCLUSION = "conclusion"  # Wrap up and closure
```

**Usage**:
```python
from src.models.models import SceneType

scene = Scene(
    scene_number=1,
    scene_type=SceneType.HOOK,
    # ...
)
```

---

#### ImageStyle

**Purpose**: Defines visual style for image generation.

```python
class ImageStyle(str, Enum):
    SINGLE_CHARACTER = "single_character"
    CHARACTER_WITH_BACKGROUND = "character_with_background"
    INFOGRAPHIC = "infographic"
    DIAGRAM_EXPLANATION = "diagram_explanation"
    BEFORE_AFTER_COMPARISON = "before_after_comparison"
    SIDE_BY_SIDE_COMPARISON = "side_by_side_comparison"
    TIMELINE_VISUALIZATION = "timeline_visualization"
    PROCESS_STEPS = "process_steps"
    EMOTIONAL_MOMENT = "emotional_moment"
    ACTION_SCENE = "action_scene"
    CLOSE_UP_REACTION = "close_up_reaction"
    WIDE_ESTABLISHING_SHOT = "wide_establishing_shot"
    VISUAL_SURPRISE = "visual_surprise"
    SPLIT_SCREEN = "split_screen"
    OVERLAY_GRAPHICS = "overlay_graphics"
    CUTAWAY_ILLUSTRATION = "cutaway_illustration"
```

**Usage**:
```python
scene = Scene(
    image_style=ImageStyle.INFOGRAPHIC,
    # ...
)
```

---

#### VoiceTone

**Purpose**: Specifies emotional tone for voice synthesis.

```python
class VoiceTone(str, Enum):
    EXCITED = "excited"
    CURIOUS = "curious"
    SERIOUS = "serious"
    FRIENDLY = "friendly"
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
```

**ElevenLabs Settings Mapping**:
```python
settings = ElevenLabsSettings.for_tone(VoiceTone.EXCITED)
# Returns: stability=0.3, similarity_boost=0.8, style=0.7, speed=1.1
```

---

#### TransitionType

**Purpose**: Defines transitions between scenes.

```python
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
    NONE = "none"  # Direct cut
```

---

#### HookTechnique

**Purpose**: Categorizes hook techniques for first scene.

```python
class HookTechnique(str, Enum):
    SHOCKING_FACT = "shocking_fact"
    INTRIGUING_QUESTION = "intriguing_question"
    VISUAL_SURPRISE = "visual_surprise"
    CONTRADICTION = "contradiction"
    MYSTERY_SETUP = "mystery_setup"
```

---

### 2. Core Models

#### VisualSegment

**Purpose**: Represents a single visual beat within a scene.

```python
class VisualSegment(BaseModel):
    segment_text: str = Field(
        ..., 
        description="The specific portion of dialogue corresponding to this image."
    )
    image_prompt: str = Field(
        ..., 
        description="Detailed image generation prompt for this segment."
    )
```

**Example**:
```python
segment = VisualSegment(
    segment_text="The AI began to dream...",
    image_prompt="Cinematic shot of a glowing neural network with dream-like imagery"
)
```

**Use Case**: Allows scenes to have multiple images that change as dialogue progresses.

---

#### Scene

**Purpose**: Represents a single scene in the video with all metadata.

**Key Fields**:

```python
class Scene(BaseModel):
    # Identification
    scene_number: int
    scene_type: SceneType
    
    # Content
    content: List[VisualSegment] = Field(
        ..., 
        description="List of visual beats within this scene."
    )
    
    # Voice settings
    voice_tone: VoiceTone
    elevenlabs_settings: Optional[ElevenLabsSettings] = None
    
    # Visual settings
    image_style: ImageStyle
    
    # Animation settings
    needs_animation: bool = False
    video_prompt: Optional[str] = None
    video_importance: int = Field(default=5, ge=1, le=10)
    
    # Hook settings (for hook scenes)
    hook_technique: Optional[HookTechnique] = None
    hook_intensity: Optional[int] = Field(default=None, ge=1, le=10)
```

**Computed Properties**:

```python
@computed_field
@property
def dialogue(self) -> str:
    """Derived full dialogue from segments"""
    return " ".join(seg.segment_text for seg in self.content)

@computed_field
@property
def image_prompts(self) -> List[str]:
    """Derived list of image prompts"""
    return [seg.image_prompt for seg in self.content]

@computed_field
@property
def image_create_prompt(self) -> str:
    """Backward compatibility: return first image prompt"""
    return self.content[0].image_prompt if self.content else ""
```

**Validators**:

```python
@field_validator('scene_type')
@classmethod
def validate_scene_type(cls, v):
    """Validate scene type is valid enum value"""
    if isinstance(v, str):
        try:
            return SceneType(v)
        except ValueError:
            valid_types = [t.value for t in SceneType]
            raise ValueError(f"Invalid scene_type: {v}. Must be one of {valid_types}")
    return v
```

**Example**:
```python
scene = Scene(
    scene_number=1,
    scene_type=SceneType.HOOK,
    content=[
        VisualSegment(
            segment_text="What if AI could dream?",
            image_prompt="Cinematic close-up of glowing AI neural network"
        )
    ],
    voice_tone=VoiceTone.MYSTERIOUS,
    image_style=ImageStyle.VISUAL_SURPRISE,
    needs_animation=False,
    hook_technique=HookTechnique.INTRIGUING_QUESTION,
    hook_intensity=9
)
```

---

#### VideoScript

**Purpose**: Complete video script with all scenes and metadata.

**Key Fields**:

```python
class VideoScript(BaseModel):
    # Metadata
    title: str
    main_character_description: str = Field(
        description="Consistent character description for all scenes"
    )
    
    # Scenes
    scenes: List[Scene]
    
    # Transitions
    transitions: List[TransitionType] = Field(
        default_factory=list,
        description="Transition between each scene (length = scenes - 1)"
    )
    
    # Estimated duration
    estimated_duration: Optional[float] = Field(
        default=None,
        description="Estimated total duration in seconds"
    )
```

**Computed Properties**:

```python
@computed_field
@property
def all_scenes(self) -> List[Scene]:
    """Return all scenes in order"""
    return self.scenes

@computed_field
@property
def total_scene_count(self) -> int:
    """Return total number of scenes"""
    return len(self.scenes)

@computed_field
@property
def hook_scene(self) -> Scene:
    """Return the first scene (hook scene)"""
    return self.scenes[0] if self.scenes else None
```

**Validators**:

```python
@field_validator('scenes')
@classmethod
def validate_scene_count(cls, v):
    """Validate that scene count is within MIN_SCENES and MAX_SCENES."""
    from src.core.config import settings
    
    if len(v) < settings.MIN_SCENES:
        raise ValueError(
            f"Script must have at least {settings.MIN_SCENES} scenes, got {len(v)}"
        )
    if len(v) > settings.MAX_SCENES:
        raise ValueError(
            f"Script must have at most {settings.MAX_SCENES} scenes, got {len(v)}"
        )
    return v
```

**Example**:
```python
script = VideoScript(
    title="The AI That Learned to Dream",
    main_character_description="A futuristic AI with glowing blue neural networks",
    scenes=[
        Scene(scene_number=1, scene_type=SceneType.HOOK, ...),
        Scene(scene_number=2, scene_type=SceneType.EXPLANATION, ...),
        Scene(scene_number=3, scene_type=SceneType.CONCLUSION, ...)
    ],
    transitions=[
        TransitionType.ZOOM_IN,
        TransitionType.FADE
    ],
    estimated_duration=58.5
)
```

---

#### SceneConfig

**Purpose**: Configuration for building video from a scene (used in video assembly).

```python
class SceneConfig(BaseModel):
    """Configuration for building video from a scene"""
    
    scene_number: int
    use_uploaded_video: bool = False
    video_path: Optional[str] = None
    effect: str = "ken_burns_zoom_in"
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
```

**Example**:
```python
config = SceneConfig(
    scene_number=1,
    use_uploaded_video=False,
    effect="slow_push_in",
    image_path="generated_assets/images/scene_1.png",
    audio_path="generated_assets/audio/scene_1.mp3"
)
```

---

#### ElevenLabsSettings

**Purpose**: Voice synthesis settings for ElevenLabs API.

```python
class ElevenLabsSettings(BaseModel):
    stability: float = Field(
        ge=0.0, le=1.0, 
        description="Consistency vs emotional expression"
    )
    similarity_boost: float = Field(
        ge=0.0, le=1.0, 
        description="Closeness to reference voice"
    )
    style: float = Field(
        ge=0.0, le=1.0, 
        description="Exaggeration of speaking style"
    )
    speed: float = Field(
        ge=0.5, le=2.0, 
        description="Speech delivery rate"
    )
    loudness: float = Field(
        ge=-1.0, le=1.0, 
        description="Audio output volume"
    )
```

**Tone-based Presets**:

```python
@classmethod
def for_tone(cls, tone: VoiceTone) -> "ElevenLabsSettings":
    """Return recommended settings for each voice tone"""
    
    tone_settings = {
        VoiceTone.EXCITED: cls(
            stability=0.3,
            similarity_boost=0.8,
            style=0.7,
            speed=1.1,
            loudness=0.3
        ),
        VoiceTone.CALM: cls(
            stability=0.7,
            similarity_boost=0.6,
            style=0.3,
            speed=0.9,
            loudness=0.0
        ),
        VoiceTone.DRAMATIC: cls(
            stability=0.4,
            similarity_boost=0.7,
            style=0.8,
            speed=0.95,
            loudness=0.2
        ),
        # ... more presets
    }
    
    return tone_settings.get(tone, cls())  # Default settings if not found
```

**Usage**:
```python
settings = ElevenLabsSettings.for_tone(VoiceTone.EXCITED)
# Use settings in ElevenLabs API call
```

---

#### VideoGenerationPrompt

**Purpose**: Detailed prompt for AI video generation.

```python
class VideoGenerationPrompt(BaseModel):
    """Detailed prompt for video generation including character movements, 
    background animations, and visual effects"""
    
    start_description: str = Field(
        description="What the viewer sees at the start of the video"
    )
    end_description: str = Field(
        description="What the viewer sees at the end of the video"
    )
    character_movement: str = Field(
        description="How the character moves or changes"
    )
    background_animation: str = Field(
        description="How the background or environment changes"
    )
    animation_purpose: str = Field(
        description="Why animation is needed: 'to show emotion change', 'to demonstrate concept', 'to maintain engagement'"
    )
```

**Example**:
```python
video_prompt = VideoGenerationPrompt(
    start_description="AI neural network glowing softly in darkness",
    end_description="Neural network pulsing brightly with dream imagery",
    character_movement="Neural connections light up sequentially",
    background_animation="Dream-like imagery fades in and out",
    animation_purpose="to show the AI 'waking up' and beginning to dream"
)
```

---

## Implementation Details

### Validation Strategy

All models use **Pydantic validators** for:

1. **Type Checking**: Automatic type validation
2. **Value Constraints**: Min/max values, string lengths
3. **Enum Validation**: Ensure valid enum values
4. **Business Rules**: Custom validation logic

**Example Validator**:
```python
@field_validator('video_importance')
@classmethod
def validate_importance(cls, v):
    """Ensure video importance is 1-10"""
    if not 1 <= v <= 10:
        raise ValueError(f"video_importance must be 1-10, got {v}")
    return v
```

### Computed Fields

**Computed fields** derive values from other fields:

```python
@computed_field
@property
def dialogue(self) -> str:
    """Combine all segment texts"""
    return " ".join(seg.segment_text for seg in self.content)
```

**Benefits**:
- No data duplication
- Always in sync with source data
- Included in serialization

### Serialization

All models can be serialized to/from JSON:

```python
# To JSON
script_dict = script.model_dump()
script_json = script.model_dump_json()

# From JSON
script = VideoScript.model_validate(data)
script = VideoScript.model_validate_json(json_string)
```

### Backward Compatibility

**`image_create_prompt` property** maintains backward compatibility:

```python
@computed_field
@property
def image_create_prompt(self) -> str:
    """Backward compatibility: return first image prompt"""
    return self.content[0].image_prompt if self.content else ""
```

**Old code** still works:
```python
prompt = scene.image_create_prompt  # Returns first segment's prompt
```

**New code** uses segments:
```python
prompts = scene.image_prompts  # Returns all prompts
```

---

## Dependencies

### External Libraries

- **pydantic**: Data validation and settings management
- **typing**: Type hints

### Internal Dependencies

- `src.core.config`: Settings for validation constraints

---

## Common Tasks

### Adding a New Field to Scene

1. **Add field to Scene class**:
   ```python
   class Scene(BaseModel):
       # Existing fields...
       new_field: str = Field(
           default="default_value",
           description="Description of new field"
       )
   ```

2. **Add validator if needed**:
   ```python
   @field_validator('new_field')
   @classmethod
   def validate_new_field(cls, v):
       if not v:
           raise ValueError("new_field cannot be empty")
       return v
   ```

3. **Update tests**:
   ```python
   def test_scene_with_new_field():
       scene = Scene(
           scene_number=1,
           scene_type=SceneType.HOOK,
           new_field="test_value",
           # ...
       )
       assert scene.new_field == "test_value"
   ```

### Adding a New Enum

1. **Define enum**:
   ```python
   class NewEnum(str, Enum):
       OPTION_1 = "option_1"
       OPTION_2 = "option_2"
   ```

2. **Use in model**:
   ```python
   class Scene(BaseModel):
       new_enum_field: NewEnum
   ```

3. **Add validator**:
   ```python
   @field_validator('new_enum_field')
   @classmethod
   def validate_new_enum(cls, v):
       if isinstance(v, str):
           try:
               return NewEnum(v)
           except ValueError:
               valid_values = [e.value for e in NewEnum]
               raise ValueError(f"Invalid value: {v}. Must be one of {valid_values}")
       return v
   ```

### Adding a Computed Field

```python
@computed_field
@property
def my_computed_field(self) -> str:
    """Compute value from other fields"""
    return f"{self.field1}_{self.field2}"
```

### Creating a Model Instance

```python
# From constructor
scene = Scene(
    scene_number=1,
    scene_type=SceneType.HOOK,
    content=[...],
    voice_tone=VoiceTone.EXCITED,
    image_style=ImageStyle.VISUAL_SURPRISE
)

# From dict
scene = Scene(**data_dict)

# From JSON
scene = Scene.model_validate_json(json_string)
```

---

## Gotchas and Notes

### Known Issues

1. **Enum String Conversion**: Enums must be converted to strings for JSON serialization
   ```python
   # Wrong
   {"scene_type": SceneType.HOOK}
   
   # Correct
   {"scene_type": SceneType.HOOK.value}
   # Or use model_dump()
   scene.model_dump()  # Automatically converts enums
   ```

2. **Computed Fields in Constructors**: Cannot set computed fields directly
   ```python
   # Wrong
   scene = Scene(dialogue="test", ...)
   
   # Correct
   scene = Scene(content=[VisualSegment(segment_text="test", ...)], ...)
   # dialogue is computed automatically
   ```

3. **Validation Order**: Validators run in field definition order

4. **Optional vs None**: Use `Optional[T]` for nullable fields
   ```python
   # Correct
   video_prompt: Optional[str] = None
   
   # Wrong (will fail validation if None)
   video_prompt: str = None
   ```

### Common Mistakes

1. **Forgetting to import enums**:
   ```python
   # Wrong
   scene_type="hook"
   
   # Correct
   from src.models.models import SceneType
   scene_type=SceneType.HOOK
   ```

2. **Not using Field for descriptions**:
   ```python
   # Less helpful
   name: str
   
   # Better
   name: str = Field(description="User's full name")
   ```

3. **Modifying immutable models**:
   ```python
   # Wrong (Pydantic models are immutable by default)
   scene.scene_number = 2
   
   # Correct
   scene = scene.model_copy(update={"scene_number": 2})
   ```

### Performance Considerations

1. **Validation Overhead**: Validation runs on every model creation. Use `model_construct()` to skip validation for trusted data.

2. **Computed Fields**: Computed on every access. Cache if expensive.

3. **Large Lists**: Validating large lists of scenes can be slow. Consider batch validation.

---

## Testing

### Unit Tests

```python
import pytest
from src.models.models import Scene, SceneType, VoiceTone, ImageStyle, VisualSegment

def test_scene_creation():
    scene = Scene(
        scene_number=1,
        scene_type=SceneType.HOOK,
        content=[
            VisualSegment(
                segment_text="Test",
                image_prompt="Test prompt"
            )
        ],
        voice_tone=VoiceTone.EXCITED,
        image_style=ImageStyle.VISUAL_SURPRISE
    )
    
    assert scene.scene_number == 1
    assert scene.dialogue == "Test"
    assert len(scene.image_prompts) == 1

def test_scene_validation():
    with pytest.raises(ValueError):
        Scene(
            scene_number=1,
            scene_type="invalid_type",  # Should fail
            content=[],
            voice_tone=VoiceTone.EXCITED,
            image_style=ImageStyle.VISUAL_SURPRISE
        )
```

---

## Related Documentation

- [Agents Documentation](../agents/README.md) - Agents that use these models
- [API Documentation](../api/README.md) - API schemas based on these models
- [Core Documentation](../core/README.md) - Configuration used in validation

---

## Future Improvements

1. **Model Versioning**: Support multiple model versions for backward compatibility
2. **Custom Serializers**: Add custom JSON serializers for complex types
3. **Validation Caching**: Cache validation results for performance
4. **Schema Generation**: Auto-generate OpenAPI schemas from models
5. **Model Inheritance**: Create base classes for common patterns
6. **Stricter Validation**: Add more business rule validators
7. **Documentation Generation**: Auto-generate docs from Field descriptions

---

**For questions or issues, see the main [Developer Guide](../DEVELOPER_GUIDE.md) or check existing tickets in `/tickets`.**
