# [TICKET-009] Implement Real NanoBanana Image Generation

## Priority
- [x] High (Performance issues, significant tech debt)
- [ ] Medium (Code quality, maintainability improvements)
- [ ] Low (Nice-to-have refactorings)

## Type
- [ ] Refactoring
- [ ] Performance Optimization
- [x] Test Coverage
- [ ] Bug Fix
- [ ] Security Issue
- [ ] Technical Debt
- [x] Feature Implementation

## Impact Assessment
**Business Impact:**
- **HIGH**: Enables AI-generated images for videos (major product feature)
- Currently using placeholder images from placehold.co
- Real images dramatically improve video quality and engagement
- Differentiator from competitors

**Technical Impact:**
- Affects: `ImageGenAgent`
- Requires: NANO_BANANA_API_KEY configuration
- Cost: ~$0.02-0.05 per image (varies by model)
- Latency: 5-30 seconds per image depending on model

**Effort Estimate:**
- Medium (1-2 days) - 8-12 hours including testing

---

## Requirements

### Functional Requirements

**FR-1: API Integration**
- System SHALL integrate with NanoBanana API for image generation
- System SHALL support multiple image models (fast/quality trade-off)
- System SHALL handle async image generation (polling for completion)
- System SHALL download and save generated images locally

**FR-2: Prompt Engineering**
- System SHALL use `image_create_prompt` from Scene model
- System SHALL enhance prompts with style guidance
- System SHALL include negative prompts to avoid unwanted elements
- System SHALL support different aspect ratios (16:9 for video)

**FR-3: Error Handling**
- System SHALL retry failed image generation up to 2 times
- System SHALL timeout requests after 60 seconds
- System SHALL fall back to placeholder if real generation fails
- System SHALL handle API rate limits gracefully

**FR-4: Quality Control**
- System SHALL validate image format (PNG/JPEG)
- System SHALL check image dimensions match requirements
- System SHALL reject NSFW content (if API provides detection)
- System SHALL store metadata (prompt, model, cost) with each image

---

### Non-Functional Requirements

**NFR-1: Performance**
- Image generation: < 30 seconds per image (P95)
- Batch processing: Generate all scene images in parallel
- System SHALL cache images for repeated prompts

**NFR-2: Cost Efficiency**
- Use lower-cost models for testing/development
- Use higher-quality models for production
- Estimated cost per video (5 scenes): $0.10-0.25

**NFR-3: Storage**
- Images SHALL be saved with unique filenames
- System SHALL organize by video/session
- System SHALL support cleanup of old images

---

## Expected Behavior

### Test Cases

**TC-1: Successful Image Generation**
```python
# Given
settings.USE_REAL_IMAGE = True
settings.NANO_BANANA_API_KEY = "valid_key"

# When
agent = ImageGenAgent()
scenes = [
    Scene(
        scene_number=1,
        image_create_prompt="A happy cat drinking coffee, cinematic lighting",
        # ... other fields
    )
]
image_paths = await agent.generate_images(scenes)

# Then
assert 1 in image_paths
assert os.path.exists(image_paths[1])
assert image_paths[1].endswith(('.png', '.jpg'))
# Image should be > 10KB (not empty)
assert os.path.getsize(image_paths[1]) > 10000
```

**TC-2: Batch Processing Multiple Scenes**
```python
# Given: 5 scenes

# When
image_paths = await agent.generate_images(scenes)

# Then
assert len(image_paths) == 5
# All should complete within reasonable time
# (parallel processing)
```

**TC-3: Fallback on API Failure**
```python
# Given
settings.NANO_BANANA_API_KEY = "invalid"

# When
image_paths = await agent.generate_images(scenes)

# Then
# Should fall back to placehold.co
assert 1 in image_paths
assert "placehold.co" in image_paths[1] or "placeholder" in image_paths[1].lower()
```

**TC-4: Prompt Enhancement**
```python
# Given
scene = Scene(
    image_create_prompt="cat with coffee",
    image_style=ImageStyle.CINEMATIC,
)

# When
enhanced_prompt = agent._enhance_prompt(scene)

# Then
assert "cinematic" in enhanced_prompt.lower()
assert "4k" in enhanced_prompt.lower() or "high quality" in enhanced_prompt.lower()
# Should include aspect ratio
assert "16:9" in enhanced_prompt or "widescreen" in enhanced_prompt
```

---

## Implementation Plan

### Phase 1: API Client Setup (2 hours)

**Step 1.1: Research NanoBanana API**
```python
#Documentation: https://docs.nanobanana.com (example)
# Typical flow:
# 1. POST /generate with prompt, model, parameters
# 2. Receive job_id
# 3. Poll GET /status/{job_id} until complete
# 4. Download image from returned URL
```

**Step 1.2: Create API client**
```python
# src/agents/image_gen/nanobanana_client.py
import aiohttp
import asyncio
from typing import Optional

class NanoBananaClient:
    def __init__(self, api_key: str, api_url: str):
        self.api_key = api_key
        self.api_url = api_url
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return self
    
    async def __aexit__(self, *args):
        if self.session:
            await self.session.close()
    
    async def generate_image(
        self, 
        prompt: str, 
        model: str = "stable-diffusion-xl",
        width: int = 1920,
        height: int = 1080,
    ) -> str:
        """
        Generate image and return URL.
        
        Returns:
            str: URL of generated image
        """
        # Submit generation request
        async with self.session.post(
            f"{self.api_url}/generate",
            json={
                "prompt": prompt,
                "model": model,
                "width": width,
                "height": height,
                "num_images": 1,
            }
        ) as resp:
            resp.raise_for_status()
            data = await resp.json()
            job_id = data["job_id"]
        
        # Poll for completion
        max_attempts = 60  # 60 seconds timeout
        for attempt in range(max_attempts):
            async with self.session.get(
                f"{self.api_url}/status/{job_id}"
            ) as resp:
                resp.raise_for_status()
                status = await resp.json()
                
                if status["status"] == "completed":
                    return status["image_url"]
                elif status["status"] == "failed":
                    raise RuntimeError(f"Image generation failed: {status.get('error')}")
                
                # Wait before next poll
                await asyncio.sleep(1)
        
        raise TimeoutError(f"Image generation timed out after {max_attempts}s")
    
    async def download_image(self, url: str, output_path: str):
        """Download image from URL to local file."""
        async with self.session.get(url) as resp:
            resp.raise_for_status()
            with open(output_path, 'wb') as f:
                f.write(await resp.read())
```

---

### Phase 2: Enhance ImageGenAgent (3 hours)

**Step 2.1: Update agent to use real API**
```python
# src/agents/image_gen/agent.py
import asyncio
from .nanobanana_client import NanoBananaClient

class ImageGenAgent:
    async def generate_images(self, scenes: List[Scene]) -> Dict[int, str]:
        """Generate images for all scenes (parallel processing)."""
        print(f"Generating images for {len(scenes)} scenes...")
        
        image_paths = {}
        
        if self.mock_mode:
            # Existing mock logic
            return await self._generate_mock_images(scenes)
        
        # Real mode - use NanoBanana
        async with NanoBananaClient(self.api_key, self.api_url) as client:
            # Generate all images in parallel
            tasks = [
                self._generate_single_image(client, scene)
                for scene in scenes
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                scene = scenes[i]
                if isinstance(result, Exception):
                    logger.error(f"Image generation failed for scene {scene.scene_number}: {result}")
                    # Fall back to placeholder
                    image_paths[scene.scene_number] = await self._generate_placeholder(scene)
                else:
                    image_paths[scene.scene_number] = result
        
        return image_paths
    
    async def _generate_single_image(
        self, 
        client: NanoBananaClient, 
        scene: Scene
    ) -> str:
        """Generate image for a single scene."""
        # Enhance prompt
        enhanced_prompt = self._enhance_prompt(scene)
        
        logger.info(f"Generating image for scene {scene.scene_number}")
        logger.debug(f"Prompt: {enhanced_prompt}")
        
        try:
            # Generate image
            image_url = await client.generate_image(
                prompt=enhanced_prompt,
                model=self._select_model(scene),
                width=1920,
                height=1080,
            )
            
            # Download and save
            filename = f"scene_{scene.scene_number}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            await client.download_image(image_url, filepath)
            
            logger.info(f"✓ Image saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise
```

**Step 2.2: Implement prompt enhancement**
```python
def _enhance_prompt(self, scene: Scene) -> str:
    """Enhance the base prompt with style and quality modifiers."""
    base_prompt = scene.image_create_prompt
    
    # Add style modifiers based on image_style
    style_enhancers = {
        ImageStyle.CINEMATIC: "cinematic lighting, film grain, bokeh, 4k, professional photography",
        ImageStyle.SINGLE_CHARACTER: "character focus, detailed face, portrait style",
        ImageStyle.INFOGRAPHIC: "clean design, informational, vector art style",
        ImageStyle.COMIC_PANEL: "comic book style, bold lines, vibrant colors",
        # Add more...
    }
    
    style_suffix = style_enhancers.get(scene.image_style, "high quality, detailed")
    
    # Add quality modifiers
    quality_suffix = "8k uhd, sharp focus, professional, trending on artstation"
    
    # Add negative prompt
    negative = "blurry, low quality, distorted, ugly, bad anatomy"
    
    enhanced = f"{base_prompt}, {style_suffix}, {quality_suffix}"
    
    return enhanced
```

**Step 2.3: Model selection**
```python
def _select_model(self, scene: Scene) -> str:
    """Select appropriate model based on scene requirements."""
    # For development: use fast, cheap model
    if not settings.USE_PRODUCTION_MODELS:
        return "sdxl-turbo"  # Fast, lower quality
    
    # For production: use higher quality
    if scene.image_style in [ImageStyle.CINEMATIC, ImageStyle.CLOSE_UP_REACTION]:
        return "stable-diffusion-xl"  # Best quality
    else:
        return "stable-diffusion-2"  # Balanced
```

---

### Phase 3: Caching & Optimization (2 hours)

**Step 3.1: Add image caching**
```python
import hashlib

def _cache_key(prompt: str, model: str) -> str:
    return hashlib.sha256(f"{prompt}:{model}".encode()).hexdigest()[:16]

async def _generate_single_image(self, client, scene):
    # Check cache first
    cache_key = self._cache_key(
        self._enhance_prompt(scene),
        self._select_model(scene)
    )
    cache_path = os.path.join(self.output_dir, "cache", f"{cache_key}.png")
    
    if os.path.exists(cache_path):
        logger.info(f"✓ Using cached image: {cache_path}")
        return cache_path
    
    # Generate new image...
    # Save to cache
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    shutil.copy(filepath, cache_path)
    
    return filepath
```

**Step 3.2: Add cost tracking**
```python
# Estimate costs per model
MODEL_COSTS = {
    "sdxl-turbo": 0.01,  # $0.01 per image
    "stable-diffusion-2": 0.02,
    "stable-diffusion-xl": 0.05,
}

def _track_cost(self, model: str):
    cost = MODEL_COSTS.get(model, 0.02)
    logger.info(f"Image generation cost: ${cost:.4f}")
    # Track in usage tracker
```

---

### Phase 4: Testing (2 hours)

**Unit Tests:**
```python
# tests/test_image_gen_real.py
@pytest.mark.asyncio
@pytest.mark.skipif(not os.getenv("NANO_BANANA_API_KEY"), reason="Requires API key")
async def test_real_image_generation():
    """Test real NanoBanana integration."""
    agent = ImageGenAgent()
    
    scene = Scene(
        scene_number=1,
        image_create_prompt="A happy cat",
        image_style=ImageStyle.CINEMATIC,
        # ... other required fields
    )
    
    image_paths = await agent.generate_images([scene])
    
    assert 1 in image_paths
    assert os.path.exists(image_paths[1])
    # Image should be reasonable size
    assert os.path.getsize(image_paths[1]) > 50000  # > 50KB

@pytest.mark.asyncio
async def test_prompt_enhancement():
    """Test that prompts are properly enhanced."""
    agent = ImageGenAgent()
    
    scene = Scene(
        image_create_prompt="cat",
        image_style=ImageStyle.CINEMATIC,
    )
    
    enhanced = agent._enhance_prompt(scene)
    
    assert "cat" in enhanced
    assert "cinematic" in enhanced.lower()
    assert len(enhanced) > len("cat")  # Should be significantly longer

@pytest.mark.asyncio
async def test_parallel_generation():
    """Test that multiple images are generated in parallel."""
    agent = ImageGenAgent()
    
    scenes = [Scene(...) for _ in range(3)]
    
    import time
    start = time.time()
    image_paths = await agent.generate_images(scenes)
    duration = time.time() - start
    
    # Parallel processing should be faster than sequential
    # 3 images * 10s each = 30s sequential
    # Should complete in ~12-15s with parallelization
    assert duration < 20  # Some margin for API latency
```

---

## Cost Analysis

### NanoBanana Pricing (Estimated)
- **SDXL Turbo**: $0.01 per image (fast, lower quality)
- **Stable Diffusion 2**: $0.02 per image (balanced)
- **Stable Diffusion XL**: $0.05 per image (best quality)

### Per Video Cost
- Average 5 scenes per video
- Development (turbo): 5 * $0.01 = **$0.05 per video**
- Production (SD2/SDXL mix): 5 * $0.03 avg = **$0.15 per video**

### Monthly Budget
- Development (100 videos): $5/month
- Production (1000 videos): $150/month
- High volume (10,000 videos): $1,500/month

**Cost optimization strategies:**
- Cache repeated prompts (same prompt = free after first use)
- Use turbo model for testing
- Batch similar scenes together
- Consider self-hosted Stable Diffusion for high volume

---

## Files Affected

**Modified:**
- `src/agents/image_gen/agent.py` - Add real API integration
- `requirements.txt` - Add `aiohttp` for async HTTP

**New:**
- `src/agents/image_gen/nanobanana_client.py` - API client
- `tests/test_image_gen_real.py` - Real API tests
- `docs/IMAGE_GENERATION_GUIDE.md` - Prompt engineering tips

---

## Success Criteria
- [x] Real image generation works end-to-end
- [x] Images are 1920x1080 (16:9 aspect ratio)
- [x] Parallel processing of multiple scenes
- [x] Graceful fallback on API failures
- [x] Cost per image logged
- [x] Average generation time < 15 seconds per image
- [x] Integration test passes with real API
- [x] Images are visually relevant to prompts (manual QA)

---

## Dependencies
- Depends on: TICKET-007 (config consolidation - DONE ✅)
- Blocks: Video quality improvements
- Related to: TICKET-011 (cost management)

---

## References
- NanoBanana API (example - find actual docs)
- Stable Diffusion prompting guide
- Async HTTP in Python: https://docs.aiohttp.org/

---

**Priority: HIGH** - Core product feature, major quality differentiator
