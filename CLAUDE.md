# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ShortFactory LangChain** is an AI-powered video creation pipeline that generates short-form videos by:
1. Using LLMs (via LangChain) to generate structured video scripts
2. Creating images for each scene (via Gemini API)
3. Generating voice narration (via gTTS/ElevenLabs)
4. Assembling everything into final videos (via MoviePy)

The system is built primarily in Python with Jupyter notebooks for interactive development and uses LangChain for orchestrating AI agents.

## Environment Setup

### Prerequisites
- Python 3.8+ (supports up to 3.12)
- Virtual environment in `venv/` directory

### Initial Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Install project in editable mode
pip install -e .
```

### Environment Variables
Copy `.env.example` to `.env` and configure:
- `GEMINI_API_KEY`: Google Gemini API key (required)
- `OPENAI_API_KEY`: OpenAI API key (optional, if using OpenAI)

**CRITICAL**: Never commit `.env` file - it's already in `.gitignore`

## Common Commands

### Development
```bash
# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Install project in editable mode (for imports to work)
pip install -e .

# Start Jupyter notebook
jupyter notebook
```

### Testing
```bash
# Run all tests (from tests/README.md)
python tests/run_tests.py

# Run specific test file directly
python tests/test_script_generation.py
```

### Cleanup
```bash
# Remove virtual environment and cache files
make clean

# Or manually
rm -rf venv __pycache__ .ipynb_checkpoints
find . -name "*.pyc" -delete
```

## Architecture

### Core Agent System

The project implements a **multi-agent video generation system** using LangChain:

**Agent 1 - Script Writer** (`src/prompts/scrip_writer_agent.py`):
- Master story creator and director
- Takes subject/topic as input
- Outputs structured `VideoScript` with multiple `Scene` objects
- Uses dynamic prompt generation that automatically includes all Pydantic enum values
- Designs narrative flow, visual direction, audio direction, and pacing

**Future Agents**:
- Agent 2: Image generation from script descriptions
- Agent 3: Video animation creation
- Agent 4: Voice synthesis with ElevenLabs settings

### Data Models (`src/models/models.py`)

The system uses **Pydantic models** for type-safe, structured data:

**Enums** (all use lowercase string values):
- `SceneType`: explanation, visual_demo, comparison, story_telling, hook, conclusion
- `ImageStyle`: single_character, infographic, four_cut_cartoon, cinematic, etc.
- `VoiceTone`: excited, curious, serious, friendly, mysterious, etc.
- `TransitionType`: fade, slide_left, zoom_in, dissolve, etc.
- `HookTechnique`: shocking_fact, intriguing_question, visual_surprise, etc.

**Main Models**:
- `Scene`: Individual video scene with dialogue, image prompts, voice settings, animation flags
- `VideoScript`: Complete video with title, character description, and ordered scenes
- `ElevenLabsSettings`: Voice synthesis settings (stability, style, speed, loudness)
  - Includes `for_tone()` class method that returns optimized settings per voice tone

### Dynamic Prompt System

**Key Innovation**: The prompt template in `src/prompts/scrip_writer_agent.py` uses `create_dynamic_prompt()` which:
1. Extracts all enum values from Pydantic models at runtime
2. Injects them into the prompt template automatically
3. Uses `PydanticOutputParser` for structured output parsing

**Benefit**: When you add new enum values to `models.py`, the prompt automatically includes them - no manual prompt updates needed.

### Module Structure

```
src/
├── models/
│   ├── models.py           # Pydantic data models (Scene, VideoScript, enums)
│   └── __init__.py
├── prompts/
│   └── scrip_writer_agent.py  # Dynamic prompt templates for Agent 1
├── utils/
│   └── file_saver.py       # Utility functions for saving LLM outputs
├── script_generation.py    # Main script generation logic
├── image_generation.py     # Image generation integration (stub)
└── video_assembly.py       # Video assembly logic (stub)
```

## Working with the Codebase

### Adding New Scene Types or Styles

To add a new scene type, image style, voice tone, or transition:

1. **Edit `src/models/models.py`** - Add the new enum value:
```python
class ImageStyle(str, Enum):
    # ... existing values ...
    NEW_STYLE = "new_style"  # Use lowercase with underscores
```

2. **That's it!** The dynamic prompt system will automatically:
   - Include the new value in Agent 1's prompt
   - Accept it as valid input from the LLM
   - Parse it correctly in the output

### Working with Jupyter Notebooks

Main notebooks:
- `notebooks/script_generation.ipynb`: Primary script generation workflow
- `notebooks/dynamic_prompt_example.py`: Example of using dynamic prompts with Pydantic
- `AIVCP.ipynb`: Main orchestration notebook (AI Video Creation Pipeline)

**Best Practice**: Develop functions in notebooks first, then refactor into `.py` modules for reusability.

### Agent Prompt Templates

When modifying Agent 1 prompt (`src/prompts/scrip_writer_agent.py`):

**DO**:
- Use `{chr(10).join(...)}` for multi-line enum listings in f-strings
- Reference enum values dynamically: `get_enum_values(SceneType)`
- Keep instructions clear about using lowercase enum values
- Provide detailed examples and guidelines

**DON'T**:
- Hardcode enum values in the prompt
- Use uppercase enum values (models use lowercase)
- Mix hook techniques with image styles (they're separate fields)

### File Naming Conventions

- Python modules: `snake_case.py`
- Classes: `PascalCase`
- Enum values: `UPPER_CASE` (enum name) = `"lowercase_value"` (actual value)
- Functions: `snake_case()`

## Testing

Tests use a custom test framework (not pytest) with emoji indicators:
- ✅ Test passed
- ❌ Test failed
- 🧪 Test running

**Running Tests**:
```bash
# All tests
python tests/run_tests.py

# Single test file
python tests/test_script_generation.py
```

**Test Coverage** (from `tests/README.md`):
- Environment setup (API keys)
- Module imports
- LLM initialization
- Prompt template creation and formatting
- Simple LLM responses
- Video script generation
- File saving functionality
- Context clearing

## Development Workflow

1. **Always activate virtual environment first**:
   ```bash
   source venv/bin/activate
   ```

2. **For new features**:
   - Update Pydantic models in `src/models/models.py` if needed
   - Models auto-update prompts (dynamic system)
   - Test in Jupyter notebook first
   - Refactor into modules
   - Run tests to verify

3. **For prompt changes**:
   - Edit `src/prompts/scrip_writer_agent.py`
   - Test with `notebooks/dynamic_prompt_example.py`
   - Verify enum values are correctly injected

4. **Before committing**:
   - Ensure `.env` is not included
   - Run tests: `python tests/run_tests.py`
   - Clean up: `make clean` (removes cache files)

## Important Notes

### API Key Security
- **NEVER** hardcode API keys in notebooks or code
- Always use `python-dotenv` to load from `.env`
- `.env` is gitignored - keep it that way

### Scene Structure Requirements

Every video script MUST follow this structure:
1. **First scene**: Hook scene with `hook_technique` set
2. **Following scenes**: Setup → Development → Climax → Resolution
3. **Each scene**:
   - Has detailed `image_create_prompt` (2-3 sentences with lighting, composition, style)
   - Uses lowercase enum values (e.g., `"excited"` not `"EXCITED"`)
   - `hook_technique` only on first scene
   - `video_prompt` is a simple string when `needs_animation: true`

### Character Consistency

The system uses a **fixed character** across all scenes:
- `main_character_description` in `VideoScript` defines the character
- Image prompts should reference "our fixed character" or "the character"
- Only describe clothing/accessories, expression, and pose - NOT physical appearance
- This ensures visual continuity across all scenes

### Animation Decision Guidelines

From `src/models/models.py`:
- **Use animation** (`needs_animation: true`) for: emotional changes, concept demonstrations, dramatic emphasis
- **Use static image** for: simple information delivery, text/diagram focus, calm explanations
- Always provide `animation_purpose` explaining why

## Project Context

This project is in **active development** focusing on Agent 1 (Script Generation). The architecture is designed for extensibility with future agents handling image generation, video animation, and voice synthesis.

Recent focus areas (from git log):
- Agent 1 prompt refinement
- Dynamic prompt system with Pydantic models
- Development environment setup
- Video script generation with structured output

The codebase follows a **hybrid Agile-Waterfall** methodology with weekly development iterations and milestone-based tracking.
