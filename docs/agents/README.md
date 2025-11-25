# Agents Documentation

## Overview

The `src/agents/` directory contains specialized AI agents that handle different aspects of short-form video content generation. Each agent is designed with a single responsibility and uses LangChain for LLM orchestration.

## Architecture

All agents follow a consistent architecture pattern:

```
Agent
├── __init__() - Initialize with API validation
├── Main Method - Core functionality (e.g., find_stories, generate_script)
└── Helper Methods - Private methods for specific tasks
```

### Key Design Patterns

1. **Dual Mode Operation**: All agents support both real LLM mode and mock mode
2. **Fail-Safe Initialization**: Agents validate API keys before initialization
3. **Structured Logging**: Request IDs track operations through the system
4. **LangChain Integration**: Uses LCEL (LangChain Expression Language) chains
5. **Error Handling**: Exceptions propagate to allow fallback decorators to handle

## Agent Inventory

### 1. StoryFinderAgent (`story_finder/`)
**Purpose**: Generate creative story ideas from topics

**Files**:
- `agent.py` - Main agent implementation
- `prompts.py` - LLM prompts and output parsers
- `models.py` - Pydantic models for story data

**Key Method**: `find_stories(subject: str, num_stories: int, category: str, mood: str) -> StoryList`

**Features**:
- **Dynamic Routing**: Switches personas (News, Real Story, Fiction, etc.) based on category
- **Web Search**: Integrates Tavily Search for real-time data (News/Real Story)
- **Context Awareness**: Adapts output style to requested mood

**Mode Switching**:
- **Real Mode**: Uses Gemini LLM + Tavily Search (optional)
- **Mock Mode**: Returns predefined mock stories for testing

### 2. ScriptWriterAgent (`script_writer/`)
**Purpose**: Convert story ideas into structured video scripts with scenes

**Files**:
- `agent.py` - Main agent implementation
- `prompts.py` - Script generation prompts and parsers

**Key Method**: `generate_script(subject: str) -> VideoScript`

**Mode Switching**:
- **Real Mode**: Uses Gemini LLM to create detailed scene-by-scene scripts
- **Mock Mode**: Returns mock script from `api/mock_data.py`

### 3. ImageGenAgent (`image_gen/`)
**Purpose**: Generate images for video scenes

**Files**:
- `agent.py` - Main agent implementation
- `nanobanana_client.py` - NanoBanana API client

**Key Method**: `generate_images(scenes: List[Scene]) -> Dict[int, str]`

**Features**:
- Prompt enhancement with style modifiers
- Image caching to avoid regeneration
- Parallel image generation
- Fallback to placeholder images

**Mode Switching**:
- **Real Mode**: Uses NanoBanana API for AI image generation
- **Mock Mode**: Uses placehold.co for placeholder images

### 4. VideoGenAgent (`video_gen/`)
**Purpose**: Generate video clips (currently mock implementation)

**Files**:
- `agent.py` - Main agent implementation

**Key Methods**:
- `generate_from_text(prompt: str) -> str`
- `generate_from_image(image_path: str, prompt: str) -> str`

**Current Status**: Mock implementation using MoviePy for simple color clips

### 5. VoiceAgent (`voice/`)
**Purpose**: Generate voiceovers for scenes (placeholder)

**Status**: Placeholder for future ElevenLabs integration

### 6. VideoAssemblyAgent (`video_assembly/`)
**Purpose**: Assemble final videos from scenes (placeholder)

**Status**: Placeholder for future implementation

## Configuration

All agents use centralized configuration from `src/core/config.py`:

### Environment Variables

```bash
# LLM Configuration
USE_REAL_LLM=True                    # Enable real LLM (default: False)
GEMINI_API_KEY=your_key_here         # Required for real LLM
TAVILY_API_KEY=your_key_here         # Required for Story Finder search
LLM_MODEL_NAME=gemini-1.5-flash-latest  # Model to use

# Image Generation
USE_REAL_IMAGE=True                  # Enable real image gen (default: False)
NANO_BANANA_API_KEY=your_key_here    # Required for real images
NANO_BANANA_API_URL=https://api.nanobanana.com

# Output Configuration
GENERATED_ASSETS_DIR=./generated_assets  # Where to save outputs
MAX_VIDEO_SCENES=5                   # Max scenes per video
```

## Common Patterns

### 1. Initialization Pattern

All agents follow this initialization pattern:

```python
class MyAgent:
    def __init__(self):
        if settings.USE_REAL_LLM:
            if not settings.GEMINI_API_KEY:
                raise ValueError("API key required")
            
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_retries=3,
                request_timeout=30.0,
            )
            self.chain = TEMPLATE | self.llm | parser
        else:
            self.llm = None
            self.chain = None
```

### 2. Request Tracking

```python
request_id = str(uuid.uuid4())[:8]
logger.info(f"[{request_id}] Operation started")
# ... operation ...
logger.info(f"[{request_id}] Operation completed")
```

### 3. Error Handling

Agents raise exceptions to allow API-level fallback:

```python
try:
    result = self.chain.invoke(params)
    return result
except Exception as e:
    logger.error(f"Operation failed: {e}", exc_info=True)
    raise  # Let @with_fallback decorator handle it
```

## LangChain Integration

### Chain Structure

Agents use LCEL (LangChain Expression Language) for composable chains:

```python
chain = PROMPT_TEMPLATE | llm | output_parser
result = chain.invoke(input_dict)
```

### Components

1. **Prompt Templates**: Define structured prompts with variables
2. **LLM**: ChatGoogleGenerativeAI with retry logic
3. **Output Parsers**: Convert LLM output to Pydantic models

### Example Chain

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser

# Define template
template = ChatPromptTemplate.from_messages([
    ("system", "You are a creative writer."),
    ("human", "Write about: {subject}")
])

# Define parser
parser = PydanticOutputParser(pydantic_object=StoryList)

# Build chain
chain = template | llm | parser

# Invoke
result = chain.invoke({"subject": "coffee"})
```

## Testing

### Mock Mode Testing

All agents can be tested without API keys:

```python
# In .env
USE_REAL_LLM=False
USE_REAL_IMAGE=False

# Agents will return mock data
agent = StoryFinderAgent()
stories = agent.find_stories("test")  # Returns mock stories
```

### Integration Testing

See `tests/integration/test_pipeline.py` for full pipeline tests.

## Common Tasks

### Adding a New Agent

1. Create agent directory: `src/agents/my_agent/`
2. Create `agent.py` with class following the pattern
3. Create `prompts.py` if using LLM
4. Add configuration to `src/core/config.py`
5. Add mock data to `src/api/mock_data.py`
6. Create tests in `tests/`

### Modifying Prompts

1. Edit `prompts.py` in the agent directory
2. Test with mock mode first
3. Test with real LLM
4. Monitor token usage and costs

### Changing LLM Model

Update in `.env`:
```bash
LLM_MODEL_NAME=gemini-1.5-pro-latest  # For more powerful model
```

## Gotchas and Notes

### 1. Model Name Format

⚠️ **Important**: Use `-latest` suffix for Gemini models with v1beta API:
- ✅ `gemini-1.5-flash-latest`
- ❌ `gemini-1.5-flash` (will cause 404 error)

### 2. Logging Conflicts

❌ **Don't use** `extra={"args": ...}` in logging calls - it conflicts with LangChain's internal logging:

```python
# Bad
logger.info("Message", extra={"args": value})

# Good
logger.info(f"Message (args: {value})")
```

### 3. API Key Validation

Agents validate API keys at initialization, not at invocation. This means:
- Errors appear when creating the agent, not when calling methods
- Tests should mock at the agent level, not method level

### 4. Mock Mode Behavior

Mock mode is determined at initialization. Changing environment variables requires:
1. Restarting the application
2. Creating new agent instances

### 5. Async vs Sync

- `ImageGenAgent` uses async methods (returns coroutines)
- Other agents use sync methods
- Mix carefully in API routes (use `await` for async agents)

## Dependencies

### External Libraries

- `langchain-google-genai` - Gemini LLM integration
- `langchain-community` - Community tools (Tavily)
- `tavily-python` - Web search API
- `langchain-core` - LangChain framework
- `pydantic` - Data validation
- `requests` - HTTP client for image downloads
- `moviepy` - Video generation (VideoGenAgent)

### Internal Dependencies

- `src/core/config` - Configuration management
- `src/models/models` - Shared data models
- `src/api/mock_data` - Mock data for testing

## Performance Considerations

### 1. Caching

`ImageGenAgent` implements caching:
- Cache key: SHA256 of `prompt:model`
- Location: `generated_assets/images/cache/`
- Benefit: Avoid regenerating identical images

### 2. Parallel Processing

`ImageGenAgent` generates images in parallel:
```python
tasks = [self._generate_single_image(client, scene) for scene in scenes]
results = await asyncio.gather(*tasks)
```

### 3. Retry Logic

LLM agents have built-in retry:
```python
max_retries=3,
request_timeout=30.0,
```

## Security Considerations

1. **API Keys**: Never commit API keys to git
2. **Input Validation**: All inputs are validated via Pydantic
3. **File Paths**: Output paths are sanitized and restricted to `GENERATED_ASSETS_DIR`
4. **Rate Limiting**: Consider implementing rate limiting for production

## Migration Notes

### Recent Changes

1. **Logging Fix** (2025-01): Removed `extra` parameter from logging calls to fix LangChain conflicts
2. **Model Name Update** (2025-01): Changed default model to `gemini-1.5-flash-latest`
3. **Variable Name Fix** (2025-01): Fixed `SCRIPT_WRITER_TEMPLATE` → `SCRIPT_WRITER_AGENT_TEMPLATE`

---

**Last Updated**: 2025-01-21
**Version**: 1.0
