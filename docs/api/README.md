# API Documentation

## Overview

The `src/api/` directory contains the FastAPI application that exposes HTTP endpoints for the ShortFactory platform. The API follows REST principles and provides endpoints for story generation, script writing, and development tools.

## Architecture

```
src/api/
├── main.py              # FastAPI app initialization
├── error_handling.py    # Error handling decorators
├── mock_data.py         # Mock data for fallback/testing
├── routes/              # API route handlers
│   ├── stories.py       # Story generation endpoints
│   ├── scripts.py       # Script generation endpoints
│   └── dev.py           # Dev Mode endpoints
└── schemas/             # Request/response models
    ├── stories.py
    ├── scripts.py
    └── dev.py
```

## File Inventory

### Core Files

#### `main.py`
**Purpose**: FastAPI application initialization and configuration

**Key Components**:
- FastAPI app instance with metadata
- CORS middleware configuration
- Health check endpoint
- Static file serving for generated assets
- Router registration

**Startup Flow**:
1. Create FastAPI app
2. Add CORS middleware
3. Register health check
4. Mount static files (`/generated_assets`)
5. Include routers (stories, scripts, dev)
6. Start Uvicorn server on port 8001

#### `error_handling.py`
**Purpose**: Centralized error handling with fallback support

**Decorators**:
1. `@with_fallback(mock_data_fn)` - Catches errors and returns mock data
2. `@strict_error_handling` - Raises HTTP exceptions without fallback

**Design Pattern**: Decorator pattern for consistent error handling across routes

#### `mock_data.py`
**Purpose**: Provides mock data for testing and fallback scenarios

**Functions**:
- `get_mock_stories(request)` - Returns mock story ideas
- `get_mock_script(request)` - Returns mock video script

### Routes

#### `routes/stories.py`
**Endpoints**:
- `POST /api/stories/generate` - Generate story ideas

**Request**:
```json
{
  "topic": "coffee",
  "mood": "Fun",
  "category": "Real Story"
}
```

**Response**:
```json
[
  {
    "title": "The Coffee Revolution",
    "premise": "A story about...",
    "genre": "Documentary",
    "target_audience": "General Audience",
    "estimated_duration": "60s"
  }
]
```

#### `routes/scripts.py`
**Endpoints**:
- `POST /api/scripts/generate` - Generate video script from story

**Request**:
```json
{
  "story_title": "The Coffee Revolution",
  "story_premise": "A story about...",
  "story_genre": "Documentary",
  "story_audience": "General Audience",
  "duration": "60s"
}
```

**Response**:
```json
{
  "script": {
    "title": "The Coffee Revolution",
    "category": "Educational",
    "scenes": [
      {
        "scene_number": 1,
        "scene_title": "hook",
        "image_create_prompt": "...",
        "image_style": "cinematic",
        "dialogue": "Welcome to...",
        "voice_tone": "enthusiastic"
      }
    ]
  }
}
```

#### `routes/dev.py`
**Endpoints**:
- `POST /api/dev/generate-image` - Generate single image (Dev Mode)
- `POST /api/dev/generate-video` - Generate video (Dev Mode)

**Image Generation Request**:
```json
{
  "prompt": "A cinematic coffee shop",
  "style": "Cinematic"
}
```

**Video Generation Request**:
```json
{
  "mode": "text_to_video",
  "prompt": "A coffee brewing process",
  "image_path": null
}
```

## Error Handling Strategy

### Two-Tier Approach

1. **Production Endpoints** (`@with_fallback`):
   - Catch all exceptions
   - Log errors with full context
   - Return mock data as fallback
   - Ensure API never returns 500 errors

2. **Strict Endpoints** (`@strict_error_handling`):
   - Validate inputs (400 for bad requests)
   - Return 500 for server errors
   - No fallback to mock data

### Example Usage

```python
from src.api.error_handling import with_fallback
from src.api.mock_data import get_mock_stories

@router.post("/generate")
@with_fallback(lambda req: get_mock_stories(req))
async def generate_stories(request: StoryRequest):
    agent = StoryFinderAgent()
    result = agent.find_stories(request.topic)
    return result
```

### Error Flow

```
Request → Endpoint → Agent → LLM
                ↓ (error)
            Log Error
                ↓
         Return Mock Data
```

## Configuration

### Environment Variables

```bash
# Server
PORT=8001                    # API server port

# CORS
CORS_ORIGINS=*              # Allowed origins (use specific in prod)

# Paths
GENERATED_ASSETS_DIR=./generated_assets  # Static file directory
```

### Static Files

Generated assets are served at `/generated_assets/`:
- Images: `/generated_assets/images/scene_1_abc123.png`
- Videos: `/generated_assets/videos/text_gen_xyz789.mp4`

## Health Check

### Endpoint: `GET /health`

**Purpose**: Verify API and dependencies are healthy

**Response (Healthy)**:
```json
{
  "status": "healthy",
  "services": {
    "storage": "ok"
  }
}
```

**Response (Unhealthy)**:
```json
{
  "status": "unhealthy",
  "errors": ["GEMINI_API_KEY not set"],
  "services": {
    "storage": "ok"
  }
}
```

**HTTP Status**:
- 200: Healthy
- 503: Unhealthy

## Request/Response Schemas

### Pydantic Models

All requests and responses use Pydantic models for validation:

```python
from pydantic import BaseModel, Field

class StoryRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
    mood: str = "Neutral"
    category: str = "General"
```

**Benefits**:
- Automatic validation
- Type safety
- API documentation (OpenAPI/Swagger)
- Serialization/deserialization

## Common Tasks

### Adding a New Endpoint

1. **Create schema** in `schemas/`:
```python
# schemas/my_feature.py
class MyRequest(BaseModel):
    param: str

class MyResponse(BaseModel):
    result: str
```

2. **Create route** in `routes/`:
```python
# routes/my_feature.py
from fastapi import APIRouter
router = APIRouter()

@router.post("/action")
async def my_action(request: MyRequest) -> MyResponse:
    # implementation
    return MyResponse(result="success")
```

3. **Register router** in `main.py`:
```python
from src.api.routes import my_feature
app.include_router(my_feature.router, prefix="/api/my-feature", tags=["my-feature"])
```

### Testing Endpoints

#### Using curl

```bash
# Story generation
curl -X POST "http://localhost:8001/api/stories/generate" \
  -H "Content-Type: application/json" \
  -d '{"topic": "coffee", "mood": "Fun", "category": "Real Story"}'

# Script generation
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

#### Using Python requests

```python
import requests

response = requests.post(
    "http://localhost:8001/api/stories/generate",
    json={"topic": "coffee", "mood": "Fun", "category": "Real Story"}
)
print(response.json())
```

### Modifying Error Handling

To change fallback behavior:

```python
# Option 1: Custom fallback function
def my_fallback(request):
    return {"custom": "fallback"}

@with_fallback(my_fallback)
async def my_endpoint(request):
    # implementation
    pass

# Option 2: No fallback (strict mode)
@strict_error_handling
async def my_endpoint(request):
    # implementation - will raise HTTPException on error
    pass
```

## CORS Configuration

### Development

```python
allow_origins=["*"]  # Allow all origins
```

### Production

```python
allow_origins=[
    "https://shortfactory.com",
    "https://www.shortfactory.com"
]
```

## API Documentation

FastAPI automatically generates interactive API docs:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **OpenAPI JSON**: http://localhost:8001/openapi.json

## Performance Considerations

### 1. Async Endpoints

All endpoints are async for better concurrency:

```python
async def my_endpoint(request):
    result = await some_async_operation()
    return result
```

### 2. Background Tasks

For long-running operations, consider background tasks:

```python
from fastapi import BackgroundTasks

@router.post("/generate")
async def generate(request: Request, background_tasks: BackgroundTasks):
    background_tasks.add_task(long_running_task, request)
    return {"status": "processing"}
```

### 3. Caching

Consider adding caching for expensive operations:

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_operation(param: str):
    # cached result
    pass
```

## Security Considerations

### 1. Input Validation

All inputs are validated via Pydantic:

```python
class Request(BaseModel):
    topic: str = Field(..., min_length=1, max_length=500)
```

### 2. Rate Limiting

**TODO**: Implement rate limiting for production:

```python
from slowapi import Limiter

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/stories/generate")
@limiter.limit("10/minute")
async def generate_stories(request):
    pass
```

### 3. API Keys

**TODO**: Add API key authentication for production:

```python
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403)
```

## Gotchas and Notes

### 1. Async vs Sync Agents

⚠️ **Important**: Mix async and sync carefully:

```python
# ImageGenAgent is async
@router.post("/generate-image")
async def generate_image(request):
    agent = ImageGenAgent()
    result = await agent.generate_images(scenes)  # await required
    return result

# StoryFinderAgent is sync
@router.post("/generate-stories")
async def generate_stories(request):
    agent = StoryFinderAgent()
    result = agent.find_stories(topic)  # no await
    return result
```

### 2. Static File Paths

Static files must use `/generated_assets/` prefix:

```python
# Correct
video_url = "/generated_assets/videos/video.mp4"

# Wrong
video_url = "/assets/videos/video.mp4"  # 404 error
```

### 3. Error Decorator Order

Decorators are applied bottom-up:

```python
@router.post("/endpoint")
@with_fallback(mock_fn)  # Applied second
async def my_endpoint():  # Applied first
    pass
```

### 4. Request Body Size

FastAPI has default limits. For large files, increase:

```python
app = FastAPI(
    max_request_size=10 * 1024 * 1024  # 10MB
)
```

## Dependencies

### External Libraries

- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation
- `python-multipart` - Form data support

### Internal Dependencies

- `src/agents/*` - Agent implementations
- `src/core/config` - Configuration
- `src/models/models` - Shared data models

## Migration Notes

### Recent Changes

1. **Error Handling Fix** (2025-01): Removed `extra` parameter from logging in `error_handling.py`
2. **Dev Mode Routes** (2025-01): Added `/api/dev/generate-image` and `/api/dev/generate-video`
3. **Static Files** (2025-01): Changed path from `/assets` to `/generated_assets`

---

**Last Updated**: 2025-01-21
**Version**: 1.0
