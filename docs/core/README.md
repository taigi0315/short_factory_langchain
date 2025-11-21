# Core Configuration Documentation

## Overview

The `src/core/` directory contains centralized configuration management for the entire ShortFactory application. All environment variables and application settings are defined in a single `Settings` class using Pydantic.

## File: `config.py`

### Purpose
Centralized configuration using Pydantic Settings for type-safe environment variable management.

### Key Components

#### Settings Class

```python
class Settings(BaseSettings):
    """Centralized application configuration."""
    
    # LLM Configuration
    llm_model_name: str = "gemini-1.5-flash-latest"
    
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    NANO_BANANA_API_KEY: Optional[str] = None
    ELEVENLABS_API_KEY: Optional[str] = None
    
    # Feature Flags
    USE_REAL_LLM: bool = False
    USE_REAL_IMAGE: bool = False
    USE_REAL_VOICE: bool = False
    
    # Application Settings
    MAX_VIDEO_SCENES: int = 8
    GENERATED_ASSETS_DIR: str = "generated_assets"
```

## Configuration Categories

### 1. LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `llm_model_name` | `gemini-1.5-flash-latest` | Gemini model to use |

**Important**: Use `-latest` suffix for v1beta API compatibility.

### 2. API Keys

| Variable | Required When | Description |
|----------|---------------|-------------|
| `GEMINI_API_KEY` | `USE_REAL_LLM=True` | Google Gemini API key |
| `NANO_BANANA_API_KEY` | `USE_REAL_IMAGE=True` | NanoBanana image generation key |
| `ELEVENLABS_API_KEY` | `USE_REAL_VOICE=True` | ElevenLabs voice synthesis key |

### 3. Feature Flags (Mock vs Real Mode)

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_REAL_LLM` | `False` | Enable real Gemini LLM |
| `USE_REAL_IMAGE` | `False` | Enable real image generation |
| `USE_REAL_VOICE` | `False` | Enable real voice synthesis |

**Design Decision**: Default to mock mode for cost-efficiency and testing.

### 4. Application Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_VIDEO_SCENES` | `8` | Maximum scenes per video |
| `GENERATED_ASSETS_DIR` | `generated_assets` | Output directory for generated files |

## Environment Variable Loading

### .env File

Create `.env` in project root:

```bash
# LLM Configuration
USE_REAL_LLM=True
GEMINI_API_KEY=your_gemini_api_key_here
LLM_MODEL_NAME=gemini-1.5-flash-latest

# Image Generation
USE_REAL_IMAGE=True
NANO_BANANA_API_KEY=your_nanobanana_key_here

# Application
MAX_VIDEO_SCENES=8
GENERATED_ASSETS_DIR=./generated_assets
```

### Environment Variables

Alternatively, set via shell:

```bash
export USE_REAL_LLM=True
export GEMINI_API_KEY=your_key_here
```

### Priority Order

1. Environment variables (highest priority)
2. `.env` file
3. Default values in `Settings` class (lowest priority)

## Usage

### Importing Settings

```python
from src.core.config import settings

# Access configuration
if settings.USE_REAL_LLM:
    print(f"Using model: {settings.llm_model_name}")
```

### Type Safety

Pydantic provides automatic type validation:

```python
settings.MAX_VIDEO_SCENES  # int
settings.USE_REAL_LLM      # bool
settings.GEMINI_API_KEY    # Optional[str]
```

## Boolean Parsing

### Custom Validator

The `parse_bool` validator accepts multiple formats:

```python
# All these are True
USE_REAL_LLM=true
USE_REAL_LLM=True
USE_REAL_LLM=1
USE_REAL_LLM=yes
USE_REAL_LLM=on

# All these are False
USE_REAL_LLM=false
USE_REAL_LLM=False
USE_REAL_LLM=0
USE_REAL_LLM=no
USE_REAL_LLM=off
```

### Case Insensitivity

```python
class Config:
    case_sensitive = False
```

Both `USE_REAL_LLM` and `use_real_llm` work.

## Common Tasks

### Adding a New Setting

1. Add field to `Settings` class:
```python
MY_NEW_SETTING: str = Field(
    default="default_value",
    description="Description of setting"
)
```

2. Add to `.env`:
```bash
MY_NEW_SETTING=custom_value
```

3. Use in code:
```python
from src.core.config import settings
value = settings.MY_NEW_SETTING
```

### Changing Default Model

Update in `.env`:
```bash
LLM_MODEL_NAME=gemini-1.5-pro-latest
```

Or in code (not recommended):
```python
# config.py
llm_model_name: str = Field(default="gemini-1.5-pro-latest")
```

### Enabling Real Services

```bash
# Enable all real services
USE_REAL_LLM=True
USE_REAL_IMAGE=True
USE_REAL_VOICE=True

# Set required API keys
GEMINI_API_KEY=your_key
NANO_BANANA_API_KEY=your_key
ELEVENLABS_API_KEY=your_key
```

## Validation

### API Key Validation

Agents validate API keys at initialization:

```python
if settings.USE_REAL_LLM:
    if not settings.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY required when USE_REAL_LLM=true")
```

### Health Check Validation

The `/health` endpoint checks configuration:

```python
if settings.USE_REAL_LLM and not settings.GEMINI_API_KEY:
    return {"status": "unhealthy", "errors": ["GEMINI_API_KEY not set"]}
```

## Security Best Practices

### 1. Never Commit API Keys

Add to `.gitignore`:
```
.env
.env.*
!.env.example
```

### 2. Use Environment Variables in Production

Don't use `.env` files in production. Use:
- Google Cloud Secret Manager
- Kubernetes Secrets
- Environment variables in Cloud Run

### 3. Rotate Keys Regularly

Change API keys periodically and update configuration.

## Testing

### Mock Mode for Tests

```python
# tests/conftest.py
import pytest
from src.core.config import settings

@pytest.fixture(autouse=True)
def force_mock_mode():
    settings.USE_REAL_LLM = False
    settings.USE_REAL_IMAGE = False
    settings.USE_REAL_VOICE = False
```

### Override Settings in Tests

```python
def test_with_custom_settings(monkeypatch):
    monkeypatch.setattr(settings, "MAX_VIDEO_SCENES", 3)
    # test with custom value
```

## Gotchas and Notes

### 1. Settings are Global

The `settings` object is a singleton:

```python
from src.core.config import settings  # Same instance everywhere
```

### 2. Changes Require Restart

Changing `.env` requires restarting the application:

```bash
# After editing .env
./start_dev.sh  # Restart to load new values
```

### 3. Boolean String Parsing

Be careful with string values:

```bash
# Wrong - will be True!
USE_REAL_LLM="False"  # String "False" is truthy

# Correct
USE_REAL_LLM=False
```

### 4. Optional vs Required

`Optional[str]` means the field can be `None`:

```python
GEMINI_API_KEY: Optional[str] = None  # Can be None
llm_model_name: str = "default"       # Cannot be None
```

## Dependencies

- `pydantic-settings` - Settings management
- `pydantic` - Data validation
- `python-dotenv` - .env file loading (implicit)

## Migration Notes

### Recent Changes

1. **Model Name Update** (2025-01): Changed default from `gemini-1.5-flash` to `gemini-1.5-flash-latest`
2. **Case Insensitivity** (2024-12): Added `case_sensitive=False` for flexibility

---

**Last Updated**: 2025-01-21
**Version**: 1.0
