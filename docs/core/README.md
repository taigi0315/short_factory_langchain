# Core Documentation

**Last Updated:** 2025-11-25  
**Version:** 1.0

## Overview

The `src/core/` directory contains fundamental infrastructure components that support the entire application. This includes configuration management, logging, utilities, and workflow state management.

### Purpose

This folder provides:
- **Centralized Configuration**: Single source of truth for all settings
- **Structured Logging**: Consistent logging across all components
- **Workflow State Management**: Track and resume video generation workflows
- **Utility Functions**: Common helper functions used throughout the app

### When to Work Here

You'll work in this folder when:
- Adding new configuration settings
- Modifying logging behavior
- Implementing workflow resumability features
- Adding shared utility functions
- Changing error handling strategies

---

## Architecture

The core module follows a **singleton pattern** for shared resources:

```
Application
    ↓
Core Module (Singleton Instances)
    ├── settings (Configuration)
    ├── logger (Structured Logging)
    ├── workflow_manager (State Management)
    └── utils (Helper Functions)
```

### Design Principles

1. **Single Source of Truth**: All configuration in one place
2. **Environment-based Config**: Use environment variables for deployment flexibility
3. **Structured Logging**: JSON-formatted logs for easy parsing
4. **Stateful Workflows**: Persist progress for resumability
5. **Type Safety**: Pydantic for validation and type checking

---

## File Inventory

| File | Purpose | Key Components |
|------|---------|----------------|
| `config.py` | Application configuration | `Settings` class, environment variables |
| `logging.py` | Logging configuration | `configure_logging()`, structlog setup |
| `workflow_state.py` | Workflow state management | `WorkflowStateManager`, `WorkflowState` |
| `utils.py` | Utility functions | Helper functions |

---

## Key Components

### 1. Configuration (`config.py`)

**Purpose**: Centralized configuration using Pydantic settings with environment variable support.

**Key Class**: `Settings`

```python
from src.core.config import settings

# Access configuration
print(settings.GEMINI_API_KEY)
print(settings.USE_REAL_LLM)
print(settings.MIN_SCENES)
```

#### Configuration Categories

**LLM Configuration**:
```python
llm_model_name: str = "gemini-2.5-flash"
```

**API Keys**:
```python
GEMINI_API_KEY: Optional[str] = None
ELEVENLABS_API_KEY: Optional[str] = None
OPENAI_API_KEY: Optional[str] = None
TAVILY_API_KEY: Optional[str] = None
```

**Feature Flags** (Mock vs Real Mode):
```python
USE_REAL_LLM: bool = False  # Use real Gemini or mock data
USE_REAL_IMAGE: bool = False  # Use real image generation or placeholders
USE_REAL_VOICE: bool = False  # Use real ElevenLabs or gTTS mock
```

**Error Handling & Development Mode**:
```python
DEV_MODE: bool = True  # Show all errors, no silent fallbacks
FAIL_FAST: bool = True  # Stop on first error
```

**Application Settings**:
```python
MIN_SCENES: int = 4  # Minimum scenes in scripts
MAX_SCENES: int = 15  # Maximum scenes in scripts
DEFAULT_SCENE_DURATION: float = 3.0  # Default scene duration (seconds)
GENERATED_ASSETS_DIR: str = "generated_assets"
IMAGE_ASPECT_RATIO: str = "9:16"  # Vertical for shorts
```

**Video Generation Settings**:
```python
VIDEO_RESOLUTION: str = "1080p"
VIDEO_FPS: int = 30
VIDEO_GENERATION_PROVIDER: str = "mock"  # mock, luma, runway
LUMA_API_KEY: Optional[str] = None
VIDEO_QUALITY: str = "medium"  # FFmpeg preset
MAX_AI_VIDEOS_PER_SCRIPT: int = 2
```

**Image Generation Retry Settings**:
```python
IMAGE_GENERATION_MAX_RETRIES: int = 5
IMAGE_GENERATION_RETRY_DELAYS: List[int] = [5, 15, 30, 60]
IMAGE_GENERATION_SCENE_DELAY: int = 5  # Delay between scenes
```

**Audio Generation Settings**:
```python
DEFAULT_VOICE_ID: str = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
VOICE_STABILITY: float = 0.5  # 0.0-1.0
VOICE_SIMILARITY: float = 0.75  # 0.0-1.0
VOICE_SETTINGS_OVERRIDE: str = "{}"  # JSON override per tone
```

#### Validators

**Scene Range Validation**:
```python
@field_validator('MAX_SCENES')
@classmethod
def validate_scene_range(cls, v, info):
    """Ensure MAX_SCENES >= MIN_SCENES."""
    min_scenes = info.data.get('MIN_SCENES', 4)
    if v < min_scenes:
        raise ValueError(f'MAX_SCENES ({v}) must be >= MIN_SCENES ({min_scenes})')
    return v
```

**Boolean Parsing**:
```python
@field_validator('USE_REAL_LLM', 'USE_REAL_IMAGE', 'USE_REAL_VOICE', 'DEV_MODE', 'FAIL_FAST', mode='before')
@classmethod
def parse_bool(cls, v):
    """Parse boolean from string env vars."""
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.lower() in ('true', '1', 'yes', 'on')
    return False
```

#### Environment Variables

Configuration is loaded from `.env` file:

```bash
# .env example
GEMINI_API_KEY=your_gemini_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here

USE_REAL_LLM=true
USE_REAL_IMAGE=true
USE_REAL_VOICE=true

DEV_MODE=true
FAIL_FAST=true

MIN_SCENES=4
MAX_SCENES=15
VIDEO_RESOLUTION=1080p
```

#### Usage Examples

**Accessing Settings**:
```python
from src.core.config import settings

# Check if using real services
if settings.USE_REAL_LLM:
    # Use real Gemini
    llm = ChatGoogleGenerativeAI(api_key=settings.GEMINI_API_KEY)
else:
    # Use mock data
    return get_mock_data()

# Get scene constraints
min_scenes = settings.MIN_SCENES
max_scenes = settings.MAX_SCENES

# Get paths
assets_dir = settings.GENERATED_ASSETS_DIR
```

**Modifying Settings at Runtime** (Not Recommended):
```python
# Settings are immutable by default
# To modify, create new Settings instance
from src.core.config import Settings

custom_settings = Settings(
    USE_REAL_LLM=True,
    MIN_SCENES=6
)
```

---

### 2. Logging (`logging.py`)

**Purpose**: Configure structured logging using structlog for consistent, parseable logs.

**Key Function**: `configure_logging()`

```python
from src.core.logging import configure_logging

logger = configure_logging()
logger.info("Application started", version="1.0.0")
```

#### Logging Configuration

**Structured Logging with structlog**:
- JSON-formatted logs for easy parsing
- Automatic context injection (timestamps, log levels)
- Correlation IDs for request tracing
- Exception information with stack traces

**Log Levels**:
- `DEBUG`: Detailed diagnostic information
- `INFO`: General informational messages
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical errors that may cause application failure

#### Usage Examples

**Basic Logging**:
```python
import structlog

logger = structlog.get_logger()

logger.info("Processing request", request_id="abc123")
logger.warning("Rate limit approaching", remaining=10)
logger.error("Failed to generate image", error=str(e), exc_info=True)
```

**Contextual Logging**:
```python
logger = structlog.get_logger()

# Add context to all subsequent logs
logger = logger.bind(
    workflow_id="workflow_123",
    user_id="user_456"
)

logger.info("Starting workflow")  # Includes workflow_id and user_id
logger.info("Completed step 1")  # Includes workflow_id and user_id
```

**Exception Logging**:
```python
try:
    result = risky_operation()
except Exception as e:
    logger.error(
        "Operation failed",
        error=str(e),
        error_type=type(e).__name__,
        exc_info=True  # Includes stack trace
    )
```

**Log Output Format**:
```json
{
  "event": "Processing request",
  "level": "info",
  "timestamp": "2025-11-25T21:08:37Z",
  "request_id": "abc123",
  "logger": "src.agents.director.agent"
}
```

---

### 3. Workflow State Management (`workflow_state.py`)

**Purpose**: Track progress of video generation workflows and enable resume functionality after failures.

**Key Classes**:
- `WorkflowState`: Represents workflow state
- `WorkflowStateManager`: Manages state persistence
- `WorkflowStep`: Enum of workflow steps
- `WorkflowStatus`: Enum of workflow statuses

#### Workflow Steps

```python
class WorkflowStep(str, Enum):
    SCRIPT_GENERATION = "script_generation"
    IMAGE_GENERATION = "image_generation"
    AUDIO_GENERATION = "audio_generation"
    VIDEO_ASSEMBLY = "video_assembly"
```

#### Workflow Statuses

```python
class WorkflowStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    FAILED = "failed"
    COMPLETED = "completed"
```

#### WorkflowState Model

```python
class WorkflowState(BaseModel):
    # Identification
    workflow_id: str
    
    # Status
    status: WorkflowStatus
    current_step: Optional[WorkflowStep]
    completed_steps: List[WorkflowStep]
    failed_step: Optional[WorkflowStep]
    
    # Error information
    error_message: Optional[str]
    error_type: Optional[str]
    
    # Input parameters
    topic: Optional[str]
    duration: Optional[str]
    
    # Generated artifacts (paths)
    script_path: Optional[str]
    image_paths: Dict[int, str]  # scene_number -> path
    audio_paths: Dict[int, str]  # scene_number -> path
    video_path: Optional[str]
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]
    
    # Progress tracking
    total_scenes: Optional[int]
    images_completed: int
    audio_completed: int
```

#### WorkflowStateManager

**Initialization**:
```python
from src.core.workflow_state import workflow_manager

# Global instance (already initialized)
state = workflow_manager.create_workflow(
    workflow_id="workflow_123",
    topic="AI and the future",
    duration="60s"
)
```

**Key Methods**:

**Create Workflow**:
```python
state = workflow_manager.create_workflow(
    workflow_id="workflow_123",
    topic="AI and the future",
    duration="60s"
)
```

**Update Step**:
```python
state = workflow_manager.update_step(
    workflow_id="workflow_123",
    step=WorkflowStep.SCRIPT_GENERATION,
    status=WorkflowStatus.IN_PROGRESS
)
```

**Mark Step Complete**:
```python
state = workflow_manager.mark_step_complete(
    workflow_id="workflow_123",
    step=WorkflowStep.SCRIPT_GENERATION
)
```

**Save Artifacts**:
```python
# Save script
state = workflow_manager.save_script(
    workflow_id="workflow_123",
    script_path="generated_assets/workflows/workflow_123/script.json",
    total_scenes=8
)

# Save image (incremental)
state = workflow_manager.save_image(
    workflow_id="workflow_123",
    scene_number=1,
    image_path="generated_assets/workflows/workflow_123/images/scene_1.png"
)

# Save audio (incremental)
state = workflow_manager.save_audio(
    workflow_id="workflow_123",
    scene_number=1,
    audio_path="generated_assets/workflows/workflow_123/audio/scene_1.mp3"
)

# Save final video
state = workflow_manager.save_video(
    workflow_id="workflow_123",
    video_path="generated_assets/workflows/workflow_123/final_video.mp4"
)
```

**Mark Failed**:
```python
state = workflow_manager.mark_failed(
    workflow_id="workflow_123",
    step=WorkflowStep.IMAGE_GENERATION,
    error_message="Rate limit exceeded",
    error_type="RateLimitError"
)
```

**Mark Completed**:
```python
state = workflow_manager.mark_completed(
    workflow_id="workflow_123"
)
```

**Load State**:
```python
state = workflow_manager.load_state("workflow_123")
if state:
    print(f"Status: {state.status}")
    print(f"Progress: {state.images_completed}/{state.total_scenes} images")
```

**List Workflows**:
```python
# All workflows
all_workflows = workflow_manager.list_workflows()

# Failed workflows only
failed_workflows = workflow_manager.list_workflows(
    status=WorkflowStatus.FAILED
)
```

#### State Persistence

**Storage Location**:
```
generated_assets/workflows/
├── workflow_123/
│   ├── state.json
│   ├── script.json
│   ├── images/
│   │   ├── scene_1.png
│   │   └── scene_2.png
│   ├── audio/
│   │   ├── scene_1.mp3
│   │   └── scene_2.mp3
│   └── final_video.mp4
└── workflow_456/
    └── state.json
```

**State File Format** (`state.json`):
```json
{
  "workflow_id": "workflow_123",
  "status": "in_progress",
  "current_step": "image_generation",
  "completed_steps": ["script_generation"],
  "failed_step": null,
  "error_message": null,
  "error_type": null,
  "topic": "AI and the future",
  "duration": "60s",
  "script_path": "generated_assets/workflows/workflow_123/script.json",
  "image_paths": {
    "1": "generated_assets/workflows/workflow_123/images/scene_1.png",
    "2": "generated_assets/workflows/workflow_123/images/scene_2.png"
  },
  "audio_paths": {
    "1": "generated_assets/workflows/workflow_123/audio/scene_1.mp3"
  },
  "video_path": null,
  "created_at": "2025-11-25T21:00:00Z",
  "updated_at": "2025-11-25T21:05:00Z",
  "completed_at": null,
  "total_scenes": 8,
  "images_completed": 2,
  "audio_completed": 1
}
```

#### Resume Workflow Example

```python
from src.core.workflow_state import workflow_manager, WorkflowStep, WorkflowStatus

# Load existing workflow
state = workflow_manager.load_state("workflow_123")

if state.status == WorkflowStatus.FAILED:
    # Resume from failed step
    failed_step = state.failed_step
    
    if failed_step == WorkflowStep.IMAGE_GENERATION:
        # Resume image generation
        # Skip already completed scenes
        for scene_num in range(1, state.total_scenes + 1):
            if scene_num not in state.image_paths:
                # Generate missing image
                image_path = await generate_image(scene_num)
                workflow_manager.save_image(
                    workflow_id=state.workflow_id,
                    scene_number=scene_num,
                    image_path=image_path
                )
        
        # Mark step complete
        workflow_manager.mark_step_complete(
            workflow_id=state.workflow_id,
            step=WorkflowStep.IMAGE_GENERATION
        )
        
        # Continue to next step
        # ...
```

---

### 4. Utilities (`utils.py`)

**Purpose**: Common helper functions used throughout the application.

**Current Functions**:
- File path utilities
- String formatting helpers
- Validation functions

**Example**:
```python
from src.core.utils import ensure_dir_exists

ensure_dir_exists("generated_assets/images")
```

---

## Implementation Details

### Configuration Loading Order

1. **Default values** in `Settings` class
2. **Environment variables** from `.env` file
3. **System environment variables** (override `.env`)

### Type Safety

All configuration uses Pydantic for:
- Type validation
- Value constraints (min/max, regex, etc.)
- Automatic type conversion
- Clear error messages

Example:
```python
MIN_SCENES: int = Field(
    default=4,
    ge=2,  # Greater than or equal to 2
    le=20,  # Less than or equal to 20
    description="Minimum number of scenes"
)
```

### Logging Best Practices

1. **Use structured logging**:
   ```python
   # Good
   logger.info("User logged in", user_id=123, ip="1.2.3.4")
   
   # Bad
   logger.info(f"User {user_id} logged in from {ip}")
   ```

2. **Include context**:
   ```python
   logger = logger.bind(request_id=request_id)
   ```

3. **Log exceptions with stack traces**:
   ```python
   logger.error("Failed", error=str(e), exc_info=True)
   ```

### Workflow State Best Practices

1. **Always save state after changes**:
   ```python
   state.images_completed += 1
   workflow_manager.save_state(state)
   ```

2. **Use incremental saves** for long-running operations:
   ```python
   for scene in scenes:
       image = generate_image(scene)
       workflow_manager.save_image(workflow_id, scene.number, image)
       # State saved automatically
   ```

3. **Check for existing state** before creating:
   ```python
   state = workflow_manager.load_state(workflow_id)
   if not state:
       state = workflow_manager.create_workflow(workflow_id)
   ```

---

## Dependencies

### External Libraries

- **pydantic**: Data validation and settings management
- **pydantic-settings**: Environment variable loading
- **structlog**: Structured logging
- **python-dotenv**: `.env` file loading (implicit via pydantic-settings)

### Internal Dependencies

None - core module is self-contained and used by all other modules.

---

## Common Tasks

### Adding a New Configuration Setting

1. **Add field to `Settings` class**:
   ```python
   class Settings(BaseSettings):
       NEW_SETTING: str = Field(
           default="default_value",
           description="Description of setting"
       )
   ```

2. **Add to `.env` file**:
   ```bash
   NEW_SETTING=production_value
   ```

3. **Use in code**:
   ```python
   from src.core.config import settings
   
   value = settings.NEW_SETTING
   ```

### Adding a Validator

```python
@field_validator('NEW_SETTING')
@classmethod
def validate_new_setting(cls, v):
    """Validate NEW_SETTING."""
    if not v.startswith("prefix_"):
        raise ValueError("Must start with 'prefix_'")
    return v
```

### Changing Log Format

Modify `logging.py`:
```python
def configure_logging():
    structlog.configure(
        processors=[
            # Add custom processors
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            # ...
        ]
    )
```

### Adding a Workflow Step

1. **Add to `WorkflowStep` enum**:
   ```python
   class WorkflowStep(str, Enum):
       SCRIPT_GENERATION = "script_generation"
       IMAGE_GENERATION = "image_generation"
       AUDIO_GENERATION = "audio_generation"
       NEW_STEP = "new_step"  # Add here
       VIDEO_ASSEMBLY = "video_assembly"
   ```

2. **Update workflow logic** to handle new step

3. **Add state tracking** if needed:
   ```python
   def save_new_step_result(
       self,
       workflow_id: str,
       result_path: str
   ) -> WorkflowState:
       state = self.load_state(workflow_id)
       state.new_step_path = result_path
       self.save_state(state)
       return state
   ```

---

## Gotchas and Notes

### Known Issues

1. **Boolean Environment Variables**: Must use lowercase `true`/`false` or `1`/`0`
   ```bash
   # Correct
   USE_REAL_LLM=true
   USE_REAL_LLM=1
   
   # Incorrect
   USE_REAL_LLM=True
   USE_REAL_LLM=TRUE
   ```

2. **Settings are Immutable**: Cannot modify `settings` object after creation
   ```python
   # Wrong
   settings.USE_REAL_LLM = True
   
   # Correct
   # Modify .env file and restart application
   ```

3. **Workflow State Concurrency**: Not thread-safe. Use locks for concurrent access.

4. **Log File Rotation**: Not implemented. Consider adding for production.

### Common Mistakes

1. **Not loading environment variables**:
   ```python
   # Wrong
   api_key = os.getenv("GEMINI_API_KEY")
   
   # Correct
   from src.core.config import settings
   api_key = settings.GEMINI_API_KEY
   ```

2. **Hardcoding paths**:
   ```python
   # Wrong
   path = "generated_assets/images"
   
   # Correct
   path = f"{settings.GENERATED_ASSETS_DIR}/images"
   ```

3. **Not saving workflow state**:
   ```python
   # Wrong
   state.images_completed += 1
   # State not persisted!
   
   # Correct
   state.images_completed += 1
   workflow_manager.save_state(state)
   ```

### Performance Considerations

1. **Configuration Loading**: Settings loaded once at startup (singleton pattern)

2. **Workflow State I/O**: Each save writes to disk. Use incremental saves wisely.

3. **Logging Overhead**: Structured logging has minimal overhead, but avoid excessive debug logs in production.

---

## Security Considerations

### Current State

- API keys stored in environment variables
- No encryption for workflow state files
- Logs may contain sensitive information

### Production Recommendations

1. **Use Secret Management**:
   ```python
   # Google Cloud Secret Manager
   from google.cloud import secretmanager
   
   client = secretmanager.SecretManagerServiceClient()
   secret = client.access_secret_version(name="projects/*/secrets/*/versions/latest")
   api_key = secret.payload.data.decode("UTF-8")
   ```

2. **Encrypt Workflow State**: Add encryption for sensitive workflow data

3. **Sanitize Logs**: Remove sensitive data from logs
   ```python
   logger.info("API call", api_key="***REDACTED***")
   ```

4. **Rotate API Keys**: Implement key rotation strategy

---

## Related Documentation

- [API Documentation](../api/README.md) - API that uses core configuration
- [Agents Documentation](../agents/README.md) - Agents that use core utilities
- [Developer Guide](../DEVELOPER_GUIDE.md) - General development guide

---

## Future Improvements

1. **Configuration Validation**: Add startup validation for all required settings
2. **Log Rotation**: Implement log file rotation for production
3. **Metrics Collection**: Add metrics tracking (Prometheus, etc.)
4. **Workflow Cleanup**: Auto-cleanup old workflow states
5. **Configuration Hot Reload**: Reload config without restart
6. **Distributed Locking**: Support for concurrent workflow access
7. **State Encryption**: Encrypt sensitive workflow data
8. **Audit Logging**: Track all configuration changes

---

**For questions or issues, see the main [Developer Guide](../DEVELOPER_GUIDE.md) or check existing tickets in `/tickets`.**
