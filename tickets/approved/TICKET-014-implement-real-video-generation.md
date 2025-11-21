# TICKET-014: Implement Real Video Generation

**Created:** 2025-01-21  
**Status:** APPROVED (Pre-approved by Architect)  
**Priority:** HIGH  
**Effort:** 3-4 days  
**Owner:** Backend Engineer

---

## Problem Statement

Currently, `VideoGenAgent` uses a basic MoviePy implementation that creates simple videos with text overlays and placeholder images. For production, we need professional-quality video assembly with real images, voice audio, transitions, and effects.

**Current State:**
- Mock video generation using MoviePy
- Text overlays on placeholder images
- No real audio integration
- Basic transitions only
- Suitable for development testing only

**Desired State:**
- Professional video assembly with real images and audio
- Smooth transitions between scenes
- Support for 16:9 aspect ratio, 1080p resolution
- Optimized rendering performance (< 2 minutes for 60s video)
- Production-ready output quality

---

## Proposed Solution

### Approach: Enhanced MoviePy Implementation

After evaluation, we'll enhance the existing MoviePy approach rather than integrate an external service. This provides:
- **Full Control**: Complete control over video assembly logic
- **Cost Efficiency**: No per-video API costs
- **Flexibility**: Easy to customize transitions, effects, timing
- **Reliability**: No external API dependencies

### 1. Enhanced Video Assembly

Update `src/agents/video_gen/agent.py`:

```python
from moviepy.editor import (
    VideoFileClip, ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, TextClip, ColorClip
)
from moviepy.video.fx import fadein, fadeout, resize
from typing import List
from pathlib import Path

class VideoGenAgent:
    """Enhanced video generation with real images and audio."""
    
    def __init__(self, use_real: bool = False):
        self.use_real = use_real
        self.output_dir = Path(settings.GENERATED_ASSETS_DIR) / "videos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_video(
        self,
        script: VideoScript,
        images: List[Path],
        audio: Path,
        style: ImageStyle = ImageStyle.CINEMATIC
    ) -> Path:
        """Generate video from script, images, and audio."""
        
        if not self.use_real:
            return self._generate_mock_video(script)
        
        # Load audio to get total duration
        audio_clip = AudioFileClip(str(audio))
        total_duration = audio_clip.duration
        
        # Calculate scene durations
        scene_durations = self._calculate_scene_durations(
            script.scenes, 
            total_duration
        )
        
        # Create scene clips
        scene_clips = []
        for i, (scene, image_path, duration) in enumerate(
            zip(script.scenes, images, scene_durations)
        ):
            clip = self._create_scene_clip(
                scene, 
                image_path, 
                duration,
                style
            )
            scene_clips.append(clip)
        
        # Apply transitions
        video_clip = self._apply_transitions(scene_clips, script.scenes)
        
        # Add audio
        final_clip = video_clip.set_audio(audio_clip)
        
        # Render video
        output_path = self.output_dir / f"video_{script.title[:30]}_{int(time.time())}.mp4"
        
        final_clip.write_videofile(
            str(output_path),
            fps=30,
            codec='libx264',
            audio_codec='aac',
            preset='medium',  # Balance between speed and quality
            threads=4,
            logger=None  # Suppress MoviePy logging
        )
        
        # Cleanup
        audio_clip.close()
        video_clip.close()
        final_clip.close()
        
        logger.info(f"Video generated: {output_path} ({total_duration:.1f}s)")
        return output_path
    
    def _create_scene_clip(
        self,
        scene: Scene,
        image_path: Path,
        duration: float,
        style: ImageStyle
    ) -> VideoClip:
        """Create a video clip for a single scene."""
        
        # Load and resize image to 1080p (1920x1080)
        img_clip = ImageClip(str(image_path))
        img_clip = img_clip.resize(height=1080)
        
        # Center crop to 16:9 if needed
        if img_clip.w / img_clip.h != 16/9:
            target_width = int(1080 * 16/9)
            img_clip = img_clip.crop(
                x_center=img_clip.w/2,
                y_center=img_clip.h/2,
                width=target_width,
                height=1080
            )
        
        # Set duration
        img_clip = img_clip.set_duration(duration)
        
        # Apply Ken Burns effect (slow zoom/pan)
        if style in [ImageStyle.CINEMATIC, ImageStyle.DRAMATIC]:
            img_clip = self._apply_ken_burns(img_clip, duration)
        
        # Add text overlay if needed
        if scene.text_overlay:
            text_clip = self._create_text_overlay(
                scene.text_overlay,
                duration,
                style
            )
            return CompositeVideoClip([img_clip, text_clip])
        
        return img_clip
    
    def _apply_ken_burns(self, clip: VideoClip, duration: float) -> VideoClip:
        """Apply Ken Burns effect (slow zoom and pan)."""
        
        def zoom_effect(get_frame, t):
            """Gradually zoom in over time."""
            frame = get_frame(t)
            zoom_factor = 1 + (t / duration) * 0.1  # 10% zoom over duration
            h, w = frame.shape[:2]
            new_h, new_w = int(h * zoom_factor), int(w * zoom_factor)
            
            # Resize and center crop
            from cv2 import resize, INTER_LINEAR
            zoomed = resize(frame, (new_w, new_h), interpolation=INTER_LINEAR)
            
            y_start = (new_h - h) // 2
            x_start = (new_w - w) // 2
            
            return zoomed[y_start:y_start+h, x_start:x_start+w]
        
        return clip.fl(zoom_effect)
    
    def _create_text_overlay(
        self,
        text: str,
        duration: float,
        style: ImageStyle
    ) -> TextClip:
        """Create text overlay for scene."""
        
        # Style-specific text formatting
        font_sizes = {
            ImageStyle.CINEMATIC: 60,
            ImageStyle.VIBRANT: 70,
            ImageStyle.MINIMALIST: 50,
            ImageStyle.DRAMATIC: 65
        }
        
        text_clip = TextClip(
            text,
            fontsize=font_sizes.get(style, 60),
            color='white',
            font='Arial-Bold',
            stroke_color='black',
            stroke_width=2,
            method='caption',
            size=(1600, None)  # Max width, auto height
        )
        
        # Position at bottom center
        text_clip = text_clip.set_position(('center', 'bottom'))
        text_clip = text_clip.set_duration(duration)
        
        # Fade in/out
        text_clip = text_clip.fadein(0.5).fadeout(0.5)
        
        return text_clip
    
    def _calculate_scene_durations(
        self,
        scenes: List[Scene],
        total_duration: float
    ) -> List[float]:
        """Calculate duration for each scene based on dialogue length."""
        
        # Weight by dialogue length
        dialogue_lengths = [len(scene.dialogue) for scene in scenes]
        total_length = sum(dialogue_lengths)
        
        durations = [
            (length / total_length) * total_duration
            for length in dialogue_lengths
        ]
        
        return durations
    
    def _apply_transitions(
        self,
        clips: List[VideoClip],
        scenes: List[Scene]
    ) -> VideoClip:
        """Apply transitions between scene clips."""
        
        transition_duration = 0.5  # 500ms transitions
        
        # Apply fade out to all clips except last
        for i, clip in enumerate(clips[:-1]):
            clips[i] = clip.fadeout(transition_duration)
        
        # Apply fade in to all clips except first
        for i, clip in enumerate(clips[1:], 1):
            clips[i] = clip.fadein(transition_duration)
        
        # Concatenate with crossfade
        return concatenate_videoclips(clips, method="compose")
```

### 2. Configuration

Add to `.env`:

```bash
# Video Generation
USE_REAL_VIDEO=true
VIDEO_RESOLUTION=1080p  # 1080p or 720p
VIDEO_FPS=30
VIDEO_QUALITY=medium  # fast, medium, slow (ffmpeg preset)
```

Add to `src/core/config.py`:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Video generation
    USE_REAL_VIDEO: bool = Field(default=False)
    VIDEO_RESOLUTION: str = Field(default="1080p")
    VIDEO_FPS: int = Field(default=30)
    VIDEO_QUALITY: str = Field(default="medium")
```

### 3. Performance Optimization

```python
# Parallel processing for multiple videos
async def generate_videos_batch(
    scripts: List[VideoScript],
    images_list: List[List[Path]],
    audios: List[Path]
) -> List[Path]:
    """Generate multiple videos in parallel."""
    
    tasks = [
        generate_video(script, images, audio)
        for script, images, audio in zip(scripts, images_list, audios)
    ]
    
    return await asyncio.gather(*tasks)

# Caching for identical videos
def get_video_cache_key(script: VideoScript, images: List[Path], audio: Path) -> str:
    """Generate cache key for video."""
    content = f"{script.json()}|{[str(p) for p in images]}|{str(audio)}"
    return hashlib.sha256(content.encode()).hexdigest()
```

---

## Success Criteria

- [ ] Videos generated with real images and audio
- [ ] Smooth transitions between scenes (fade in/out)
- [ ] 16:9 aspect ratio, 1080p resolution
- [ ] Ken Burns effect applied to scenes (subtle zoom/pan)
- [ ] Text overlays render correctly
- [ ] Generation time < 2 minutes for 60-second video
- [ ] Video quality suitable for social media (YouTube, TikTok, Instagram)
- [ ] Integration test passes with real images and audio
- [ ] Documentation updated in `docs/agents/README.md`

---

## Testing Plan

### Unit Tests

```python
# tests/agents/test_video_gen.py

@pytest.mark.asyncio
async def test_video_generation_with_real_assets():
    """Test video generation with real images and audio."""
    agent = VideoGenAgent(use_real=True)
    
    # Load test script, images, audio
    script = VideoScript(...)  # Test script
    images = [Path("test_image1.jpg"), Path("test_image2.jpg")]
    audio = Path("test_audio.mp3")
    
    video_path = await agent.generate_video(script, images, audio)
    
    assert video_path.exists()
    assert video_path.suffix == ".mp4"
    
    # Verify video properties
    clip = VideoFileClip(str(video_path))
    assert clip.duration > 0
    assert clip.size == (1920, 1080)  # 1080p
    assert clip.fps == 30
    clip.close()

def test_scene_duration_calculation():
    """Test scene duration calculation based on dialogue length."""
    agent = VideoGenAgent()
    
    scenes = [
        Scene(dialogue="Short", ...),
        Scene(dialogue="Much longer dialogue here", ...)
    ]
    
    durations = agent._calculate_scene_durations(scenes, total_duration=10.0)
    
    assert len(durations) == 2
    assert sum(durations) == pytest.approx(10.0)
    assert durations[1] > durations[0]  # Longer dialogue = longer duration
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_video_pipeline():
    """Test complete pipeline: script -> images -> audio -> video."""
    
    # Generate script
    script_agent = ScriptWriterAgent(use_real=True)
    script = await script_agent.generate_script("AI revolution")
    
    # Generate images
    image_agent = ImageGenAgent(use_real=True)
    images = await image_agent.generate_images_for_script(script)
    
    # Generate audio
    video_agent = VideoGenAgent(use_real=True)
    audio = await video_agent.generate_voice(script.full_dialogue, VoiceTone.ENTHUSIASTIC)
    
    # Generate video
    video_path = await video_agent.generate_video(script, images, audio)
    
    assert video_path.exists()
    assert video_path.stat().st_size > 1_000_000  # At least 1MB
```

### Manual Testing

1. **Visual Quality**:
   - Generate videos with different styles
   - Verify image quality, transitions, text overlays
   - Check for artifacts or glitches

2. **Performance**:
   - Measure generation time for 30s, 60s, 90s videos
   - Verify < 2 minutes for 60s video
   - Monitor CPU/memory usage

3. **Compatibility**:
   - Upload to YouTube, TikTok, Instagram
   - Verify playback works correctly
   - Check aspect ratio and quality

---

## Implementation Steps

1. **Enhanced Scene Clip Creation** (4 hours)
   - Implement `_create_scene_clip` with image loading and resizing
   - Add Ken Burns effect
   - Add text overlay support

2. **Transition System** (2 hours)
   - Implement `_apply_transitions`
   - Test fade in/out, crossfade
   - Optimize transition timing

3. **Audio Integration** (2 hours)
   - Integrate audio with video
   - Calculate scene durations based on audio
   - Sync audio with scene changes

4. **Performance Optimization** (3 hours)
   - Optimize rendering settings (codec, preset, threads)
   - Implement caching for identical videos
   - Add parallel processing for batch generation

5. **Testing** (3 hours)
   - Write unit tests
   - Write integration tests
   - Manual QA for video quality

6. **Documentation** (1 hour)
   - Update `docs/agents/README.md`
   - Add video generation examples
   - Document configuration options

---

## Dependencies

- **Completed**: TICKET-009 (images), TICKET-013 (voice) ✅
- **Blocks**: Production launch (final piece of pipeline)

---

## Risks & Mitigation

### Risk: Slow Rendering Performance

**Mitigation:**
- Use optimized ffmpeg presets (`medium` or `fast`)
- Reduce resolution to 720p if needed
- Implement queue-based async processing
- Consider GPU acceleration (ffmpeg with NVENC)

### Risk: Video Quality Issues

**Mitigation:**
- Manual QA for first 100 videos
- A/B testing different codecs and settings
- Iterative refinement based on feedback

### Risk: High Memory Usage

**Mitigation:**
- Close clips after rendering
- Process videos sequentially if memory constrained
- Monitor memory usage, add limits if needed

---

## References

- MoviePy Documentation: https://zulko.github.io/moviepy/
- FFmpeg Presets: https://trac.ffmpeg.org/wiki/Encode/H.264
- Ken Burns Effect: https://en.wikipedia.org/wiki/Ken_Burns_effect

---

## 🏛️ Architect Review & Approval

**Reviewed by:** Architect Agent  
**Review Date:** 2025-01-21  
**Decision:** ✅ APPROVED (Pre-approved)

**Strategic Rationale:**
- **Final Pipeline Piece**: Completes end-to-end video generation capability
- **Most Complex Integration**: Requires images + audio + transitions + effects
- **Production Blocker**: Cannot launch without professional video output
- **MoviePy Approach**: Cost-effective, flexible, full control

**Implementation Phase:** Phase 1, Week 2  
**Sequence Order:** #3 (After TICKET-009 and TICKET-013)

**Architectural Guidance:**
- **Performance First**: Optimize rendering settings for speed without sacrificing quality
- **Modular Design**: Separate scene creation, transitions, audio sync into distinct methods
- **Caching Strategy**: Cache identical videos to avoid re-rendering
- **Quality Assurance**: Manual QA process for first 100 videos

**Estimated Timeline:** 3-4 days  
**Recommended Owner:** Backend engineer with video processing experience

---

**Priority: HIGH** - Core product feature, blocks production launch
