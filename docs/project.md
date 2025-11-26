# ShortFactory Project Overview

**Last Updated:** 2025-11-25  
**Version:** 2.0  
**Status:** Active Development

---

## Table of Contents

1. [What is ShortFactory?](#what-is-shortfactory)
2. [System Architecture](#system-architecture)
3. [Project Structure](#project-structure)
4. [Core Components](#core-components)
5. [Data Flow](#data-flow)
6. [Getting Started](#getting-started)
7. [Development Workflow](#development-workflow)
8. [Key Technical Decisions](#key-technical-decisions)
9. [Technology Stack](#technology-stack)
10. [Cross-Cutting Concerns](#cross-cutting-concerns)
11. [Module Dependencies](#module-dependencies)
12. [Navigation Guide](#navigation-guide)
13. [Current Status & Roadmap](#current-status--roadmap)

---

## What is ShortFactory?

ShortFactory is an **AI-powered platform for generating professional short-form video content** (YouTube Shorts, TikTok, Instagram Reels). It uses a multi-agent AI architecture to automate the entire video creation pipeline: from story ideation to script writing, cinematic direction, image generation, voice synthesis, and final video assembly.

### Target Users

- **Content Creators**: YouTubers, TikTokers, Instagram creators
- **Marketers**: Social media managers, brand marketers
- **Educators**: Teachers, course creators
- **Storytellers**: Anyone who wants to create engaging short videos quickly

### Key Capabilities

1. **Story Generation**: Generate creative story ideas from topics using LLM
2. **Script Writing**: Transform stories into structured video scripts with scenes
3. **Cinematic Direction**: Add professional shot types, camera movements, and visual coherence
4. **Image Generation**: Generate AI images for each scene using Gemini Imagen or NanoBanana
5. **Voice Synthesis**: Create natural voiceovers using ElevenLabs
6. **Video Assembly**: Combine all assets into final video with effects and transitions
7. **Scene Editing**: Edit individual scenes, regenerate images/audio
8. **Workflow Resumability**: Resume failed workflows from last checkpoint

### What Makes It Unique?

- **Cinematic Quality**: Uses professional cinematography language (shot types, camera angles, lighting)
- **Visual Coherence**: Director Agent ensures visual continuity between scenes
- **Dual-Mode Architecture**: Works with real AI services or mock data for development
- **Resumable Workflows**: Automatically saves progress and can resume after failures
- **Developer-Friendly**: Comprehensive dev mode for testing individual components

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│                    http://localhost:3000                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dev Mode    │  │  Production  │  │Scene Editor  │      │
│  │  Dashboard   │  │     UI       │  │     UI       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│                    http://localhost:8001                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   /stories   │  │   /scripts   │  │   /videos    │      │
│  │   /dev       │  │/scene-editor │  │   /health    │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                        Agent Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │StoryFinder   │→ │ScriptWriter  │→ │  Director    │      │
│  │   Agent      │  │    Agent     │  │   Agent      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                            ↓                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  ImageGen    │  │    Voice     │  │  VideoGen    │      │
│  │   Agent      │  │    Agent     │  │   Agent      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                            ↓                                 │
│  ┌──────────────────────────────────────────────────┐       │
│  │           VideoAssembly Agent                     │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                      Core Services                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │Configuration │  │   Logging    │  │  Workflow    │      │
│  │   (config)   │  │ (structlog)  │  │    State     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Gemini     │  │Gemini Imagen │  │  ElevenLabs  │      │
│  │     LLM      │  │  /NanoBanana │  │    Voice     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Agent Pipeline Flow

```
Story Finder → Script Writer → Director → Image Gen → Voice Gen → Video Gen → Video Assembly
                                             ↓           ↓           ↓
                                         (parallel)  (parallel)  (optional)
```

---

## Project Structure

```
ShortFactoryLangChain/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   │   ├── page.tsx     # Main production UI
│   │   │   └── dev/         # Dev mode dashboard
│   │   └── components/      # React components
│   │       ├── DevDashboard.tsx
│   │       └── SceneEditor.tsx
│   └── package.json
│
├── src/                     # Python backend
│   ├── agents/              # AI agent implementations ⭐
│   │   ├── director/        # Cinematic direction
│   │   │   ├── agent.py
│   │   │   ├── models.py
│   │   │   └── cinematic_language.py
│   │   ├── story_finder/    # Story generation
│   │   ├── script_writer/   # Script writing
│   │   ├── image_gen/       # Image generation
│   │   │   ├── agent.py
│   │   │   ├── gemini_image_client.py
│   │   │   └── nanobanana_client.py
│   │   ├── voice/           # Voice synthesis
│   │   │   ├── agent.py
│   │   │   └── elevenlabs_client.py
│   │   ├── video_gen/       # AI video generation
│   │   │   ├── agent.py
│   │   │   └── providers/
│   │   └── video_assembly/  # Final video assembly
│   │       └── agent.py
│   │
│   ├── api/                 # FastAPI application ⭐
│   │   ├── routes/          # API endpoints
│   │   │   ├── stories.py
│   │   │   ├── scripts.py
│   │   │   ├── videos.py
│   │   │   ├── scene_editor.py
│   │   │   └── dev.py
│   │   ├── schemas/         # Request/response models
│   │   ├── main.py          # App initialization
│   │   ├── error_handling.py # Error decorators
│   │   └── mock_data.py     # Mock data for testing
│   │
│   ├── core/                # Core infrastructure ⭐
│   │   ├── config.py        # Settings management
│   │   ├── logging.py       # Structured logging
│   │   ├── workflow_state.py # Workflow state management
│   │   └── utils.py         # Utility functions
│   │
│   ├── models/              # Data models ⭐
│   │   └── models.py        # Pydantic models (Scene, VideoScript, etc.)
│   │
│   └── utils/               # Shared utilities
│
├── docs/                    # Documentation ⭐
│   ├── agents/              # Agent documentation
│   │   └── README.md
│   ├── api/                 # API documentation
│   │   └── README.md
│   ├── core/                # Core documentation
│   │   └── README.md
│   ├── models/              # Data model documentation
│   │   └── README.md
│   ├── project.md           # This file
│   ├── DEVELOPER_GUIDE.md   # Developer guide
│   └── DEPLOYMENT.md        # Deployment guide
│
├── tests/                   # Test suite
│   ├── unit/                # Unit tests
│   └── integration/         # Integration tests
│
├── generated_assets/        # Output directory
│   ├── images/              # Generated images
│   ├── audio/               # Generated audio
│   ├── videos/              # Generated videos
│   └── workflows/           # Workflow state files
│       └── workflow_123/
│           ├── state.json
│           ├── script.json
│           ├── images/
│           ├── audio/
│           └── final_video.mp4
│
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── start_dev.sh            # Development startup script
└── README.md               # Project README
```

---

## Core Components

### 1. Agents (`src/agents/`) ⭐

**Responsibility**: Specialized AI agents for different stages of video generation.

#### Director Agent (`director/`)

**Purpose**: Transforms scripts into cinematically directed shot lists with professional visual coherence.

**Key Features**:
- Analyzes scripts and identifies narrative beats (Hook, Setup, Development, Resolution)
- Maps emotional arc through the video
- Generates cinematic direction using professional cinematography language
- Ensures visual continuity between scenes
- Recommends AI video vs. image+effect for each scene

**Cinematic Language**:
- **Shot Types**: extreme_wide, wide, medium, close_up, extreme_close_up
- **Camera Movements**: static, slow_push_in, pan_left, dolly_zoom, crane_up, orbit
- **Camera Angles**: eye_level, low, high, dutch, overhead
- **Lighting Moods**: bright, dramatic, soft, golden_hour, chiaroscuro
- **Composition Rules**: rule_of_thirds, symmetry, leading_lines, negative_space

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

**Documentation**: [docs/agents/README.md](agents/README.md#1-director-agent-director)

#### Story Finder Agent (`story_finder/`)

**Purpose**: Discovers interesting stories from Reddit or generates story ideas from topics.

**Key Features**:
- Dynamic routing based on category (News, History, Tutorial, Fiction)
- Web search integration using Tavily API for real-time data
- Structured output with title, hook, summary, and keywords

**Documentation**: [docs/agents/README.md](agents/README.md#2-story-finder-agent-story_finder)

#### Script Writer Agent (`script_writer/`)

**Purpose**: Transforms stories into structured video scripts with scenes and dialogue.

**Key Features**:
- Breaks stories into scenes with narrative structure
- Generates dialogue optimized for short-form video
- Creates detailed image and video generation prompts
- Extensive prompt engineering (~28KB of prompts)

**Scene Types**:
- `HOOK`: Grab attention in first 3 seconds
- `EXPLANATION`: Provide context and background
- `VISUAL_DEMO`: Show visual examples
- `COMPARISON`: Compare/contrast elements
- `CONCLUSION`: Wrap up and provide closure

**Documentation**: [docs/agents/README.md](agents/README.md#3-script-writer-agent-script_writer)

#### Image Generation Agent (`image_gen/`)

**Purpose**: Orchestrates image generation using multiple providers.

**Key Features**:
- Multi-provider support (Gemini Imagen, NanoBanana)
- Retry logic with exponential backoff
- Provider fallback on failure
- Rate limiting protection with delays between scenes

**Providers**:
- **Gemini Imagen**: Primary provider, high quality
- **NanoBanana**: Fallback provider, faster generation

**Documentation**: [docs/agents/README.md](agents/README.md#4-image-generation-agent-image_gen)

#### Voice Generation Agent (`voice/`)

**Purpose**: Synthesizes voiceover audio using ElevenLabs.

**Key Features**:
- Multiple voice profiles
- Tone-based voice settings (excited, calm, dramatic, etc.)
- Configurable speech rate and pitch

**Documentation**: [docs/agents/README.md](agents/README.md#5-voice-generation-agent-voice)

#### Video Generation Agent (`video_gen/`)

**Purpose**: Generates AI video for complex scenes that need motion.

**Key Features**:
- Multi-provider support (Luma, Runway, etc.)
- Async job polling for long-running generations
- Used selectively for high-importance scenes

**When Used**:
- High importance scenes (video_importance >= 9)
- Complex camera movements (dolly zoom, crane, orbit)
- Scenes marked as `needs_animation`

**Documentation**: [docs/agents/README.md](agents/README.md#6-video-generation-agent-video_gen)

#### Video Assembly Agent (`video_assembly/`)

**Purpose**: Combines all assets into final video with effects and transitions.

**Key Features**:
- Applies camera movements and effects to images
- Adds transitions between scenes
- Synchronizes audio with visuals
- Adds title card at beginning

**Effects Supported**:
- Ken Burns (zoom in/out)
- Pan (left/right)
- Tilt (up/down)
- Shake (handheld effect)
- Dolly zoom, crane movements

**Output**: MP4 video, 9:16 aspect ratio, 30fps, 44.1kHz stereo audio

**Documentation**: [docs/agents/README.md](agents/README.md#7-video-assembly-agent-video_assembly)

---

### 2. API (`src/api/`) ⭐

**Responsibility**: FastAPI-based REST API serving as interface between frontend and agents.

**Key Routes**:

- **POST `/api/stories/generate`**: Generate story ideas
- **POST `/api/scripts/generate`**: Generate video script
- **POST `/api/videos/generate`**: Generate complete video
- **GET `/api/videos/{video_id}`**: Retrieve video metadata
- **PUT `/api/scene-editor/scenes/{scene_id}`**: Update scene
- **POST `/api/scene-editor/scenes/{scene_id}/regenerate-image`**: Regenerate scene image
- **GET `/api/dev/config`**: View configuration (dev mode)
- **GET `/health`**: Health check endpoint

**Key Features**:
- Error handling with fallback to mock data
- CORS support for frontend integration
- Request validation using Pydantic schemas
- Structured logging with correlation IDs
- Long timeouts for video generation (10 minutes)
- Static file serving for generated assets

**Documentation**: [docs/api/README.md](api/README.md)

---

### 3. Core (`src/core/`) ⭐

**Responsibility**: Fundamental infrastructure components.

#### Configuration (`config.py`)

**Purpose**: Centralized settings management using Pydantic.

**Key Settings**:
- **Feature Flags**: `USE_REAL_LLM`, `USE_REAL_IMAGE`, `USE_REAL_VOICE`
- **Development Mode**: `DEV_MODE`, `FAIL_FAST`
- **API Keys**: `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`, etc.
- **Scene Constraints**: `MIN_SCENES`, `MAX_SCENES`
- **Video Settings**: `VIDEO_RESOLUTION`, `VIDEO_FPS`, `VIDEO_QUALITY`
- **Retry Settings**: `IMAGE_GENERATION_MAX_RETRIES`, `IMAGE_GENERATION_RETRY_DELAYS`

**Example**:
```python
from src.core.config import settings

if settings.USE_REAL_LLM:
    # Use real Gemini
    llm = ChatGoogleGenerativeAI(api_key=settings.GEMINI_API_KEY)
else:
    # Use mock data
    return get_mock_data()
```

#### Logging (`logging.py`)

**Purpose**: Structured logging using structlog.

**Features**:
- JSON-formatted logs
- Automatic context injection
- Correlation IDs for request tracing
- Exception information with stack traces

**Example**:
```python
import structlog

logger = structlog.get_logger()
logger.info("Processing request", workflow_id="123", scene_count=8)
```

#### Workflow State Management (`workflow_state.py`)

**Purpose**: Track progress of video generation workflows and enable resume functionality.

**Key Classes**:
- `WorkflowState`: Represents workflow state
- `WorkflowStateManager`: Manages state persistence
- `WorkflowStep`: Enum of workflow steps
- `WorkflowStatus`: Enum of workflow statuses

**Workflow Steps**:
1. `SCRIPT_GENERATION`
2. `IMAGE_GENERATION`
3. `AUDIO_GENERATION`
4. `VIDEO_ASSEMBLY`

**Features**:
- Saves state after each step
- Tracks completed scenes (images, audio)
- Stores error information on failure
- Enables resume from last checkpoint

**Example**:
```python
from src.core.workflow_state import workflow_manager, WorkflowStep

# Create workflow
state = workflow_manager.create_workflow(
    workflow_id="workflow_123",
    topic="AI and the future"
)

# Update step
workflow_manager.update_step(
    workflow_id="workflow_123",
    step=WorkflowStep.IMAGE_GENERATION
)

# Save image (incremental)
workflow_manager.save_image(
    workflow_id="workflow_123",
    scene_number=1,
    image_path="path/to/image.png"
)

# Resume on failure
state = workflow_manager.load_state("workflow_123")
if state.status == WorkflowStatus.FAILED:
    # Resume from failed step
    # Skip already completed scenes
    pass
```

**Documentation**: [docs/core/README.md](core/README.md)

---

### 4. Data Models (`src/models/`) ⭐

**Responsibility**: Type-safe data structures using Pydantic.

**Key Models**:

#### Scene

Represents a single scene in the video.

```python
class Scene(BaseModel):
    scene_number: int
    scene_type: SceneType  # HOOK, EXPLANATION, VISUAL_DEMO, etc.
    content: List[VisualSegment]  # Multiple images per scene
    voice_tone: VoiceTone  # EXCITED, CALM, DRAMATIC, etc.
    image_style: ImageStyle  # INFOGRAPHIC, ACTION_SCENE, etc.
    needs_animation: bool
    video_prompt: Optional[str]
    video_importance: int  # 1-10
```

#### VideoScript

Complete video script with all scenes.

```python
class VideoScript(BaseModel):
    title: str
    main_character_description: str
    scenes: List[Scene]
    transitions: List[TransitionType]
    estimated_duration: Optional[float]
```

**Enumerations**:
- `SceneType`: HOOK, EXPLANATION, VISUAL_DEMO, COMPARISON, CONCLUSION
- `VoiceTone`: EXCITED, CALM, DRAMATIC, MYSTERIOUS, etc.
- `ImageStyle`: INFOGRAPHIC, ACTION_SCENE, CLOSE_UP_REACTION, etc.
- `TransitionType`: FADE, SLIDE_LEFT, ZOOM_IN, DISSOLVE, etc.

**Documentation**: [docs/models/README.md](models/README.md)

---

### 5. Frontend (`frontend/`)

**Responsibility**: User interface for video generation.

**Key Components**:
- **DevDashboard**: Development testing interface for individual agents
- **Production UI**: Main video generation interface
- **SceneEditor**: Edit individual scenes, regenerate assets

**Technology**: Next.js 16 (App Router), TypeScript, Tailwind CSS

---

## Data Flow

### Complete Video Generation Flow

```
1. User Input (topic/story)
        ↓
2. Story Finder Agent
   - Generate story ideas
   - Return story list
        ↓
3. Script Writer Agent
   - Transform story into script
   - Create scenes with dialogue
   - Generate image/video prompts
        ↓
4. Director Agent
   - Analyze script narrative
   - Map emotional arc
   - Add cinematic direction
   - Ensure visual continuity
        ↓
5. Image Generation (Parallel)
   - For each scene:
     * Generate image from enhanced prompt
     * Save to workflow state
     * Apply retry logic if needed
        ↓
6. Voice Generation (Parallel)
   - For each scene:
     * Synthesize voiceover from dialogue
     * Apply tone-based settings
     * Save to workflow state
        ↓
7. Video Generation (Optional, Selective)
   - For high-importance scenes:
     * Generate AI video
     * Save to workflow state
        ↓
8. Video Assembly
   - Combine all assets
   - Apply effects and transitions
   - Sync audio with visuals
   - Add title card
   - Export final video
        ↓
9. Final Video (MP4, 9:16, 30fps)
```

### Workflow State Persistence

At each step, the workflow state is saved:

```json
{
  "workflow_id": "workflow_123",
  "status": "in_progress",
  "current_step": "image_generation",
  "completed_steps": ["script_generation"],
  "script_path": "path/to/script.json",
  "image_paths": {
    "1": "path/to/scene_1.png",
    "2": "path/to/scene_2.png"
  },
  "audio_paths": {
    "1": "path/to/scene_1.mp3"
  },
  "images_completed": 2,
  "audio_completed": 1,
  "total_scenes": 8
}
```

If a failure occurs, the workflow can resume from the last checkpoint, skipping already completed scenes.

---

## Getting Started

### Prerequisites

- **Python 3.12+**
- **Node.js 18+**
- **API Keys** (for real mode):
  - Gemini API key (required for LLM and image generation)
  - ElevenLabs API key (required for voice synthesis)
  - Luma API key (optional, for AI video generation)

### Installation

1. **Clone repository**:
```bash
git clone https://github.com/yourusername/ShortFactoryLangChain.git
cd ShortFactoryLangChain
```

2. **Set up Python environment**:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Set up frontend**:
```bash
cd frontend
npm install
cd ..
```

4. **Configure environment**:
```bash
cp .env.example .env
# Edit .env with your API keys
```

Example `.env`:
```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

# Feature Flags
USE_REAL_LLM=true
USE_REAL_IMAGE=true
USE_REAL_VOICE=true

# Development Mode
DEV_MODE=true
FAIL_FAST=true

# Application Settings
MIN_SCENES=4
MAX_SCENES=15
VIDEO_RESOLUTION=1080p
```

5. **Start development environment**:
```bash
./start_dev.sh
```

6. **Access the application**:
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8001
- **API Docs**: http://localhost:8001/docs

### Quick Start Example

```bash
# Generate stories
curl -X POST "http://localhost:8001/api/stories/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "artificial intelligence", "category": "technology", "mood": "mysterious"}'

# Generate script
curl -X POST "http://localhost:8001/api/scripts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The AI That Learned to Dream",
    "premise": "A breakthrough AI begins experiencing dreams...",
    "style": "dramatic",
    "duration": 60
  }'

# Generate complete video
curl -X POST "http://localhost:8001/api/videos/generate" \
  -H "Content-Type: application/json" \
  -d @script.json
```

---

## Development Workflow

### Adding a New Feature

1. **Plan**: Create implementation plan or ticket
2. **Backend**: Add agent or API endpoint
3. **Frontend**: Add UI component
4. **Test**: Write unit and integration tests
5. **Document**: Update relevant documentation

### Testing Strategy

- **Mock Mode**: Test without API keys using `USE_REAL_LLM=false`
- **Unit Tests**: `pytest tests/unit/`
- **Integration Tests**: `pytest tests/integration/`
- **Manual Testing**: Use Dev Mode dashboard at http://localhost:3000/dev

### Common Development Tasks

| Task | Command |
|------|---------|
| Start dev environment | `./start_dev.sh` |
| Run all tests | `pytest tests/` |
| Run specific test | `pytest tests/unit/test_director_agent.py` |
| Check API docs | Open http://localhost:8001/docs |
| View logs | Check terminal output or use structlog |
| Clear generated assets | `rm -rf generated_assets/*` |
| Restart backend only | `python -m src.api.main` |
| Restart frontend only | `cd frontend && npm run dev` |

---

## Key Technical Decisions

### 1. Multi-Agent Architecture

**Decision**: Use specialized agents for each stage of video generation.

**Rationale**:
- **Separation of Concerns**: Each agent has a single, well-defined responsibility
- **Modularity**: Easy to replace or upgrade individual agents
- **Testability**: Can test each agent independently
- **Scalability**: Can run agents in parallel or distribute across services

### 2. Director Agent for Cinematic Quality

**Decision**: Add a dedicated Director Agent to analyze scripts and add professional cinematic direction.

**Rationale**:
- **Visual Quality**: Ensures professional-looking videos with proper shot composition
- **Visual Coherence**: Maintains visual continuity between scenes
- **Emotional Impact**: Maps emotional arc and uses appropriate visual language
- **Differentiation**: Sets ShortFactory apart from simple image-to-video tools

### 3. Dual-Mode Architecture (Real vs Mock)

**Decision**: Support both real AI services and mock data modes.

**Rationale**:
- **Cost Efficiency**: Develop and test without expensive API calls
- **Faster Development**: Mock mode is instant, no waiting for API responses
- **Graceful Degradation**: Can fall back to mock data if API fails
- **Onboarding**: New developers can start without API keys

### 4. Workflow State Management

**Decision**: Persist workflow state at each step to enable resumability.

**Rationale**:
- **Reliability**: Can recover from failures without losing progress
- **Cost Savings**: Don't regenerate already completed assets
- **User Experience**: Users can see progress and resume failed workflows
- **Debugging**: Can inspect state to understand where failures occurred

### 5. LangChain Integration

**Decision**: Use LangChain for LLM orchestration.

**Rationale**:
- **Standardized Prompts**: Template-based prompt management
- **Built-in Retry Logic**: Automatic retry on transient failures
- **Output Parsing**: Parse LLM responses into Pydantic models
- **Provider Flexibility**: Easy to switch between LLM providers

### 6. FastAPI for Backend

**Decision**: Use FastAPI instead of Flask/Django.

**Rationale**:
- **Automatic API Documentation**: OpenAPI/Swagger docs generated automatically
- **Type Safety**: Pydantic integration for request/response validation
- **Async Support**: Better performance for I/O-bound operations
- **Modern Python**: Uses Python 3.6+ features (type hints, async/await)

### 7. Centralized Configuration

**Decision**: Single `Settings` class for all configuration.

**Rationale**:
- **Type Safety**: Pydantic validates all environment variables
- **Documentation**: Field descriptions document all settings
- **Testability**: Easy to override settings in tests
- **Single Source of Truth**: All configuration in one place

### 8. Structured Logging

**Decision**: Use structlog for JSON-formatted logs.

**Rationale**:
- **Parseable**: JSON logs easy to parse and analyze
- **Contextual**: Automatic context injection (timestamps, request IDs)
- **Searchable**: Easy to search and filter logs
- **Production-Ready**: Integrates with log aggregation tools

---

## Technology Stack

### Backend

- **Framework**: FastAPI 0.104+
- **LLM**: LangChain + Google Gemini 2.5 Flash
- **Validation**: Pydantic 2.0+
- **Server**: Uvicorn (ASGI)
- **Logging**: structlog
- **Video Processing**: MoviePy
- **Image Processing**: Pillow

### Frontend

- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **State Management**: React hooks

### External Services

- **LLM**: Google Gemini 2.5 Flash
- **Image Generation**: Gemini Imagen, NanoBanana
- **Voice Synthesis**: ElevenLabs
- **Video Generation**: Luma Dream Machine (optional)

### Development Tools

- **Testing**: pytest
- **Type Checking**: Pydantic (runtime), mypy (planned)
- **API Documentation**: FastAPI/Swagger
- **Version Control**: Git

---

## Cross-Cutting Concerns

### Error Handling

**Strategy**: Multi-level error handling with fallback mechanisms.

1. **Retry Logic**: Exponential backoff for transient failures
2. **Provider Fallback**: Switch to alternative services
3. **Graceful Degradation**: Use simpler approaches if advanced features fail
4. **Mock Data Fallback**: Return mock data if all else fails (dev mode)

**Example**:
```python
@with_fallback(lambda req: get_mock_data(req))
async def generate_content(request: Request):
    try:
        return await real_implementation(request)
    except Exception as e:
        logger.error("Failed", error=str(e), exc_info=True)
        # Falls back to mock data automatically
```

### Logging

**Format**: Structured JSON logs with context.

**Example**:
```json
{
  "event": "Workflow step completed",
  "level": "info",
  "timestamp": "2025-11-25T21:08:37Z",
  "workflow_id": "workflow_123",
  "step": "image_generation",
  "images_completed": 5,
  "total_scenes": 8
}
```

**Best Practices**:
- Use structured logging with key-value pairs
- Include context (workflow_id, scene_number, etc.)
- Log exceptions with stack traces (`exc_info=True`)
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)

### Security

**Current State**:
- API keys stored in environment variables
- No authentication/authorization implemented
- CORS allows all origins (development)
- Input validation via Pydantic

**Production Recommendations**:
1. **Add Authentication**: JWT tokens or API keys
2. **Rate Limiting**: Prevent abuse and manage costs
3. **CORS Configuration**: Restrict to specific domains
4. **Secret Management**: Use Google Cloud Secret Manager
5. **Input Sanitization**: Additional validation for sensitive fields

### Performance

**Optimizations**:
- **Parallel Processing**: Images and audio generated concurrently
- **Async/Await**: Non-blocking I/O for better throughput
- **Incremental State Saves**: Save progress after each scene
- **Provider Selection**: Choose fastest provider for each task

**Bottlenecks**:
- **LLM Calls**: Can take 5-10 seconds per call
- **Image Generation**: 10-30 seconds per image
- **Video Assembly**: 30-60 seconds for final video
- **Total Pipeline**: 5-10 minutes for complete video

---

## Module Dependencies

### External Dependencies

```
Backend:
├── fastapi (web framework)
├── langchain-google-genai (LLM)
├── pydantic (validation)
├── structlog (logging)
├── moviepy (video processing)
├── pillow (image processing)
├── elevenlabs (voice synthesis)
└── requests (HTTP client)

Frontend:
├── next (framework)
├── react (UI library)
├── typescript (type safety)
└── tailwindcss (styling)
```

### Internal Dependencies

```
Frontend
    ↓ HTTP/REST
API Layer (FastAPI)
    ↓
Agent Layer (Director, ScriptWriter, ImageGen, etc.)
    ↓
Core Services (Config, Logging, WorkflowState)
    ↓
Data Models (Pydantic)
```

**Dependency Graph**:
- **API** depends on **Agents**, **Core**, **Models**
- **Agents** depend on **Core**, **Models**
- **Core** depends on **Models** (for validation)
- **Models** has no dependencies (self-contained)

---

## Navigation Guide

### "I want to..."

| Goal | Look in | Documentation |
|------|---------|---------------|
| Add a new agent | `src/agents/` | [agents/README.md](agents/README.md) |
| Add an API endpoint | `src/api/routes/` | [api/README.md](api/README.md) |
| Change configuration | `src/core/config.py` | [core/README.md](core/README.md) |
| Modify data models | `src/models/models.py` | [models/README.md](models/README.md) |
| Add cinematic direction | `src/agents/director/cinematic_language.py` | [agents/README.md](agents/README.md#1-director-agent-director) |
| Test individual components | Dev Mode Dashboard | [dev-mode/README.md](dev-mode/README.md) |
| Understand error handling | `src/api/error_handling.py` | [api/README.md](api/README.md#3-error-handling-error_handlingpy) |
| Manage workflow state | `src/core/workflow_state.py` | [core/README.md](core/README.md#3-workflow-state-management-workflow_statepy) |
| Deploy to production | Docker + Cloud Run | [DEPLOYMENT.md](DEPLOYMENT.md) |
| Debug video generation | Check workflow state files | [core/README.md](core/README.md#workflow-state-management) |

---

## Current Status & Roadmap

### ✅ Completed

- ✅ Story generation (real LLM + mock)
- ✅ Script writing (real LLM + mock)
- ✅ **Director Agent with cinematic direction**
- ✅ Image generation (Gemini Imagen + NanoBanana)
- ✅ Voice synthesis (ElevenLabs)
- ✅ **Workflow state management and resumability**
- ✅ Video assembly with effects and transitions
- ✅ Scene editor for regenerating assets
- ✅ Dev Mode dashboard
- ✅ **Comprehensive documentation (agents, API, core, models)**

### 🚧 In Progress

- 🚧 AI video generation integration (Luma Dream Machine)
- 🚧 Production UI improvements
- 🚧 Integration tests for full pipeline

### 📋 Planned

- 📋 User authentication and accounts
- 📋 Cloud deployment (Google Cloud Run)
- 📋 Rate limiting and cost management
- 📋 Monitoring & analytics (Prometheus, Grafana)
- 📋 Video quality improvements (4K support)
- 📋 Custom voice profiles
- 📋 Multi-language support
- 📋 Video templates and presets
- 📋 Batch video generation
- 📋 Social media integration (auto-upload to YouTube, TikTok)

---

## Contributing

1. Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. Check existing documentation in `docs/`
3. Follow established patterns (see examples in each folder)
4. Write tests for new features
5. Update documentation for changes

---

## Support & Resources

- **Documentation**: `docs/` directory
  - [Agents](agents/README.md)
  - [API](api/README.md)
  - [Core](core/README.md)
  - [Models](models/README.md)
- **API Docs**: http://localhost:8001/docs
- **Dev Mode**: http://localhost:3000/dev
- **Issues**: GitHub Issues
- **Developer Guide**: [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)

---

**Last Updated**: 2025-11-25  
**Version**: 2.0  
**Status**: Active Development

**Major Updates in v2.0**:
- Added Director Agent for cinematic direction
- Implemented workflow state management and resumability
- Created comprehensive documentation for all major folders
- Improved error handling and retry logic
- Enhanced image generation with multiple providers
- Added scene editor functionality
