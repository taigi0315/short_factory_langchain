# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ShortFactory is an AI-powered platform that automatically generates short-form videos (YouTube Shorts, Instagram Reels) from text topics. It uses a multi-agent architecture with Google Gemini for LLM/image generation, ElevenLabs for voice synthesis, and Luma Dream Machine for video generation.

**Stack:**
- Backend: Python 3.12, FastAPI, LangChain
- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS
- AI Services: Google Gemini, ElevenLabs, Tavily (search), Luma (optional)

## Development Commands

### Setup
```bash
# Full setup (backend + frontend)
make setup

# Backend only
make setup-backend

# Frontend only
make setup-frontend

# Quick start (auto-detects what needs setup)
./start_dev.sh
```

### Running Services
```bash
# Start both backend and frontend (macOS opens frontend in new tab)
./start_dev.sh

# Or manually:
make run-backend  # http://localhost:8000
make run-frontend # http://localhost:3000
```

### Testing
```bash
# All tests
pytest tests/

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# Run specific test
python -m tests.unit.test_script_prompt_regression

# With coverage
pytest --cov=src tests/
```

### Code Quality
```bash
# Linting
ruff check src/

# Type checking
mypy src/

# Formatting
black src/
```

## Architecture Overview

### Multi-Agent Pipeline

The system uses a sequential pipeline of specialized AI agents, each handling a specific stage of video generation:

1. **Story Finder Agent** (`src/agents/story_finder/`)
   - Uses dynamic prompt routing based on story category (News/Real Story/Fiction/Educational)
   - Integrates Tavily web search for News and Real Story categories
   - Returns ranked story ideas

2. **Script Writer Agent** (`src/agents/script_writer/`)
   - Converts story ideas into structured 5-part VideoScript (hook, development, resolution)
   - Uses dynamic prompts from `prompts.py` with all enum values injected
   - Each scene has: dialogue, image prompt, voice tone, animation decision
   - Enforces mandatory hook technique in first scene

3. **Image Generator Agent** (`src/agents/image_gen/`)
   - Generates 9:16 aspect ratio images using Gemini Image API
   - Maintains character consistency across scenes
   - Implements caching to avoid regeneration

4. **Voice Synthesizer Agent** (`src/agents/voice/`)
   - Uses ElevenLabs with 13 emotional tones (excited, serious, mysterious, etc.)
   - Dynamic settings per tone (stability, similarity_boost, style, speed, loudness)
   - Settings defined in `src/models/models.py` ElevenLabsSettings.for_tone()

5. **Video Assembler Agent** (`src/agents/video_assembly/`)
   - Uses MoviePy for video assembly
   - Supports Ken Burns effect for static images
   - Optional Luma integration for image-to-video animation (when needs_animation=true)
   - Syncs video duration to audio length

### Data Models

Core models are defined in `src/models/models.py`:

- **VideoScript**: Contains title, character description, style, and list of scenes
- **Scene**: Has scene_number, scene_type, dialogue, voice_tone, image_create_prompt, needs_animation, video_prompt, transition_to_next
- **Enums**: SceneType, ImageStyle, VoiceTone, TransitionType, HookTechnique

**IMPORTANT**: The Script Writer uses dynamic prompts that inject all enum values from models. If you add/modify enums in `models.py`, they automatically appear in the prompt via `create_dynamic_prompt()` in `src/agents/script_writer/prompts.py`.

### Workflow State Management

The system implements resumable workflows using checkpoint-based state tracking:

- **WorkflowStateManager** (`src/core/workflow_state.py`) persists progress to JSON
- Tracks completed steps: script_generation → image_generation → audio_generation → video_assembly
- Stores paths to generated artifacts (script, images, audio, final video)
- Enables recovery from failures by resuming from last checkpoint

### API Structure

FastAPI backend (`src/api/main.py`) with routes:

- `/api/stories/*` - Story generation endpoints
- `/api/scripts/*` - Script generation endpoints
- `/api/dev/*` - Development/testing endpoints
- `/api/scene-editor/*` - Scene editing functionality
- `/generated_assets` - Static file serving for generated content
- `/health` - Health check (validates API keys if real mode enabled)

## Configuration

Environment variables in `.env`:

```bash
# Required API Keys
GEMINI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
TAVILY_API_KEY=your_key  # Required for Story Finder web search

# Optional
LUMA_API_KEY=your_key  # For AI video generation

# Feature Flags
USE_REAL_LLM=true
USE_REAL_IMAGE=true
USE_REAL_VOICE=true

# Video Settings
VIDEO_RESOLUTION=1080p
VIDEO_FPS=30
IMAGE_ASPECT_RATIO=9:16
DEFAULT_SCENE_DURATION=8.0
VIDEO_GENERATION_PROVIDER=mock  # or 'luma'
```

Settings loaded via `src/core/config.py` using pydantic-settings.

## Key Implementation Details

### Prompt Engineering Strategy

**Dynamic Prompt System**: The Script Writer agent uses `create_dynamic_prompt()` which:
1. Extracts all enum values from Pydantic models
2. Injects them into the prompt template
3. Uses LangChain's PydanticOutputParser for structured output
4. Ensures LLM always sees current valid options

This eliminates hardcoded enum values in prompts and prevents drift between models and prompts.

### Image Aspect Ratio Enforcement

All images MUST be 9:16 for vertical video format:
- Specified in image prompts as "9:16 aspect ratio, vertical image"
- Validated in tests (`tests/unit/test_image_aspect_ratio.py`)
- Critical for Instagram Reels/YouTube Shorts format

### Multiple Images Per Dialogue

Scenes support multiple images for a single dialogue segment:
- Scene.image_create_prompt can be List[str] or str
- Image generation loops handle both cases
- Enables visual variety within single narrative beat
- Implemented in TICKET-032

### Voice Tone Mapping

Each VoiceTone enum has corresponding ElevenLabsSettings:
- High energy (excited, enthusiastic) → lower stability, higher style, faster speed
- Emotional/soft (sad, calm) → higher stability, slower speed, lower loudness
- Neutral (friendly, confident) → balanced settings
- See `ElevenLabsSettings.for_tone()` in models.py for full mapping

### Caching Strategy

- **Image cache**: Prevents regenerating identical prompts
- **Script cache**: Saves generated scripts to workflow directory
- Cache implementation in workflow_state.py

## Testing Strategy

Tests are organized by type:

**Unit Tests** (`tests/unit/`):
- `test_script_prompt_regression.py` - Validates prompt output schema
- `test_image_aspect_ratio.py` - Ensures 9:16 ratio
- `test_audio_quality.py` - Voice synthesis validation
- `test_multiple_images.py` - Multi-image per scene support
- `test_visual_segmentation.py` - Scene segmentation logic
- `test_story_finder_routing.py` - Dynamic routing logic
- `test_min_scenes_validation.py` - Minimum scene count enforcement

**Integration Tests** (`tests/integration/`):
- `test_pipeline.py` - End-to-end pipeline
- `test_story_finder_integration.py` - Story finder with real API

Run tests with `pytest tests/` or specific test with `python -m tests.unit.test_name`.

## Common Development Patterns

### Adding New Scene Types

1. Add enum to `SceneType` in `src/models/models.py`
2. No prompt changes needed (dynamic injection handles it)
3. Add test case in `tests/unit/test_script_prompt_regression.py`

### Adding New Voice Tones

1. Add enum to `VoiceTone` in `src/models/models.py`
2. Add settings mapping in `ElevenLabsSettings.for_tone()`
3. Test in `tests/unit/test_audio_quality.py`

### Modifying Agent Behavior

Each agent has:
- `agent.py` - Main logic and LangChain chain setup
- `prompts.py` (if applicable) - Prompt templates
- Config loaded from `src/core/config.py`

### Working with Workflows

When implementing features that generate artifacts:
1. Use WorkflowStateManager to track progress
2. Save intermediate results to workflow directory
3. Enable resume by checking completed_steps before executing
4. Update state after each step completion

## Project Structure Notes

- `src/agents/` - Each agent is self-contained with agent.py and optional prompts.py
- `src/api/routes/` - API endpoints organized by resource
- `src/core/` - Shared utilities (logging, config, workflow state)
- `src/models/` - Pydantic models (single source of truth for data structures)
- `generated_assets/` - Output directory for all generated content
- `tickets/` - Feature ticket tracking (approved/, done/)
- `docs/` - Documentation and guides
- `scripts/` - Utility scripts

## Important Constraints

1. **9:16 Aspect Ratio**: All images must be vertical format for short-form video
2. **5-Scene Minimum**: Scripts must have at least 5 scenes for proper story arc
3. **Hook First**: First scene MUST use a hook technique
4. **Audio Sync**: Video duration must match audio length exactly
5. **Character Consistency**: Main character description flows through all image prompts

## Deployment

The project includes Docker configuration (`docker/`) and is designed for Cloud Run deployment. Health check endpoint validates critical dependencies and API key configuration.
