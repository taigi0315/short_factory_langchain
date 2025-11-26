# API Documentation

**Last Updated:** 2025-11-25  
**Version:** 1.0

## Overview

The `src/api/` directory contains the FastAPI-based REST API that serves as the interface between the frontend and the video generation pipeline. It provides endpoints for story generation, script creation, video generation, and development utilities.

### Purpose

This folder implements a production-ready REST API with:
- RESTful endpoints for all video generation stages
- Error handling and fallback mechanisms
- CORS support for frontend integration
- Health checks for deployment monitoring
- Static file serving for generated assets
- Request validation using Pydantic schemas

### When to Work Here

You'll work in this folder when:
- Adding new API endpoints
- Modifying request/response schemas
- Implementing new error handling strategies
- Adding middleware or authentication
- Debugging API-related issues
- Integrating new frontend features

---

## Architecture

The API follows a **layered architecture**:

```
Client Request
    ↓
FastAPI Router (routes/)
    ↓
Request Validation (schemas/)
    ↓
Agent Orchestration (agents/)
    ↓
Response Formatting (schemas/)
    ↓
Client Response
```

### Key Design Patterns

1. **Router-based Organization**: Endpoints grouped by resource type
2. **Schema Validation**: Pydantic models for request/response validation
3. **Error Handling Middleware**: Centralized exception handling
4. **Fallback Decorators**: Graceful degradation to mock data
5. **Static File Serving**: Direct access to generated assets

---

## File Inventory

### Root Files

| File | Purpose | Key Components |
|------|---------|----------------|
| `main.py` | FastAPI application setup | App initialization, middleware, exception handlers |
| `error_handling.py` | Error handling utilities | `with_fallback` decorator, error formatters |
| `mock_data.py` | Mock data for development | Mock stories, scripts, videos |

### Subdirectories

| Directory | Purpose | Files |
|-----------|---------|-------|
| `routes/` | API endpoint definitions | `stories.py`, `scripts.py`, `videos.py`, `dev.py`, `scene_editor.py` |
| `schemas/` | Request/response models | Pydantic schemas for validation |

---

## Key Components

### 1. FastAPI Application (`main.py`)

**Purpose**: Central application setup with middleware, exception handlers, and router registration.

**Key Features**:
```python
from fastapi import FastAPI
from src.api.main import app

# Application metadata
app = FastAPI(
    title="ShortFactory API",
    description="API for ShortFactoryLangChain video generation platform",
    version="1.0.0"
)
```

**Middleware Stack**:
1. **CorrelationIdMiddleware**: Adds unique request IDs for tracing
2. **CORSMiddleware**: Enables cross-origin requests from frontend

```python
app.add_middleware(CorrelationIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Exception Handlers**:
- `http_exception_handler`: Formats HTTP exceptions as JSON
- `validation_exception_handler`: Handles Pydantic validation errors
- `global_exception_handler`: Catches all unhandled exceptions

**Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    """Health check for Cloud Run deployment"""
    return {
        "status": "healthy",
        "services": {"storage": "ok"}
    }
```

**Static File Serving**:
```python
app.mount("/generated_assets", 
    StaticFiles(directory="generated_assets"), 
    name="generated_assets"
)
```

**Uvicorn Configuration**:
```python
# Long timeouts for video generation
config = Config(
    app="src.api.main:app",
    host="0.0.0.0",
    port=8001,
    reload=True,
    timeout_keep_alive=600,  # 10 minutes
    timeout_graceful_shutdown=600,  # 10 minutes
)
```

---

### 2. Routes

#### Stories Router (`routes/stories.py`)

**Purpose**: Story idea generation and discovery.

**Endpoints**:

**POST `/api/stories/generate`**
- **Description**: Generate story ideas based on topic, category, and mood
- **Request Body**:
  ```json
  {
    "topic": "artificial intelligence",
    "category": "technology",
    "mood": "mysterious"
  }
  ```
- **Response**:
  ```json
  [
    {
      "title": "The AI That Learned to Dream",
      "premise": "A breakthrough AI begins experiencing...",
      "genre": "technology • mysterious",
      "target_audience": "General",
      "estimated_duration": "30-60s"
    }
  ]
  ```
- **Fallback**: Returns mock stories if LLM unavailable

---

#### Scripts Router (`routes/scripts.py`)

**Purpose**: Script generation from story ideas.

**Endpoints**:

**POST `/api/scripts/generate`**
- **Description**: Generate video script from story premise
- **Request Body**:
  ```json
  {
    "title": "The AI That Learned to Dream",
    "premise": "A breakthrough AI begins experiencing...",
    "style": "dramatic",
    "duration": 60
  }
  ```
- **Response**: Complete `VideoScript` object with scenes
- **Fallback**: Returns mock script if LLM unavailable

---

#### Videos Router (`routes/videos.py`)

**Purpose**: Video generation and retrieval.

**Endpoints**:

**POST `/api/videos/generate`**
- **Description**: Generate complete video from script
- **Request Body**: `VideoScript` object
- **Response**:
  ```json
  {
    "video_id": "abc123",
    "status": "completed",
    "video_url": "/generated_assets/videos/abc123.mp4",
    "duration": 58.5,
    "scenes": 8
  }
  ```
- **Processing**: Orchestrates all agents (Director → Image Gen → Voice → Assembly)
- **Timeout**: 10 minutes (configured in Uvicorn)

**GET `/api/videos/{video_id}`**
- **Description**: Retrieve video metadata and status
- **Response**: Video information and download URL

---

#### Scene Editor Router (`routes/scene_editor.py`)

**Purpose**: Edit individual scenes in generated scripts.

**Endpoints**:

**PUT `/api/scene-editor/scenes/{scene_id}`**
- **Description**: Update scene content, prompts, or settings
- **Request Body**: Updated scene data
- **Response**: Updated scene object

**POST `/api/scene-editor/scenes/{scene_id}/regenerate-image`**
- **Description**: Regenerate image for a specific scene
- **Response**: New image URL

**POST `/api/scene-editor/scenes/{scene_id}/regenerate-audio`**
- **Description**: Regenerate audio for a specific scene
- **Response**: New audio URL

---

#### Dev Router (`routes/dev.py`)

**Purpose**: Development and debugging utilities.

**Endpoints**:

**GET `/api/dev/config`**
- **Description**: View current configuration settings
- **Response**: Settings object (sanitized API keys)

**POST `/api/dev/clear-cache`**
- **Description**: Clear generated assets cache
- **Response**: Success message

**GET `/api/dev/logs`**
- **Description**: Retrieve recent application logs
- **Response**: Log entries

---

### 3. Error Handling (`error_handling.py`)

**Purpose**: Centralized error handling with fallback mechanisms.

**Key Components**:

**`with_fallback` Decorator**:
```python
from src.api.error_handling import with_fallback

@router.post("/generate")
@with_fallback(lambda request: get_mock_data(request))
async def generate_content(request: Request):
    # Try real implementation
    return await real_implementation(request)
    # Falls back to mock data on error
```

**How It Works**:
1. Attempts to execute the wrapped function
2. If exception occurs, logs the error
3. Calls fallback function with original request
4. Returns fallback result
5. In DEV_MODE, re-raises exception after fallback

**Error Response Format**:
```json
{
  "detail": "Error description",
  "message": "Detailed error message (dev mode only)",
  "errors": [...]  // Validation errors if applicable
}
```

---

### 4. Mock Data (`mock_data.py`)

**Purpose**: Provides realistic mock data for development and testing.

**Available Mocks**:

**`get_mock_stories(request)`**:
```python
from src.api.mock_data import get_mock_stories

stories = get_mock_stories(request)
# Returns list of StoryIdeaResponse objects
```

**`get_mock_script(request)`**:
```python
from src.api.mock_data import get_mock_script

script = get_mock_script(request)
# Returns complete VideoScript object
```

**`get_mock_video(request)`**:
```python
from src.api.mock_data import get_mock_video

video = get_mock_video(request)
# Returns video metadata with placeholder URL
```

**Design Decisions**:
- Mock data matches production schema exactly
- Includes realistic content for UI testing
- Deterministic output for reproducible tests
- Covers edge cases (long titles, special characters, etc.)

---

### 5. Schemas (`schemas/`)

**Purpose**: Pydantic models for request/response validation.

**Key Schema Files**:

**`stories.py`**:
```python
from pydantic import BaseModel, Field

class StoryGenerationRequest(BaseModel):
    topic: str = Field(..., min_length=1, max_length=200)
    category: str = Field(default="general")
    mood: str = Field(default="neutral")

class StoryIdeaResponse(BaseModel):
    title: str
    premise: str
    genre: str
    target_audience: str
    estimated_duration: str
```

**`scripts.py`**:
```python
class ScriptGenerationRequest(BaseModel):
    title: str
    premise: str
    style: str = Field(default="engaging")
    duration: int = Field(default=60, ge=15, le=180)

class ScriptResponse(BaseModel):
    script_id: str
    title: str
    scenes: List[Scene]
    total_duration: float
```

**Validation Features**:
- Field constraints (min/max length, ranges)
- Type validation
- Default values
- Custom validators
- Nested models

---

## Implementation Details

### Request Flow

1. **Client sends request** → FastAPI receives HTTP request
2. **Middleware processing** → CORS, correlation ID added
3. **Schema validation** → Pydantic validates request body
4. **Router handling** → Appropriate endpoint function called
5. **Agent orchestration** → Agents process the request
6. **Response formatting** → Pydantic formats response
7. **Error handling** → Exceptions caught and formatted
8. **Client receives response** → JSON response sent

### Async/Await Pattern

All endpoints use async/await for non-blocking I/O:

```python
@router.post("/generate")
async def generate_content(request: Request):
    # Async agent calls
    result = await agent.process(request)
    return result
```

**Benefits**:
- Concurrent request handling
- Better resource utilization
- Improved throughput for I/O-bound operations

### CORS Configuration

Current configuration allows all origins (development):

```python
allow_origins=["*"]  # Replace in production
```

**Production Configuration**:
```python
allow_origins=[
    "https://your-frontend-domain.com",
    "https://www.your-frontend-domain.com"
]
```

### Static File Serving

Generated assets are served directly:

```python
app.mount("/generated_assets", 
    StaticFiles(directory="generated_assets"),
    name="generated_assets"
)
```

**URL Format**:
```
http://localhost:8001/generated_assets/images/scene_1.png
http://localhost:8001/generated_assets/audio/scene_1.mp3
http://localhost:8001/generated_assets/videos/final_video.mp4
```

---

## Dependencies

### External Libraries

- **fastapi**: Web framework
- **uvicorn**: ASGI server
- **pydantic**: Data validation
- **asgi-correlation-id**: Request tracing
- **python-multipart**: File upload support

### Internal Dependencies

- `src.core.config`: Configuration settings
- `src.core.logging`: Structured logging
- `src.agents.*`: Agent implementations
- `src.models.models`: Shared data models

### Environment Variables

See `src.core.config` for full list. Key variables:

```bash
# Server
PORT=8001

# Feature Flags
USE_REAL_LLM=true
USE_REAL_IMAGE=true
USE_REAL_VOICE=true
DEV_MODE=true

# API Keys
GEMINI_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
```

---

## Common Tasks

### Adding a New Endpoint

1. **Create/update router file** in `routes/`:
   ```python
   # routes/my_resource.py
   from fastapi import APIRouter
   
   router = APIRouter()
   
   @router.post("/action")
   async def perform_action(request: MyRequest):
       # Implementation
       return response
   ```

2. **Create schemas** in `schemas/`:
   ```python
   # schemas/my_resource.py
   from pydantic import BaseModel
   
   class MyRequest(BaseModel):
       field1: str
       field2: int
   
   class MyResponse(BaseModel):
       result: str
   ```

3. **Register router** in `main.py`:
   ```python
   from src.api.routes import my_resource
   
   app.include_router(
       my_resource.router,
       prefix="/api/my-resource",
       tags=["my-resource"]
   )
   ```

4. **Test endpoint**:
   ```bash
   curl -X POST http://localhost:8001/api/my-resource/action \
     -H "Content-Type: application/json" \
     -d '{"field1": "value", "field2": 42}'
   ```

### Adding Error Handling

1. **Use `with_fallback` decorator**:
   ```python
   @router.post("/generate")
   @with_fallback(lambda req: get_mock_data(req))
   async def generate(request: Request):
       # Implementation
       pass
   ```

2. **Or handle manually**:
   ```python
   from fastapi import HTTPException
   
   @router.post("/generate")
   async def generate(request: Request):
       try:
           result = await process(request)
           return result
       except ValueError as e:
           raise HTTPException(
               status_code=400,
               detail=str(e)
           )
   ```

### Testing Endpoints

1. **Unit tests** in `tests/unit/test_api.py`:
   ```python
   from fastapi.testclient import TestClient
   from src.api.main import app
   
   client = TestClient(app)
   
   def test_generate_stories():
       response = client.post(
           "/api/stories/generate",
           json={"topic": "AI", "category": "tech"}
       )
       assert response.status_code == 200
       assert len(response.json()) > 0
   ```

2. **Integration tests** with real agents:
   ```python
   @pytest.mark.integration
   async def test_full_pipeline():
       response = client.post("/api/videos/generate", json=script)
       assert response.status_code == 200
       assert "video_url" in response.json()
   ```

### Debugging API Issues

1. **Enable detailed logging**:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. **Check request/response in logs**:
   ```python
   logger.debug("Request received", request=request.dict())
   logger.debug("Response sent", response=response.dict())
   ```

3. **Use FastAPI docs**: Visit `http://localhost:8001/docs` for interactive API documentation

4. **Test with curl**:
   ```bash
   curl -v http://localhost:8001/api/stories/generate \
     -H "Content-Type: application/json" \
     -d '{"topic": "test"}'
   ```

---

## Gotchas and Notes

### Known Issues

1. **Long Request Timeouts**: Video generation can take 5-10 minutes. Ensure:
   - Uvicorn `timeout_keep_alive` is set to 600+ seconds
   - Frontend has appropriate timeout settings
   - Consider implementing async job queue for production

2. **CORS in Production**: Change `allow_origins=["*"]` to specific domains

3. **File Upload Limits**: Default limit is 100MB (configurable in settings)

4. **Static File Caching**: Browser may cache generated assets. Use cache-busting query params:
   ```
   /generated_assets/images/scene_1.png?v=123456
   ```

5. **Error Messages in Production**: Set `DEV_MODE=false` to hide detailed error messages

### Common Mistakes

1. **Forgetting async/await**:
   ```python
   # Wrong
   @router.post("/generate")
   def generate(request):  # Missing async
       result = agent.process(request)  # Missing await
   
   # Correct
   @router.post("/generate")
   async def generate(request):
       result = await agent.process(request)
   ```

2. **Not validating request data**:
   ```python
   # Wrong
   @router.post("/generate")
   async def generate(data: dict):  # No validation
   
   # Correct
   @router.post("/generate")
   async def generate(request: MyRequest):  # Pydantic validation
   ```

3. **Hardcoding URLs**:
   ```python
   # Wrong
   return {"video_url": "http://localhost:8001/video.mp4"}
   
   # Correct
   from fastapi import Request
   return {"video_url": f"{request.base_url}generated_assets/video.mp4"}
   ```

### Performance Considerations

1. **Concurrent Requests**: FastAPI handles concurrent requests well, but agents may have rate limits

2. **Memory Usage**: Video generation is memory-intensive. Monitor memory usage and implement cleanup

3. **Database Connections**: Use connection pooling if adding database support

4. **Caching**: Consider caching LLM responses for identical requests

---

## Security Considerations

### Current State

- No authentication/authorization implemented
- All endpoints are public
- API keys stored in environment variables
- CORS allows all origins

### Production Recommendations

1. **Add Authentication**:
   ```python
   from fastapi.security import HTTPBearer
   
   security = HTTPBearer()
   
   @router.post("/generate")
   async def generate(
       request: Request,
       token: str = Depends(security)
   ):
       # Verify token
       pass
   ```

2. **Rate Limiting**:
   ```python
   from slowapi import Limiter
   
   limiter = Limiter(key_func=get_remote_address)
   
   @router.post("/generate")
   @limiter.limit("5/minute")
   async def generate(request: Request):
       pass
   ```

3. **Input Sanitization**: Already handled by Pydantic, but add custom validators for sensitive fields

4. **HTTPS Only**: Configure reverse proxy (nginx) to enforce HTTPS

5. **API Key Rotation**: Implement key rotation strategy

---

## Deployment

### Local Development

```bash
# Start server
python -m src.api.main

# Or use uvicorn directly
uvicorn src.api.main:app --reload --port 8001
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

### Cloud Run Deployment

```yaml
# cloud-run.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: shortfactory-api
spec:
  template:
    spec:
      containers:
      - image: gcr.io/project/shortfactory-api
        env:
        - name: GEMINI_API_KEY
          valueFrom:
            secretKeyRef:
              name: gemini-api-key
              key: key
        resources:
          limits:
            memory: 2Gi
            cpu: 2
```

---

## Related Documentation

- [Agents Documentation](../agents/README.md) - Agent implementations
- [Core Documentation](../core/README.md) - Configuration and utilities
- [Models Documentation](../models/README.md) - Data models
- [Developer Guide](../DEVELOPER_GUIDE.md) - General development guide

---

## Future Improvements

1. **WebSocket Support**: Real-time progress updates for video generation
2. **Job Queue**: Async job processing with Celery/Redis
3. **Database Integration**: Store scripts, videos, and user data
4. **Authentication**: User accounts and API key management
5. **Rate Limiting**: Prevent abuse and manage costs
6. **Caching Layer**: Redis for LLM response caching
7. **GraphQL API**: Alternative to REST for complex queries
8. **API Versioning**: Support multiple API versions

---

**For questions or issues, see the main [Developer Guide](../DEVELOPER_GUIDE.md) or check existing tickets in `/tickets`.**
