# Data Models Documentation

## Overview

The `src/models/models.py` file contains all Pydantic data models used throughout the ShortFactory application. These models provide type safety, validation, and serialization for video content generation.

## Core Models

### Scene
**Purpose**: Represents a single scene in a video script

```python
class Scene(BaseModel):
    scene_number: int
    scene_title: str  # e.g., "hook", "story_telling"
    image_create_prompt: str  # Prompt for image generation
    image_style: ImageStyle  # Visual style enum
    dialogue: str  # Voiceover text
    voice_tone: VoiceTone  # Emotional tone enum
```

### VideoScript
**Purpose**: Complete video script with metadata

```python
class VideoScript(BaseModel):
    title: str
    category: str  # e.g., "Educational", "Entertainment"
    scenes: List[Scene]
```

## Enums

### ImageStyle
Visual styles for scene images:

- **Basic**: `single_character`, `character_with_background`
- **Educational**: `infographic`, `diagram_explanation`, `before_after_comparison`
- **Comic**: `four_cut_cartoon`, `comic_panel`, `speech_bubble`
- **Cinematic**: `cinematic`, `close_up_reaction`, `wide_establishing_shot`
- **Special**: `split_screen`, `overlay_graphics`, `cutaway_illustration`

### VoiceTone
Emotional tones for voiceover:

`excited`, `curious`, `serious`, `friendly`, `sad`, `mysterious`, `surprised`, `confident`, `worried`, `playful`, `dramatic`, `calm`, `enthusiastic`, `sarcastic`

### SceneType
Scene purposes:

`explanation`, `visual_demo`, `comparison`, `story_telling`, `hook`, `conclusion`

### TransitionType
Video transitions:

`fade`, `slide_left`, `slide_right`, `zoom_in`, `zoom_out`, `dissolve`, `wipe`, `push`, `spin`, `flip`, `none`

## Usage Examples

### Creating a Scene

```python
from src.models.models import Scene, ImageStyle, VoiceTone

scene = Scene(
    scene_number=1,
    scene_title="hook",
    image_create_prompt="A cinematic coffee shop at sunrise",
    image_style=ImageStyle.CINEMATIC,
    dialogue="Welcome to the amazing world of coffee!",
    voice_tone=VoiceTone.ENTHUSIASTIC
)
```

### Validation

Pydantic automatically validates:

```python
# This will raise ValidationError
scene = Scene(
    scene_number="not a number",  # Must be int
    image_style="invalid_style"   # Must be valid ImageStyle
)
```

---

**Last Updated**: 2025-01-21
