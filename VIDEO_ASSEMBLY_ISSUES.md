# Video Assembly Issues - Fix Plan

## Issue 1: No Title Overlay
**Error**: `Invalid font Arial-Bold, pillow failed to use it with error cannot open resource`

**Root Cause**: ImageMagick or required fonts not installed/configured properly

**Solutions**:
1. Use a built-in font that doesn't require ImageMagick
2. Install ImageMagick: `brew install imagemagick`
3. Use PIL/Pillow fonts instead of TextClip

**Recommended Fix**: Switch to using a system font or skip ImageMagick dependency

## Issue 2: No Subtitles
**Root Cause**: Code doesn't generate subtitles - only attempts title overlay

**Current Code**: Only has title overlay logic (lines 100-124 in video_assembly/agent.py)

**Required**: Add subtitle generation per scene based on dialogue/segment_text

**Implementation Needed**:
- Parse scene.content (VisualSegment objects) for segment_text
- Create TextClip for each subtitle with timing
- Overlay subtitles on video at appropriate timestamps

## Issue 3: 1:1 Aspect Ratio (Should be 9:16)
**Root Cause**: Gemini `gemini-2.5-flash-image-preview` only generates 1024x1024 images

**Evidence**: 
```
generated_assets/images/scene_1_0_728fff3d.png: PNG image data, 1024 x 1024
```

**Solutions**:
1. **Crop to 9:16**: Crop center 576x1024 from 1024x1024
2. **Resize to 9:16**: Resize to 1080x1920 (standard vertical video)
3. **Use different model**: Switch to a model that supports aspect ratios

**Recommended Fix**: Add post-processing to crop/resize images to 9:16 after generation

## Implementation Priority:
1. **Fix aspect ratio** (critical - affects all videos)
2. **Add subtitles** (important for engagement)
3. **Fix title overlay** (nice to have - can work around)
