# ShortFactory Project Overview

## What is ShortFactory?

ShortFactory is an AI-powered platform for generating short-form video content. It uses LLM agents to automate the entire video creation pipeline: from story ideation to script writing, image generation, and video assembly.

**Target Users**: Content creators, marketers, educators who need to produce engaging short videos quickly.

**Key Capabilities**:
- Generate creative story ideas from topics
- Write structured video scripts with scenes
- Generate AI images for each scene
- Assemble final videos (in development)
- Dev Mode for testing individual components

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Frontend (Next.js)                      │
│                    http://localhost:3000                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Dev Mode    │  │  Production  │  │   Future     │      │
│  │  Dashboard   │  │     UI       │  │   Features   │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │ HTTP/REST
┌─────────────────────────────────────────────────────────────┐
│                    Backend API (FastAPI)                     │
│                    http://localhost:8001                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   /stories   │  │   /scripts   │  │    /dev      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                        Agent Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │StoryFinder   │  │ScriptWriter  │  │  ImageGen    │      │
│  │   Agent      │  │    Agent     │  │   Agent      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  VideoGen    │  │    Voice     │  │VideoAssembly │      │
│  │   Agent      │  │    Agent     │  │    Agent     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────────┐
│                    External Services                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Gemini     │  │  NanoBanana  │  │  ElevenLabs  │      │
│  │     LLM      │  │    Images    │  │    Voice     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ShortFactoryLangChain/
├── frontend/                 # Next.js frontend application
│   ├── src/
│   │   ├── app/             # Next.js app router
│   │   └── components/      # React components (DevDashboard)
│   └── package.json
│
├── src/                     # Python backend
│   ├── agents/              # AI agent implementations
│   │   ├── story_finder/    # Story generation
│   │   ├── script_writer/   # Script writing
│   │   ├── image_gen/       # Image generation
│   │   ├── video_gen/       # Video generation (mock)
│   │   ├── voice/           # Voice synthesis (placeholder)
│   │   └── video_assembly/  # Video assembly (placeholder)
│   │
│   ├── api/                 # FastAPI application
│   │   ├── routes/          # API endpoints
│   │   ├── schemas/         # Request/response models
│   │   ├── main.py          # App initialization
│   │   ├── error_handling.py # Error decorators
│   │   └── mock_data.py     # Mock data for testing
│   │
│   ├── core/                # Core configuration
│   │   └── config.py        # Settings management
│   │
│   ├── models/              # Data models
│   │   └── models.py        # Pydantic models
│   │
│   └── prompts/             # LLM prompts (future)
│
├── docs/                    # Documentation
│   ├── agents/              # Agent documentation
│   ├── api/                 # API documentation
│   ├── core/                # Configuration docs
│   ├── models/              # Data model docs
│   ├── dev-mode/            # Dev Mode docs
│   ├── project.md           # This file
│   ├── DEVELOPER_GUIDE.md   # Developer guide
│   └── DEPLOYMENT.md        # Deployment guide
│
├── tests/                   # Test suite
│   └── integration/         # Integration tests
│
├── generated_assets/        # Output directory
│   ├── images/              # Generated images
│   └── videos/              # Generated videos
│
├── .env                     # Environment variables
├── requirements.txt         # Python dependencies
├── start_dev.sh            # Development startup script
└── README.md               # Project README
```

## Core Components

### 1. Agents (`src/agents/`)
**Responsibility**: Specialized AI agents for different tasks

**Key Agents**:
- **StoryFinderAgent**: Generates creative story ideas from topics using Gemini LLM
- **ScriptWriterAgent**: Converts stories into structured video scripts
- **ImageGenAgent**: Generates images for scenes using NanoBanana API
- **VideoGenAgent**: Creates video clips (currently mock implementation)

**Pattern**: All agents support dual-mode operation (real LLM vs mock data)

**Documentation**: [docs/agents/README.md](agents/README.md)

### 2. API (`src/api/`)
**Responsibility**: HTTP endpoints for frontend communication

**Key Routes**:
- `/api/stories/generate` - Story generation
- `/api/scripts/generate` - Script generation
- `/api/dev/*` - Dev Mode endpoints

**Pattern**: Error handling with fallback to mock data

**Documentation**: [docs/api/README.md](api/README.md)

### 3. Configuration (`src/core/`)
**Responsibility**: Centralized settings management

**Key Features**:
- Environment variable loading
- Feature flags (mock vs real mode)
- API key management

**Documentation**: [docs/core/README.md](core/README.md)

### 4. Data Models (`src/models/`)
**Responsibility**: Type-safe data structures

**Key Models**:
- `Scene` - Single video scene
- `VideoScript` - Complete script
- Enums for styles, tones, transitions

**Documentation**: [docs/models/README.md](models/README.md)

### 5. Frontend (`frontend/`)
**Responsibility**: User interface

**Key Components**:
- DevDashboard - Development testing interface
- Production UI (future)

**Documentation**: [docs/dev-mode/README.md](dev-mode/README.md)

## Data Flow

### Story Generation Flow

```
User Input (topic)
    ↓
POST /api/stories/generate
    ↓
StoryFinderAgent.find_stories()
    ↓
Gemini LLM (or mock data)
    ↓
StoryList (Pydantic model)
    ↓
JSON Response
```

### Script Generation Flow

```
Story Idea
    ↓
POST /api/scripts/generate
    ↓
ScriptWriterAgent.generate_script()
    ↓
Gemini LLM (or mock data)
    ↓
VideoScript with Scenes
    ↓
JSON Response
```

### Image Generation Flow

```
Scene List
    ↓
ImageGenAgent.generate_images()
    ↓
For each scene (parallel):
    - Enhance prompt
    - Check cache
    - Call NanoBanana API (or placeholder)
    - Download image
    ↓
Dict[scene_number -> image_path]
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js 18+
- API Keys (for real mode):
  - Gemini API key
  - NanoBanana API key (optional)

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

5. **Start development environment**:
```bash
./start_dev.sh
```

6. **Access the application**:
- Frontend: http://localhost:3000
- API: http://localhost:8001
- API Docs: http://localhost:8001/docs

### Quick Start Example

```bash
# Generate stories
curl -X POST "http://localhost:8001/api/stories/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "coffee", "mood": "Fun", "category": "Real Story"}'

# Generate script
curl -X POST "http://localhost:8001/api/scripts/generate" \
  -H "Content-Type: application/json" \
  -d '{
    "story_title": "Coffee Story",
    "story_premise": "A fun story about coffee",
    "story_genre": "Documentary",
    "story_audience": "General",
    "duration": "30s"
  }'
```

## Development Workflow

### Adding a New Feature

1. **Plan**: Create implementation plan
2. **Backend**: Add agent or API endpoint
3. **Frontend**: Add UI component
4. **Test**: Write integration tests
5. **Document**: Update relevant docs

### Testing Strategy

- **Mock Mode**: Test without API keys
- **Integration Tests**: `tests/integration/test_pipeline.py`
- **Manual Testing**: Use Dev Mode dashboard

### Common Development Tasks

| Task | Command |
|------|---------|
| Start dev environment | `./start_dev.sh` |
| Run tests | `pytest tests/` |
| Check API docs | Open http://localhost:8001/docs |
| View logs | Check terminal output |

## Key Technical Decisions

### 1. Dual-Mode Architecture
**Decision**: Support both real LLM and mock data modes

**Rationale**:
- Cost efficiency during development
- Faster testing without API calls
- Graceful degradation in production

### 2. LangChain Integration
**Decision**: Use LangChain for LLM orchestration

**Rationale**:
- Standardized prompt templates
- Built-in retry logic
- Output parsing to Pydantic models

### 3. FastAPI for Backend
**Decision**: Use FastAPI instead of Flask/Django

**Rationale**:
- Automatic API documentation
- Type safety with Pydantic
- Async support for better performance

### 4. Centralized Configuration
**Decision**: Single `Settings` class for all config

**Rationale**:
- Type-safe environment variables
- Easy to test with overrides
- Clear documentation of all settings

### 5. Error Handling with Fallback
**Decision**: Return mock data on errors instead of 500 responses

**Rationale**:
- Better user experience
- Allows testing without API keys
- Graceful degradation

## Technology Stack

### Backend
- **Framework**: FastAPI 0.104+
- **LLM**: LangChain + Google Gemini
- **Validation**: Pydantic 2.0+
- **Server**: Uvicorn (ASGI)

### Frontend
- **Framework**: Next.js 16 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS

### External Services
- **LLM**: Google Gemini 1.5 Flash
- **Images**: NanoBanana API
- **Voice**: ElevenLabs (planned)

### Development Tools
- **Testing**: pytest
- **Linting**: (to be added)
- **Type Checking**: mypy (to be added)

## Cross-Cutting Concerns

### Error Handling
- **Strategy**: Decorator-based error handling
- **Fallback**: Return mock data on errors
- **Logging**: Structured logging with request IDs

### Logging
- **Format**: `[request_id] Message`
- **Levels**: INFO for operations, ERROR for failures
- **Gotcha**: Don't use `extra={"args": ...}` (conflicts with LangChain)

### Security
- **API Keys**: Stored in `.env`, never committed
- **Input Validation**: Pydantic models validate all inputs
- **CORS**: Configured in FastAPI middleware

### Performance
- **Caching**: Image generation uses SHA256-based caching
- **Parallel Processing**: Images generated concurrently
- **Async**: API endpoints are async for better concurrency

## Module Dependencies

### External Dependencies
```
Backend:
├── fastapi (web framework)
├── langchain-google-genai (LLM)
├── pydantic (validation)
├── requests (HTTP client)
└── moviepy (video generation)

Frontend:
├── next (framework)
├── react (UI library)
└── typescript (type safety)
```

### Internal Dependencies
```
API Layer
    ↓
Agent Layer
    ↓
Core Configuration
    ↓
Data Models
```

## Navigation Guide

### "I want to..."

| Goal | Look in |
|------|---------|
| Add a new agent | `src/agents/` + [agents docs](agents/README.md) |
| Add an API endpoint | `src/api/routes/` + [API docs](api/README.md) |
| Change configuration | `src/core/config.py` + [core docs](core/README.md) |
| Modify data models | `src/models/models.py` + [models docs](models/README.md) |
| Test individual components | Dev Mode + [dev-mode docs](dev-mode/README.md) |
| Understand error handling | `src/api/error_handling.py` + [API docs](api/README.md) |
| Deploy to production | [DEPLOYMENT.md](DEPLOYMENT.md) |

## Current Status & Roadmap

### ✅ Completed
- Story generation (real LLM + mock)
- Script writing (real LLM + mock)
- Image generation (real API + mock)
- Video generation (mock only)
- Dev Mode dashboard
- Comprehensive documentation

### 🚧 In Progress
- Real video generation integration
- Voice synthesis integration

### 📋 Planned
- Video assembly pipeline
- Production UI
- User authentication
- Cloud deployment
- Rate limiting
- Monitoring & analytics

## Contributing

1. Read [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
2. Check existing documentation
3. Follow established patterns
4. Write tests
5. Update documentation

## Support & Resources

- **Documentation**: `docs/` directory
- **API Docs**: http://localhost:8001/docs
- **Issues**: GitHub Issues
- **Dev Mode**: http://localhost:3000

---

**Last Updated**: 2025-01-21
**Version**: 1.0
**Status**: Active Development
