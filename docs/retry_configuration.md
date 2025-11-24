# Image Generation Retry Configuration

## Overview
The image generation retry logic is now fully configurable through `src/core/config.py`. The frontend dynamically fetches these settings from the backend at runtime.

## Configuration Settings

### `IMAGE_GENERATION_MAX_RETRIES`
- **Default**: `5`
- **Range**: 1-10
- **Description**: Maximum number of retry attempts per scene

### `IMAGE_GENERATION_RETRY_DELAYS`
- **Default**: `[5, 15, 30, 60]` (seconds)
- **Description**: Exponential backoff delay sequence
  - 1st retry: wait 5 seconds
  - 2nd retry: wait 15 seconds
  - 3rd retry: wait 30 seconds
  - 4th+ retries: wait 60 seconds (uses last value)

### `IMAGE_GENERATION_SCENE_DELAY`
- **Default**: `5` seconds
- **Range**: 1-60
- **Description**: Delay between successful scene generations to prevent rate limiting

## How to Customize

### Option 1: Environment Variables
Create/edit `.env` file:
```bash
IMAGE_GENERATION_MAX_RETRIES=5
IMAGE_GENERATION_RETRY_DELAYS=[5,15,30,60]
IMAGE_GENERATION_SCENE_DELAY=5
```

### Option 2: Direct Config Edit
Edit `src/core/config.py`:
```python
IMAGE_GENERATION_MAX_RETRIES: int = Field(default=5, ...)
IMAGE_GENERATION_RETRY_DELAYS: List[int] = Field(default=[5, 15, 30, 60], ...)
IMAGE_GENERATION_SCENE_DELAY: int = Field(default=5, ...)
```

## Example Scenarios

### Conservative (Avoid Rate Limits)
```python
IMAGE_GENERATION_MAX_RETRIES = 5
IMAGE_GENERATION_RETRY_DELAYS = [10, 30, 60, 120]  # 10s, 30s, 1m, 2m
IMAGE_GENERATION_SCENE_DELAY = 10  # 10s between scenes
```

### Aggressive (Fast but risky)
```python
IMAGE_GENERATION_MAX_RETRIES = 3
IMAGE_GENERATION_RETRY_DELAYS = [2, 5, 10]  # 2s, 5s, 10s
IMAGE_GENERATION_SCENE_DELAY = 2  # 2s between scenes
```

### Current Production Settings
```python
IMAGE_GENERATION_MAX_RETRIES = 5
IMAGE_GENERATION_RETRY_DELAYS = [5, 15, 30, 60]  # 5s, 15s, 30s, 1m
IMAGE_GENERATION_SCENE_DELAY = 5  # 5s between scenes
```

## API Endpoint

Frontend fetches config from:
```
GET /api/dev/retry-config
```

Response:
```json
{
  "max_retries": 5,
  "retry_delays_seconds": [5, 15, 30, 60],
  "scene_delay_seconds": 5
}
```

## Frontend Implementation

The frontend automatically:
1. Fetches retry config on "Generate Full Video" click
2. Uses the config values for all retry logic
3. Falls back to defaults if fetch fails
4. Logs the configuration being used

## Benefits

✅ **Centralized Configuration**: All retry settings in one place  
✅ **Dynamic Updates**: No frontend rebuild needed to change delays  
✅ **Environment-Specific**: Different settings for dev/staging/prod  
✅ **Flexible**: Easy to tune based on API rate limits  
✅ **Transparent**: Logs show exact configuration being used
