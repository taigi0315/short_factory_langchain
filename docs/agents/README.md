# Agents Documentation

**Last Updated:** 2025-11-25  
**Version:** 1.0

## Overview

The `src/agents/` directory contains the core AI agents that power the ShortFactory video generation pipeline. Each agent is responsible for a specific stage of the video creation process, from finding stories to assembling the final video.

### Purpose

This folder implements a multi-agent architecture where specialized agents work together to transform a topic or story into a complete short-form video. The agents use LLMs (primarily Google Gemini), image generation APIs, video generation services, and voice synthesis to create engaging content.

### When to Work Here

You'll work in this folder when:
- Adding new agent capabilities or improving existing ones
- Modifying the video generation pipeline logic
- Integrating new AI services or APIs
- Debugging issues in specific stages of video creation
- Enhancing prompt engineering for better outputs

---

## Architecture

The agents follow a **sequential pipeline architecture** with some parallel processing capabilities:

```
Story Finder → Script Writer → Director → Image Gen → Voice Gen → Video Gen → Video Assembly
                                            ↓           ↓           ↓
                                         (parallel)  (parallel)  (optional)
```

### Agent Flow

1. **Story Finder**: Discovers interesting stories from Reddit or other sources
2. **Script Writer**: Transforms stories into video scripts with scenes and dialogue
3. **Director**: Adds cinematic direction (shot types, camera movements, visual coherence)
4. **Image Gen**: Generates images for each scene based on prompts
5. **Voice Gen**: Synthesizes voiceover audio from dialogue
6. **Video Gen**: (Optional) Generates AI video for complex scenes
7. **Video Assembly**: Combines all assets into final video with effects and transitions

---

## File Inventory

### Agent Subdirectories

| Directory | Purpose | Key Files |
|-----------|---------|-----------|
| `director/` | Cinematic direction and shot planning | `agent.py`, `models.py`, `cinematic_language.py` |
| `story_finder/` | Reddit story discovery and filtering | `agent.py`, `models.py`, `prompts.py` |
| `script_writer/` | Script generation from stories | `agent.py`, `prompts.py` |
| `image_gen/` | Image generation orchestration | `agent.py`, `gemini_image_client.py`, `nanobanana_client.py` |
| `voice/` | Voice synthesis | `agent.py`, `elevenlabs_client.py` |
| `video_gen/` | AI video generation | `agent.py`, `providers/` |
| `video_assembly/` | Final video assembly | `agent.py` |
| `video_effect/` | Video effects (legacy/unused) | - |

### Root Files

- `__init__.py`: Package initialization
- `base_agent.py`: **Base class for all agents** (see below)

---

## Base Agent Architecture

### BaseAgent Class (`base_agent.py`)

**Purpose**: Provides common initialization logic and standardized behavior for all agents in the system.

**Added in**: TICKET-036 (Nov 2025)

All agents in the ShortFactory pipeline inherit from `BaseAgent`, which provides:
- **API key validation**: Ensures required API keys are present in real mode
- **LLM initialization**: Standardized LLM setup with retry logic
- **Mock mode handling**: Automatic mock mode detection and configuration
- **Logging setup**: Consistent structured logging across all agents

**Usage**:
```python
from src.agents.base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="MyAgent",
            temperature=0.7,
            max_retries=3,
            request_timeout=30.0,
            require_llm=True  # Set to False for non-LLM agents
        )
    
    def _setup(self):
        """Agent-specific setup logic."""
        # Initialize agent-specific components here
        self.my_tool = MyTool()
        
        # Build chains, configure providers, etc.
        if not self.mock_mode:
            self.chain = self._build_chain()
```

**Key Features**:
- **Template Method Pattern**: Defines initialization skeleton, subclasses override `_setup()`
- **Dependency Injection**: LLM and configuration injected via base class
- **Automatic Mock Mode**: Detects `USE_REAL_LLM` setting and configures accordingly
- **Error Handling**: Validates API keys and provides clear error messages

**Parameters**:
- `agent_name` (str): Name of the agent for logging
- `temperature` (float): LLM temperature setting (default: 0.7)
- `max_retries` (int): Number of retry attempts for LLM calls (default: 3)
- `request_timeout` (float): Timeout for LLM requests in seconds (default: 30.0)
- `require_llm` (bool): Whether this agent requires LLM (default: True)

**Benefits**:
- **Reduced Duplication**: Eliminated ~200 lines of duplicated initialization code
- **Consistency**: All agents behave identically for common operations
- **Maintainability**: Changes to initialization logic made in one place
- **Testability**: Shared test fixtures reduce test duplication

**Example Agents Using BaseAgent**:
All 7 agents in the pipeline inherit from `BaseAgent`:
- `StoryFinderAgent` (with LLM)
- `ScriptWriterAgent` (with LLM)
- `DirectorAgent` (with LLM)
- `ImageGenAgent` (without LLM, `require_llm=False`)
- `VoiceAgent` (without LLM, `require_llm=False`)
- `VideoGenAgent` (without LLM, `require_llm=False`)
- `VideoAssemblyAgent` (without LLM, `require_llm=False`)

---

## Key Components

### 1. Director Agent (`director/`)

**Purpose**: Transforms scripts into cinematically directed shot lists with visual coherence and emotional impact.

**Key Classes**:
- `DirectorAgent`: Main agent class
- `CinematicDirection`: Direction for a single scene
- `DirectedScene`: Scene with cinematic direction
- `DirectedScript`: Complete directed script
- `EmotionalArc`: Maps emotional journey through video

**Core Functionality**:
```python
from src.agents.director.agent import DirectorAgent

director = DirectorAgent()
directed_script = await director.analyze_script(video_script)
```

**Key Methods**:
- `analyze_script()`: Main entry point - analyzes script and creates cinematic direction
- `_identify_story_beats()`: Identifies narrative beats (Hook, Setup, Development, Resolution)
- `_generate_cinematic_direction()`: Uses LLM to generate shot types, camera movements, angles
- `select_transition()`: Chooses optimal transitions between scenes
- `recommend_ai_video()`: Decides if scene should use AI video vs. image+effect

**Cinematic Language** (`cinematic_language.py`):
Defines professional cinematography vocabulary:
- **Shot Types**: extreme_wide, wide, medium, close_up, etc.
- **Camera Movements**: static, slow_push_in, pan_left, dolly_zoom, etc.
- **Camera Angles**: eye_level, low, high, dutch, overhead
- **Lighting Moods**: bright, dramatic, soft, golden_hour, chiaroscuro
- **Composition Rules**: rule_of_thirds, symmetry, leading_lines, etc.

**Design Decisions**:
- Uses LLM (Gemini) to generate contextual cinematic direction for each scene
- Maps emotions to visual styles using `EMOTION_TO_VISUAL` dictionary
- Ensures visual continuity by analyzing previous/next scenes
- Provides fallback direction if LLM fails
- Avoids "handheld" camera movement by default (can be dizzying)

**Example Output**:
```python
{
    "shot_type": "medium_close_up",
    "camera_movement": "slow_push_in",
    "camera_angle": "low",
    "lighting_mood": "dramatic",
    "composition": "rule_of_thirds",
    "emotional_purpose": "Build tension and intrigue",
    "narrative_function": "Hook viewer with mystery",
    "enhanced_image_prompt": "Medium close-up of mysterious figure...",
    "director_notes": "This shot hooks the viewer by creating visual intrigue..."
}
```

---

### 2. Story Finder Agent (`story_finder/`)

**Purpose**: Discovers interesting stories from Reddit that are suitable for video adaptation.

**Key Classes**:
- `StoryFinderAgent`: Main agent class
- `RedditStory`: Data model for discovered stories

**Core Functionality**:
```python
from src.agents.story_finder.agent import StoryFinderAgent

story_finder = StoryFinderAgent()
stories = await story_finder.find_stories(
    subreddit="AskReddit",
    limit=10,
    min_score=1000
)
```

**Key Methods**:
- `find_stories()`: Searches Reddit for suitable stories
- `_filter_stories()`: Filters stories based on criteria (length, engagement, etc.)
- `_score_story()`: Scores stories for video potential

**Configuration**:
- Uses PRAW (Python Reddit API Wrapper) for Reddit access
- Filters by upvotes, comments, and content quality
- Looks for narrative structure and emotional hooks

---

### 3. Script Writer Agent (`script_writer/`)

**Purpose**: Transforms stories into structured video scripts with scenes, dialogue, and visual prompts.

**Key Classes**:
- `ScriptWriterAgent`: Main agent class

**Core Functionality**:
```python
from src.agents.script_writer.agent import ScriptWriterAgent

script_writer = ScriptWriterAgent()
video_script = await script_writer.generate_script(story)
```

**Key Methods**:
- `generate_script()`: Main entry point - generates complete video script
- `_create_scenes()`: Breaks story into scenes with dialogue
- `_generate_prompts()`: Creates image and video generation prompts

**Prompt Engineering** (`prompts.py`):
- Contains extensive prompt templates for different scene types
- Guides LLM to create engaging, short-form content
- Includes examples and formatting instructions
- ~28KB of carefully crafted prompts

**Scene Types**:
- `HOOK`: Grab attention in first 3 seconds
- `EXPLANATION`: Provide context and background
- `VISUAL_DEMO`: Show visual examples or demonstrations
- `COMPARISON`: Compare/contrast elements
- `CONCLUSION`: Wrap up and provide closure

---

### 4. Image Generation Agent (`image_gen/`)

**Purpose**: Orchestrates image generation using multiple providers (Gemini, NanoBanana).

**Key Classes**:
- `ImageGenAgent`: Main orchestration agent
- `GeminiImageClient`: Gemini Imagen integration
- `NanoBananaClient`: NanoBanana API integration

**Core Functionality**:
```python
from src.agents.image_gen.agent import ImageGenAgent

image_gen = ImageGenAgent()
image_path = await image_gen.generate_image(
    prompt="Cinematic shot of mysterious figure...",
    aspect_ratio="9:16"
)
```

**Key Methods**:
- `generate_image()`: Main entry point - generates image from prompt
- `_select_provider()`: Chooses best provider based on requirements
- `_retry_with_fallback()`: Implements retry logic with provider fallback

**Providers**:
- **Gemini Imagen**: Primary provider, high quality
- **NanoBanana**: Fallback provider, faster generation

**Design Decisions**:
- Implements retry logic with exponential backoff
- Falls back to alternative providers on failure
- Validates image generation success
- Saves images to `generated_assets/images/`

---

### 5. Voice Generation Agent (`voice/`)

**Purpose**: Synthesizes voiceover audio from dialogue using ElevenLabs.

**Key Classes**:
- `VoiceAgent`: Main agent class
- `ElevenLabsClient`: ElevenLabs API integration

**Core Functionality**:
```python
from src.agents.voice.agent import VoiceAgent

voice_agent = VoiceAgent()
audio_path = await voice_agent.generate_voice(
    text="Welcome to this amazing story...",
    voice_id="21m00Tcm4TlvDq8ikWAM"  # Rachel voice
)
```

**Key Methods**:
- `generate_voice()`: Generates audio from text
- `_select_voice()`: Chooses appropriate voice based on tone
- `_apply_effects()`: Applies audio effects if needed

**Voice Options**:
- Multiple voice profiles available
- Supports different tones (excited, calm, dramatic, etc.)
- Configurable speech rate and pitch

---

### 6. Video Generation Agent (`video_gen/`)

**Purpose**: Generates AI video for complex scenes that need motion.

**Key Classes**:
- `VideoGenAgent`: Main orchestration agent
- Provider-specific clients in `providers/`

**Core Functionality**:
```python
from src.agents.video_gen.agent import VideoGenAgent

video_gen = VideoGenAgent()
video_path = await video_gen.generate_video(
    prompt="Camera slowly pushes in on mysterious figure...",
    duration=3.0
)
```

**Key Methods**:
- `generate_video()`: Main entry point
- `_select_provider()`: Chooses video generation provider
- `_poll_for_completion()`: Polls async video generation jobs

**Providers**:
- Multiple video generation providers supported
- Implements async job polling for long-running generations
- Handles provider-specific API differences

**When Used**:
- High importance scenes (video_importance >= 9)
- Complex camera movements (dolly zoom, crane, orbit)
- Scenes marked as `needs_animation` with detailed prompts

---

### 7. Video Assembly Agent (`video_assembly/`)

**Purpose**: Combines all generated assets (images, audio, video) into final video with effects and transitions.

**Key Classes**:
- `VideoAssemblyAgent`: Main agent class

**Core Functionality**:
```python
from src.agents.video_assembly.agent import VideoAssemblyAgent

assembly_agent = VideoAssemblyAgent()
final_video_path = await assembly_agent.assemble_video(
    directed_script=directed_script,
    assets={
        "images": [...],
        "audio": [...],
        "videos": [...]
    }
)
```

**Key Methods**:
- `assemble_video()`: Main entry point - creates final video
- `_apply_effects()`: Applies camera movements and effects to images
- `_add_transitions()`: Adds transitions between scenes
- `_sync_audio()`: Synchronizes audio with visuals
- `_add_title_card()`: Adds title card at beginning

**Effects Supported**:
- Ken Burns (zoom in/out)
- Pan (left/right)
- Tilt (up/down)
- Shake (handheld effect)
- Dolly zoom
- Crane movements

**Output**:
- Final video in MP4 format
- Aspect ratio: 9:16 (vertical for shorts)
- Frame rate: 30 fps
- Audio: 44.1kHz stereo

---

## Implementation Details

### LLM Integration

All agents use **Google Gemini** as the primary LLM:

```python
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings

llm = ChatGoogleGenerativeAI(
    model=settings.llm_model_name,  # "gemini-2.0-flash-exp"
    temperature=0.7,
    google_api_key=settings.GEMINI_API_KEY
)
```

### Error Handling Strategy

Agents implement multi-level error handling:

1. **Retry Logic**: Exponential backoff for transient failures
2. **Fallback Providers**: Switch to alternative services
3. **Graceful Degradation**: Use simpler approaches if advanced features fail
4. **Fallback Defaults**: Provide reasonable defaults when all else fails

Example from Director Agent:
```python
try:
    # Try LLM-generated direction
    direction = await self._generate_scene_direction(...)
except Exception as e:
    logger.warning("LLM failed, using fallback")
    # Use emotion-to-visual mapping as fallback
    direction = self._create_fallback_scene_direction(scene, emotion)
```

### Logging

All agents use **structlog** for structured logging:

```python
import structlog

logger = structlog.get_logger()

logger.info("Analyzing script", 
    title=script.title, 
    scenes=len(script.scenes)
)
```

### Async/Await Pattern

Agents use async/await for I/O-bound operations:

```python
async def generate_image(self, prompt: str) -> str:
    # Async API calls
    response = await self.client.generate(prompt)
    return response.image_path
```

---

## Dependencies

### External Libraries

- **langchain-google-genai**: Google Gemini LLM integration
- **praw**: Reddit API access (Story Finder)
- **elevenlabs**: Voice synthesis
- **moviepy**: Video editing and assembly
- **Pillow**: Image processing
- **pydantic**: Data validation and models

### Internal Dependencies

- `src.core.config`: Configuration and settings
- `src.models.models`: Shared data models
- `src.utils`: Utility functions

### Environment Variables

Required environment variables (see `.env`):
```bash
GEMINI_API_KEY=your_gemini_key
ELEVENLABS_API_KEY=your_elevenlabs_key
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
NANOBANANA_API_KEY=your_nanobanana_key  # Optional
```

---

## Common Tasks

### Adding a New Agent

1. Create new subdirectory: `src/agents/my_agent/`
2. Create `agent.py` with main agent class **inheriting from `BaseAgent`**
3. Create `models.py` for data structures (if needed)
4. Create `prompts.py` for LLM prompts (if needed)
5. Add to pipeline in appropriate location
6. Update tests in `tests/unit/`

Example structure:
```python
# src/agents/my_agent/agent.py
import structlog
from src.agents.base_agent import BaseAgent
from src.core.config import settings

logger = structlog.get_logger()

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            agent_name="MyAgent",
            temperature=0.7,
            require_llm=True  # Set to False if agent doesn't need LLM
        )
    
    def _setup(self):
        """Agent-specific initialization."""
        # Initialize agent-specific components
        if not self.mock_mode:
            self.chain = self._build_chain()
    
    async def process(self, input_data):
        """Main processing method."""
        # Implementation
        pass
```

### Modifying Prompt Engineering

1. Locate prompts in `prompts.py` file
2. Update prompt templates
3. Test with various inputs
4. Monitor LLM responses for quality
5. Iterate based on results

**Best Practices**:
- Be specific and detailed in instructions
- Provide examples of desired output
- Specify output format (JSON, text, etc.)
- Include constraints and guidelines
- Test edge cases

### Improving Error Handling

1. Identify failure points in agent logic
2. Add try/except blocks with specific exceptions
3. Implement retry logic with exponential backoff
4. Add fallback strategies
5. Log errors with context using structlog

Example:
```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
async def generate_with_retry(self, prompt: str):
    try:
        return await self.client.generate(prompt)
    except ProviderError as e:
        logger.warning("Provider failed, trying fallback", error=str(e))
        return await self.fallback_client.generate(prompt)
```

### Testing Agents

1. Create unit tests in `tests/unit/test_<agent>_agent.py`
2. Use mocks for external API calls
3. Test happy path and error cases
4. Verify data model validation

Example:
```python
import pytest
from unittest.mock import Mock, patch
from src.agents.director.agent import DirectorAgent

@pytest.mark.asyncio
async def test_analyze_script():
    director = DirectorAgent()
    script = create_test_script()
    
    directed_script = await director.analyze_script(script)
    
    assert len(directed_script.directed_scenes) == len(script.scenes)
    assert directed_script.visual_theme is not None
```

---

## Gotchas and Notes

### Known Issues

1. **LLM JSON Parsing**: Gemini sometimes wraps JSON in markdown code blocks. Always extract JSON from ```json``` blocks.

2. **Rate Limiting**: External APIs (ElevenLabs, image generation) have rate limits. Implement exponential backoff.

3. **Async Context**: All agent methods should be async to support concurrent operations.

4. **Memory Usage**: Video assembly can be memory-intensive. Monitor memory usage for long videos.

5. **Handheld Effect**: The "handheld" camera movement can be dizzying. Use sparingly and only for chaotic scenes.

### Common Mistakes

1. **Forgetting to await**: All async methods must be awaited
   ```python
   # Wrong
   result = agent.process(data)
   
   # Correct
   result = await agent.process(data)
   ```

2. **Not handling LLM failures**: Always provide fallback logic
   ```python
   try:
       result = await llm.invoke(prompt)
   except Exception:
       result = fallback_result
   ```

3. **Hardcoding paths**: Use `settings` for all paths and configuration
   ```python
   # Wrong
   image_path = "/tmp/image.png"
   
   # Correct
   image_path = settings.generated_assets_dir / "images" / "image.png"
   ```

### Performance Considerations

1. **Parallel Processing**: Image and voice generation can run in parallel
2. **Caching**: Consider caching LLM responses for identical prompts
3. **Batch Processing**: Batch API calls when possible
4. **Resource Cleanup**: Clean up temporary files after video assembly

---

## Migration Notes

### Recent Changes

**TICKET-035** (Nov 2025): Director Agent now generates detailed image prompts for visual segments within each scene, improving image quality and consistency.

**TICKET-027** (Nov 2025): Improved error handling and retry logic across all agents.

### Backward Compatibility

The `get_effect_name()` method in Director Agent maintains backward compatibility with legacy effect names:

```python
# Maps new camera movements to legacy effect names
CAMERA_MOVEMENT_TO_EFFECT = {
    CameraMovement.SLOW_PUSH_IN: "ken_burns_zoom_in",
    CameraMovement.STATIC: "static",
    # ...
}
```

---

## Related Documentation

- [API Documentation](../API_DOCUMENTATION.md) - API endpoints that use these agents
- [Core Documentation](../core/README.md) - Configuration and core utilities
- [Models Documentation](../models/README.md) - Shared data models
- [Architecture Overview](../architecture/README.md) - System architecture

---

## Future Improvements

1. **Agent Orchestration**: Implement a coordinator agent to manage the pipeline
2. **Parallel Execution**: Run independent agents in parallel for faster processing
3. **Caching Layer**: Cache LLM responses and generated assets
4. **Quality Metrics**: Add quality scoring for generated content
5. **A/B Testing**: Support multiple prompt variations for testing
6. **Custom Agents**: Plugin system for custom agent implementations

---

**For questions or issues, see the main [Developer Guide](../DEVELOPER_GUIDE.md) or check existing tickets in `/tickets`.**
