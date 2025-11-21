# Dev Mode Documentation

## Overview

Dev Mode is a development dashboard that provides direct access to individual agents for testing and experimentation. It allows developers to test image generation, script writing, and video generation without going through the full pipeline.

## Features

### 1. Image Gen Tab
**Purpose**: Test image generation with different prompts and styles

**Inputs**:
- Prompt: Text description of desired image
- Style: Visual style (Cinematic, Single Character, Infographic, Comic Panel)

**Output**: Generated image preview

**API Endpoint**: `POST /api/dev/generate-image`

### 2. Script & Scenes Tab
**Purpose**: Generate video scripts from story ideas

**Inputs**:
- Story Title
- Story Premise
- Genre
- Target Audience
- Duration

**Output**: Complete video script with scenes

**API Endpoint**: `POST /api/scripts/generate`

### 3. Video Gen Tab
**Purpose**: Test video generation (currently mock implementation)

**Modes**:
- **Text to Video**: Generate video from text prompt
- **Image to Video**: Animate an image with text prompt

**API Endpoints**:
- `POST /api/dev/generate-video`

## Accessing Dev Mode

1. Start the development environment:
```bash
./start_dev.sh
```

2. Navigate to: `http://localhost:3000`

3. Dev Mode dashboard loads automatically

## Configuration

Dev Mode respects the same environment variables:

```bash
# Use real services in Dev Mode
USE_REAL_IMAGE=True
NANO_BANANA_API_KEY=your_key

# Or use mock mode (default)
USE_REAL_IMAGE=False
```

## Common Use Cases

### Testing Image Prompts

1. Go to Image Gen tab
2. Enter prompt: "A cinematic coffee shop at sunrise"
3. Select style: "Cinematic"
4. Click "Generate Image"
5. Review result and iterate on prompt

### Validating Scripts

1. Go to Script & Scenes tab
2. Fill in story details
3. Click "Generate Script"
4. Review scenes and dialogue
5. Verify image prompts and voice tones

### Video Generation Testing

1. Go to Video Gen tab
2. Select mode (Text to Video or Image to Video)
3. Enter prompt
4. Click "Generate Video"
5. Preview generated video

## Gotchas

1. **Mock Mode by Default**: Dev Mode uses mock data unless real services are enabled
2. **API Keys Required**: Real mode requires valid API keys in `.env`
3. **Frontend Port**: Dev Mode runs on port 3000, API on port 8001

---

**Last Updated**: 2025-01-21
