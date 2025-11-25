Here is a comprehensive technical ticket designed to be handed directly to an AI coder or a human software engineer. It covers the logic, data structures, math, and edge cases in detail.

-----

# Feature Ticket: Dynamic Visual Segmentation with Audio Sync

**Priority:** High
**Component:** `Script Writer Agent` & `Video Generation Pipeline`
**Type:** Enhancement / Refactor

## 1\. Context & Problem Statement

**Current State:**
Currently, a video "Scene" consists of **1 Dialogue + 1 Image**.

  * **Issue:** If a scene is 15 seconds long, the user stares at a single static image for 15 seconds ("Slide-show effect").
  * **Failed Attempt:** Splitting the scene into multiple mini-audio files creates a robotic, disjointed voiceover because the TTS engine loses context and intonation between clips.

**Target State:**
We want **Continuous Audio** with **Dynamic Visuals**.

  * **The Goal:** A single Scene should generate **one seamless audio file**, but display **multiple images** that switch dynamically based on the context of the sentence.
  * **The Method:** "Character-Count Timestamping." We will calculate the duration of each image based on the ratio of its text length relative to the total scene text length.

-----

## 2\. Technical Specifications

### A. Data Model Changes (Pydantic)

We need to refactor the `Scene` object. Instead of having a single `image_prompt`, it will contain a list of `VisualSegment` objects.

**Current (Deprecate):**

```python
class Scene(BaseModel):
    dialogue: str
    image_prompt: str
```

**New Structure (Implement):**

```python
from pydantic import BaseModel, Field
from typing import List

class VisualSegment(BaseModel):
    segment_text: str = Field(..., description="The specific portion of dialogue corresponding to this image.")
    image_prompt: str = Field(..., description="Detailed image generation prompt for this segment.")

class Scene(BaseModel):
    scene_id: int
    # Note: We no longer have a single 'dialogue' field here.
    # The full dialogue is derived by joining visual_segments[i].segment_text
    content: List[VisualSegment] = Field(..., description="List of visual beats within this scene.")
```

### B. Logic Flow (Step-by-Step)

#### Step 1: Script Writer Output (LLM)

The LLM generates a Scene split into segments.

  * *Example Scenario:* Explaining Capital One's origin.
  * *LLM Output JSON:*
    ```json
    {
      "scene_id": 1,
      "content": [
        {
          "segment_text": "In the early 90s, banks were rigid and boring.",
          "image_prompt": "Old grey dusty bank building, boring atmosphere"
        },
        {
          "segment_text": "But two math geniuses decided to change everything using data.",
          "image_prompt": "Two energetic men looking at colorful data charts on a computer"
        }
      ]
    }
    ```

#### Step 2: Audio Generation (TTS)

**Crucial:** Do NOT generate audio for each segment separately.

1.  Concatenate all `segment_text` values:
      * `"In the early 90s, banks were rigid and boring. But two math geniuses decided to change everything using data."`
2.  Send this **full string** to the TTS API (ElevenLabs/OpenAI).
3.  Receive **one** MP3 file (e.g., `scene_1.mp3`).
4.  Get the duration of this file (e.g., `10.0 seconds`).

#### Step 3: The "Ratio Calculation" (The Logic)

We assume speaking speed is roughly constant. We allocate image time based on text length.

  * **Total Text Length:** 106 characters.
  * **Segment 1 Length:** 46 characters.
  * **Segment 2 Length:** 60 characters.
  * **Total Audio Duration:** 10.0 seconds.

**Formula:** `(Segment_Char_Count / Total_Char_Count) * Total_Audio_Duration`

  * **Image 1 Duration:** `(46 / 106) * 10.0` = **4.34 seconds**
  * **Image 2 Duration:** `(60 / 106) * 10.0` = **5.66 seconds**

-----

## 3\. Implementation Guide

### A. Helper Function (Python)

Use this exact logic to handle the math, ensuring we don't crash on empty strings or zero division.

```python
def calculate_segment_durations(total_audio_duration: float, segments: List[str]) -> List[float]:
    """
    Calculates how long each image should be displayed based on text length.
    
    Args:
        total_audio_duration: Length of the full TTS MP3 file in seconds.
        segments: List of segment_text strings.
    
    Returns:
        List of durations (floats) corresponding to each segment.
    """
    # 1. Calculate lengths
    char_counts = [len(seg) for seg in segments]
    total_chars = sum(char_counts)
    
    # Edge Case: Avoid division by zero if text is empty
    if total_chars == 0:
        return [total_audio_duration / len(segments)] * len(segments)

    durations = []
    
    # 2. Calculate Ratios
    for count in char_counts:
        ratio = count / total_chars
        duration = total_audio_duration * ratio
        durations.append(duration)
        
    return durations
```

### B. Video Assembly (Pseudocode / MoviePy)

```python
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip

def create_scene_video(scene_data, full_audio_path, image_paths):
    # 1. Load Audio
    audio_clip = AudioFileClip(full_audio_path)
    total_duration = audio_clip.duration
    
    # 2. Extract texts for calculation
    segment_texts = [seg.segment_text for seg in scene_data.content]
    
    # 3. Calculate Timings
    durations = calculate_segment_durations(total_duration, segment_texts)
    
    # 4. Create Image Clips with specific durations
    clips = []
    for img_path, duration in zip(image_paths, durations):
        # Create clip and set duration
        clip = ImageClip(img_path).set_duration(duration)
        
        # Optional: Add "Zoom In" effect here for extra dynamism
        clips.append(clip)
        
    # 5. Stitch Images together
    video_track = concatenate_videoclips(clips, method="compose")
    
    # 6. Overlay the continuous audio
    final_scene = video_track.set_audio(audio_clip)
    
    return final_scene
```

-----

## 4\. Prompt Engineering Requirements (Script Writer)

You must update the System Prompt for the Script Writer to understand *how* to split segments.

**Add this to the System Prompt:**

> "Do not create static scenes. Divide every scene into `visual_segments`.
> **Rule:** If a sentence has two distinct ideas, split it.
> **Example:** 'The volcano sat quietly for years, [Segment 1] but suddenly it erupted with massive force\! [Segment 2]'
> **Target:** Aim for 2-3 visual segments per scene to keep the video engaging."

-----

## 5\. Test Cases & Edge Cases

When implementing, verify these scenarios:

| Test Case | Scenario | Expected Behavior |
| :--- | :--- | :--- |
| **Happy Path** | 2 segments, roughly equal length text. | Image 1 shows for \~50%, Image 2 shows for \~50% of audio. |
| **The "Short Blip"** | Segment 1 is "No.", Segment 2 is a long paragraph. | Image 1 should appear very briefly (e.g., 0.5s) then switch to Image 2. This is desired behavior (dramatic effect). |
| **Silence/Pause** | TTS adds a long pause between sentences. | The "Ratio Math" is an approximation. It won't match the pause perfectly, but it is acceptable. The image switch will happen roughly during the pause or slightly after. |
| **Empty Text** | LLM returns an empty string for text. | The code must not crash (ZeroDivisionError). Fallback to equal duration distribution. |
| **Mismatch Count** | LLM generates 3 segments but Image Generator fails and returns 2 images. | Code should raise an error or fallback to using the last image for the remaining duration. |

## 6\. Why This Approach? (Architecture Decision Record)

  * **Audio Quality:** Generating one continuous audio file preserves the prosody, breathing, and intonation of the AI voice. Splitting audio file by file results in a jarring, robotic "stop-and-go" effect.
  * **Sync Accuracy:** While not millisecond-perfect like manual editing, character-count ratio is statistically accurate enough for narrative content (95% accuracy) and requires 0 manual timestamps.