# LLM & Agent Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Base Agent Pattern](#base-agent-pattern)
4. [LLM Integration](#llm-integration)
5. [Agent Types & Responsibilities](#agent-types--responsibilities)
6. [LLM Chain Patterns](#llm-chain-patterns)
7. [Prompt Engineering Strategy](#prompt-engineering-strategy)
8. [Error Handling & Retry Logic](#error-handling--retry-logic)
9. [Best Practices](#best-practices)

---

## Overview

ShortFactory uses a **multi-agent architecture** where specialized AI agents collaborate to generate YouTube Shorts. Each agent is responsible for a specific domain (script writing, image generation, voice synthesis, etc.) and uses Large Language Models (LLMs) for intelligent decision-making.

### Key Technologies
- **LLM Provider**: Google Gemini (via LangChain)
- **Framework**: LangChain for LLM orchestration
- **Pattern**: Agent-based architecture with inheritance
- **Language**: Python 3.12+ with async/await

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        ShortFactory Pipeline                     │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   BaseAgent (Abstract)   │
                    │  ┌──────────────────┐   │
                    │  │ LLM: Gemini 2.5  │   │
                    │  │ Temperature: 0.7 │   │
                    │  │ Timeout: 300s    │   │
                    │  └──────────────────┘   │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌───────────────┐      ┌──────────────────┐     ┌─────────────────┐
│ ScriptWriter  │      │  DirectorAgent   │     │  ImageGenAgent  │
│    Agent      │      │                  │     │  (No LLM)       │
├───────────────┤      ├──────────────────┤     ├─────────────────┤
│ LLM: ✓        │      │ LLM: ✓           │     │ LLM: ✗          │
│ Chain: ✓      │      │ Chain: ✗         │     │ API: Gemini Img │
│               │      │                  │     │                 │
│ Generates:    │      │ Generates:       │     │ Generates:      │
│ - VideoScript │      │ - Cinematic      │     │ - Images        │
│ - Scenes      │      │   Direction      │     │                 │
│ - Dialogue    │      │ - Shot Lists     │     │                 │
└───────────────┘      └──────────────────┘     └─────────────────┘
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │   VoiceAgent (No LLM)  │
                    │   API: ElevenLabs      │
                    └────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ VideoGenAgent (No LLM) │
                    │   Uses: MoviePy        │
                    └────────────────────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │ VideoAssemblyAgent     │
                    │   (No LLM)             │
                    └────────────────────────┘
```

---

## Base Agent Pattern

### Class Hierarchy

```python
BaseAgent (Abstract)
    │
    ├── ScriptWriterAgent (LLM-based)
    ├── DirectorAgent (LLM-based)
    ├── ImageGenAgent (API-based, no LLM)
    ├── VoiceAgent (API-based, no LLM)
    ├── VideoGenAgent (Processing-based, no LLM)
    └── VideoAssemblyAgent (Processing-based, no LLM)
```

### BaseAgent Implementation

```python
class BaseAgent(ABC):
    """
    Base class for all AI agents in the ShortFactory pipeline.
    
    Provides:
    - LLM initialization with Gemini
    - API key validation
    - Mock mode handling
    - Logging setup
    """
    
    def __init__(
        self,
        agent_name: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        request_timeout: Optional[float] = None,
        require_llm: bool = True
    ):
        self.agent_name = agent_name
        self.mock_mode = not settings.USE_REAL_LLM
        self.llm: Optional[ChatGoogleGenerativeAI] = None
        
        actual_timeout = request_timeout or settings.DEFAULT_REQUEST_TIMEOUT
        
        if require_llm:
            self._initialize_llm(temperature, max_retries, actual_timeout)
        
        self._setup()  # Agent-specific setup
```

### Key Design Decisions

1. **Inheritance over Composition**: All agents inherit from `BaseAgent` for consistent initialization
2. **Optional LLM**: `require_llm=False` for agents that don't need LLM (image, voice, video)
3. **Lazy Initialization**: LLM is only initialized when needed
4. **Mock Mode**: Supports testing without API calls

---

## LLM Integration

### LangChain Integration Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    LangChain Integration                     │
└─────────────────────────────────────────────────────────────┘

User Input
    │
    ▼
┌──────────────────┐
│ Agent.method()   │
│ (e.g., generate_ │
│  script())       │
└────────┬─────────┘
         │
         ▼
┌──────────────────────────────────────────────────────────────┐
│                    LangChain Chain                            │
│  ┌────────────┐    ┌──────────┐    ┌─────────┐    ┌───────┐ │
│  │  Prompt    │───▶│   LLM    │───▶│ Parser  │───▶│Output │ │
│  │  Template  │    │ (Gemini) │    │(Pydantic│    │ Model │ │
│  └────────────┘    └──────────┘    └─────────┘    └───────┘ │
└──────────────────────────────────────────────────────────────┘
         │
         ▼
┌──────────────────┐
│ Structured Output│
│ (VideoScript,    │
│  DirectedScript) │
└──────────────────┘
```

### LLM Configuration

```python
# In BaseAgent._initialize_llm()
self.llm = ChatGoogleGenerativeAI(
    model=settings.llm_model_name,           # "gemini-2.5-flash"
    google_api_key=settings.GEMINI_API_KEY,
    temperature=temperature,                  # 0.7 (default)
    max_retries=max_retries,                 # 3 (default)
    request_timeout=actual_timeout,          # 300s (5 minutes)
)
```

### Temperature Settings by Agent

| Agent | Temperature | Reasoning |
|-------|-------------|-----------|
| ScriptWriter | 0.7 | Balance creativity and structure |
| Director | 0.7 | Creative cinematography with consistency |
| Others | N/A | Don't use LLM |

---

## Agent Types & Responsibilities

### 1. ScriptWriterAgent (LLM-Based)

**Purpose**: Generate complete video scripts from user input

**LLM Usage**: ✅ Heavy
- Uses LangChain chains with prompt routing
- Structured output parsing with Pydantic
- Retry logic with exponential backoff

**Chain Architecture**:
```python
chain = (
    {
        "subject": lambda x: x["subject"],
        "language": lambda x: x["language"],
        "max_video_scenes": lambda x: x["max_video_scenes"],
        "category": lambda x: x.get("category", "Creative"),
        "format_instructions": lambda x: VIDEO_SCRIPT_PARSER.get_format_instructions()
    }
    | prompt_router  # Routes to different templates based on category
    | self.llm       # Gemini LLM
    | VIDEO_SCRIPT_PARSER  # Pydantic parser
)
```

**Prompt Routing**:
```
Input Category
    │
    ├─ "Real Story" / "News" ──────▶ REAL_STORY_TEMPLATE
    ├─ "Educational" / "Explainer" ─▶ EDUCATIONAL_TEMPLATE
    └─ Default ────────────────────▶ CREATIVE_TEMPLATE
```

**Output**: `VideoScript` (Pydantic model with scenes, dialogue, image prompts)

---

### 2. DirectorAgent (LLM-Based)

**Purpose**: Add cinematic direction to scripts

**LLM Usage**: ✅ Moderate
- Direct LLM invocation (not chains)
- JSON response parsing
- Fallback to rule-based direction

**LLM Call Pattern**:
```python
async def _generate_scene_direction(self, scene, ...):
    prompt = self._create_director_prompt(scene, ...)
    
    # Direct LLM call
    response = self.llm.invoke(prompt)
    
    # Parse JSON response
    direction_data = json.loads(response.content)
    
    # Create structured output
    return CinematicDirection(**direction_data)
```

**Prompt Structure**:
```
You are a master film director...

**Global Visual Style:** {global_visual_style}
**Scene Information:** ...
**Your Task:** Create cinematic direction that:
1. Serves the narrative beat
2. Evokes emotional tone
3. MAINTAINS GLOBAL VISUAL STYLE

**Output JSON Format:**
{
    "shot_type": "...",
    "camera_movement": "...",
    "enhanced_image_prompt": "..., {global_visual_style}",
    ...
}
```

**Output**: `DirectedScript` with `CinematicDirection` for each scene

---

### 3. ImageGenAgent (API-Based, No LLM)

**Purpose**: Generate images from prompts

**LLM Usage**: ❌ None
- Uses Gemini Image API directly
- Prompt enhancement without LLM
- Rule-based style application

**Why No LLM?**
- Image generation is handled by specialized image model
- Prompt enhancement uses deterministic rules
- No need for reasoning/creativity

**Prompt Enhancement Flow**:
```python
def _enhance_prompt_text(self, base_prompt, style, global_visual_style=""):
    # Deterministic enhancement
    enhanced = f"{base_prompt}, {vertical_composition}, {style_suffix}, {quality_suffix}"
    
    # Add global style for consistency
    if global_visual_style:
        enhanced = f"{enhanced}, {global_visual_style}"
    
    return enhanced
```

---

### 4. VoiceAgent (API-Based, No LLM)

**Purpose**: Generate voiceovers from text

**LLM Usage**: ❌ None
- Uses ElevenLabs API
- Rule-based voice settings per tone
- No reasoning required

---

### 5. VideoGenAgent & VideoAssemblyAgent (Processing-Based)

**Purpose**: Video composition and assembly

**LLM Usage**: ❌ None
- Pure video processing (MoviePy)
- Deterministic operations
- No AI decision-making needed

---

## LLM Chain Patterns

### Pattern 1: LCEL (LangChain Expression Language) Chain

**Used by**: ScriptWriterAgent

```python
# Declarative chain definition
chain = (
    input_mapper
    | prompt_router
    | llm
    | output_parser
)

# Async execution
result = await chain.ainvoke(input_data)
```

**Advantages**:
- Declarative and readable
- Built-in retry logic
- Automatic error handling
- Streaming support

---

### Pattern 2: Direct LLM Invocation

**Used by**: DirectorAgent

```python
# Imperative LLM call
response = self.llm.invoke(prompt)

# Manual parsing
content = response.content
direction_data = json.loads(content)
```

**Advantages**:
- More control over parsing
- Easier to handle complex JSON
- Custom error handling

**Why DirectorAgent uses this**:
- Complex nested JSON output
- Need for custom fallback logic
- Gemini doesn't support `response_format` parameter

---

## Prompt Engineering Strategy

### 1. Structured Output Prompts

**Goal**: Get consistent, parseable responses

**Technique**: Provide explicit JSON schema in prompt

```python
prompt = f"""
**Output JSON Format:**
{{
    "shot_type": "medium_close_up",
    "camera_movement": "slow_push_in",
    "enhanced_image_prompt": "...",
    ...
}}

**IMPORTANT:**
You MUST provide exactly {len(scene.content)} visual segments.
Each must have an 'image_prompt' field.
"""
```

---

### 2. Few-Shot Examples

**Goal**: Guide LLM behavior with examples

**Technique**: Include example outputs in prompt

```python
VIDEO_PROMPT_EXAMPLES = """
Good video_prompt examples:
- "Character starts with curious expression, then eyes widen..."
- "Character points enthusiastically at diagram..."
"""
```

---

### 3. Constraint Enforcement

**Goal**: Ensure LLM follows rules

**Technique**: Use bold, repeated instructions

```python
prompt = f"""
**CRITICAL: All enhanced_image_prompt and visual_segments 
MUST include the global visual style: "{global_visual_style}"**

5. **MAINTAINS THE GLOBAL VISUAL STYLE: {global_visual_style}**
"""
```

---

### 4. Prompt Routing

**Goal**: Different prompts for different content types

**Technique**: LangChain `RunnableBranch`

```python
prompt_router = RunnableBranch(
    (lambda x: x.get("category") in ["Real Story", "News"], 
     REAL_STORY_TEMPLATE),
    (lambda x: x.get("category") in ["Educational", "Explainer"], 
     EDUCATIONAL_TEMPLATE),
    CREATIVE_TEMPLATE  # Default
)
```

---

## Error Handling & Retry Logic

### Retry Decorator Pattern

```python
@retry_with_backoff(operation_name="script generation")
async def _generate_script_internal(self, ...):
    """Internal method with automatic retries"""
    result = await self.chain.ainvoke(input_data)
    return result
```

**Retry Configuration**:
- Max retries: 3
- Backoff: Exponential (2s, 4s, 8s)
- Retryable errors: `ValidationError`, `ValueError`, API errors

---

### Validation & Fixing

**ScriptWriterAgent** validates and auto-fixes common LLM errors:

```python
def _validate_and_fix_script(self, script: VideoScript):
    """Fix common LLM mistakes"""
    
    # Fix invalid enum values
    if scene.voice_tone == "explanation":
        scene.voice_tone = VoiceTone.SERIOUS
    
    # Fix scene count
    if len(script.scenes) < settings.MIN_SCENES:
        raise ValueError("Too few scenes")
    
    return script
```

**Common Fixes**:
- Invalid enum values → Map to closest valid value
- Missing fields → Use defaults
- Too few/many scenes → Raise error for retry

---

### Fallback Strategies

**DirectorAgent** has rule-based fallback:

```python
try:
    # Try LLM-based direction
    direction = await self._generate_scene_direction(...)
except Exception as e:
    logger.warning("LLM failed, using fallback")
    # Use emotion-based rules
    direction = self._create_fallback_scene_direction(scene, emotion)
```

---

## Best Practices

### 1. **Separate LLM-Based from Rule-Based Logic**

✅ **Good**:
```python
class ImageGenAgent(BaseAgent):
    def __init__(self):
        super().__init__(require_llm=False)  # No LLM needed
```

❌ **Bad**:
```python
# Don't use LLM for deterministic tasks
llm.invoke("Convert this to uppercase")
```

---

### 2. **Use Pydantic for Structured Output**

✅ **Good**:
```python
class VideoScript(BaseModel):
    title: str
    scenes: List[Scene]
    
    @field_validator('scenes')
    def validate_scene_count(cls, v):
        if len(v) < MIN_SCENES:
            raise ValueError("Too few scenes")
        return v
```

**Benefits**:
- Automatic validation
- Type safety
- Self-documenting

---

### 3. **Implement Retry Logic for LLM Calls**

✅ **Good**:
```python
@retry_with_backoff(operation_name="generation")
async def _generate_internal(self, ...):
    return await self.llm.invoke(...)
```

**Why**:
- LLMs can fail (rate limits, timeouts)
- Transient errors are common
- Exponential backoff prevents API hammering

---

### 4. **Use Mock Mode for Testing**

```python
if not settings.USE_REAL_LLM:
    return get_mock_script()  # Fast, deterministic
```

**Benefits**:
- Fast tests
- No API costs
- Deterministic behavior

---

### 5. **Set Appropriate Timeouts**

```python
DEFAULT_REQUEST_TIMEOUT = 300.0  # 5 minutes for complex generations
```

**Why**:
- Script generation can take 30-60 seconds
- Image generation: 10-20 seconds
- Prevents premature timeouts

---

### 6. **Log LLM Interactions**

```python
logger.info("Generating script", 
           subject=subject[:50], 
           category=category)

logger.debug("LLM prompt", prompt=prompt[:200])

logger.info("Script generated", 
           scenes=len(result.scenes))
```

**Benefits**:
- Debugging
- Performance monitoring
- Cost tracking

---

## Conclusion

ShortFactory's LLM & Agent architecture demonstrates several AI engineering best practices:

1. **Separation of Concerns**: LLM-based agents for creative tasks, rule-based for deterministic tasks
2. **Structured Output**: Pydantic models ensure type safety and validation
3. **Error Resilience**: Retry logic, validation, and fallbacks
4. **Prompt Engineering**: Structured prompts, few-shot examples, constraint enforcement
5. **Testability**: Mock mode for fast, deterministic testing

This architecture enables reliable, scalable AI-powered video generation while maintaining code quality and developer experience.
