# TICKET-025: Video Effect & Transition Agent

## 🎯 Overview
Create an intelligent agent that decides video effects, transitions, and generates video prompts based on the overall story flow. This agent will analyze the entire script to make cohesive decisions about visual continuity and motion.

## 📋 Problem Statement

Currently:
- Effects are selected manually or use a default value
- Video prompts are generic or scene-specific without story context
- Transitions between scenes are decided by the script writer without visual flow consideration
- No intelligent decision-making about which scenes need motion vs. static images

## 🎬 Proposed Solution: VideoEffectAgent

Create a new agent that:
1. **Analyzes the entire script** to understand the story flow
2. **Decides effects** for each scene based on narrative purpose
3. **Writes video prompts** for AI video generation (image-to-video)
4. **Determines transitions** between scenes for visual continuity
5. **Identifies which scenes** truly benefit from AI video vs. image+effect

## 🏗️ Agent Responsibilities

### 1. Effect Selection
**Input:** Full script with all scenes
**Output:** Effect choice for each scene

**Decision Logic:**
```python
def select_effect(scene, prev_scene, next_scene, story_context):
    """
    - Hook scenes: Dynamic effects (Ken Burns zoom, pan)
    - Explanation scenes: Subtle effects or static
    - Visual demo scenes: Pan to show details
    - Conclusion scenes: Zoom out or static
    - High importance scenes: More dynamic effects
    """
```

**Available Effects:**
- `ken_burns_zoom_in`: Slow zoom into image (builds tension, focus)
- `ken_burns_zoom_out`: Slow zoom out (reveals context, conclusion)
- `pan_left`: Horizontal pan left (progression, time passage)
- `pan_right`: Horizontal pan right (exploration, discovery)
- `static`: No movement (stability, clarity)
- `shake`: Rapid shake (action, impact, thunder example)
- `tilt_up`: Vertical tilt up (revelation, awe)
- `tilt_down`: Vertical tilt down (grounding, detail)

### 2. Video Prompt Generation
**Input:** Scene details + story context
**Output:** Detailed prompt for image-to-video AI

**Prompt Structure:**
```
[Scene Context]
Starting Frame: [Image description]
Motion: [Specific camera/subject movement]
Effects: [Visual effects to add]
Mood: [Emotional tone]
Duration: [Seconds]
```

**Example:**
```
Scene 3: Thunder strikes the branch
Starting Frame: Dark forest with a single tree branch
Motion: Rapid shake effect simulating thunder impact, branch trembles
Effects: Flash of light, particles flying, dramatic shadows
Mood: Sudden, shocking, powerful
Duration: 3 seconds
```

### 3. Transition Intelligence
**Input:** Current scene + next scene
**Output:** Optimal transition type

**Decision Logic:**
- **Fade**: Gentle topic shifts, time passage
- **Zoom**: Connecting related concepts, focus changes
- **Slide**: Comparison, progression
- **Dissolve**: Abstract concepts, dream-like
- **Cut**: Fast-paced, energetic content

### 4. AI Video vs. Image+Effect Decision
**Input:** Scene importance, animation needs, budget constraints
**Output:** Boolean decision per scene

**Criteria:**
- `video_importance >= 8`: Strong candidate for AI video
- `needs_animation == true`: Consider AI video
- Complex motion described in `video_prompt`: AI video preferred
- Simple effects (zoom, pan): Image+effect is sufficient

## 📊 Data Flow

```
ScriptWriterAgent
    ↓ (generates script)
VideoEffectAgent
    ↓ (analyzes & enhances)
Enhanced Script with:
    - Optimized effects per scene
    - Detailed video prompts
    - Smart transitions
    - AI video recommendations
    ↓
VideoGenAgent
    ↓ (generates final video)
Final Video
```

## 🔧 Technical Implementation

### Agent Structure

```python
class VideoEffectAgent:
    """
    Intelligent agent for video effects, transitions, and motion planning.
    """
    
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(...)  # Optional: Use LLM for complex decisions
        
    def analyze_script(self, script: VideoScript) -> EnhancedVideoScript:
        """
        Analyze entire script and make decisions about effects, transitions, and video generation.
        
        Returns:
            EnhancedVideoScript with:
                - selected_effect per scene
                - enhanced video_prompt per scene
                - optimized transitions
                - ai_video_recommended flags
        """
        
    def select_effect_for_scene(
        self, 
        scene: Scene, 
        prev_scene: Optional[Scene],
        next_scene: Optional[Scene],
        story_context: str
    ) -> str:
        """Select optimal effect based on scene context"""
        
    def generate_video_prompt(
        self,
        scene: Scene,
        story_context: str
    ) -> str:
        """Generate detailed video prompt for AI video generation"""
        
    def select_transition(
        self,
        current_scene: Scene,
        next_scene: Scene
    ) -> TransitionType:
        """Select optimal transition between scenes"""
        
    def recommend_ai_video(
        self,
        scene: Scene,
        budget_limit: int = 2
    ) -> bool:
        """Decide if scene should use AI video vs. image+effect"""
```

### Prompt Template (Optional LLM Mode)

```python
VIDEO_EFFECT_AGENT_PROMPT = """
You are a Video Effect Director analyzing a video script.

Script: {script_summary}
Scene {scene_number}: {scene_description}

Your tasks:
1. Select the best effect for this scene from: {available_effects}
2. Write a detailed video generation prompt (if AI video is recommended)
3. Recommend transition to next scene from: {available_transitions}
4. Decide if this scene needs AI video (true/false)

Consider:
- Story flow and pacing
- Emotional tone
- Visual continuity
- Scene importance
- Budget constraints (max {max_ai_videos} AI videos)

Output JSON:
{{
    "effect": "ken_burns_zoom_in",
    "video_prompt": "...",
    "transition": "fade",
    "recommend_ai_video": false,
    "reasoning": "..."
}}
"""
```

## 📋 Implementation Phases

### Phase 1: Core Agent (2-3 days)
- [ ] Create `VideoEffectAgent` class in `src/agents/video_effect/agent.py`
- [ ] Implement rule-based effect selection
- [ ] Implement video prompt generation
- [ ] Implement transition selection
- [ ] Add tests

### Phase 2: LLM Integration (Optional, 1-2 days)
- [ ] Create LLM prompt template
- [ ] Integrate Gemini for intelligent decisions
- [ ] Add fallback to rule-based system
- [ ] Test with real scripts

### Phase 3: Integration (1-2 days)
- [ ] Update workflow to call VideoEffectAgent after ScriptWriterAgent
- [ ] Update Scene model if needed
- [ ] Update API endpoints
- [ ] Update frontend to display recommendations

### Phase 4: Advanced Effects (1-2 days)
- [ ] Add new effect types (shake, tilt, etc.)
- [ ] Implement effect parameters (speed, intensity)
- [ ] Add effect preview in UI
- [ ] Test with various content types

## 🎯 Success Criteria

- [ ] Agent selects appropriate effects for different scene types
- [ ] Video prompts are detailed and actionable
- [ ] Transitions feel natural and enhance story flow
- [ ] AI video recommendations are accurate (high importance scenes)
- [ ] System works with both rule-based and LLM modes
- [ ] Integration with existing workflow is seamless

## 💡 Example Output

**Input Script:**
```
Scene 1 (Hook): "Did you know thunder can split trees?"
Scene 2 (Explanation): "Thunder carries 1 billion volts..."
Scene 3 (Visual Demo): "Watch what happens when it strikes"
Scene 4 (Conclusion): "Nature's power is incredible"
```

**VideoEffectAgent Output:**
```
Scene 1:
  - Effect: ken_burns_zoom_in (builds tension)
  - Video Prompt: "Dramatic zoom into dark storm clouds, lightning flashing"
  - Transition to Scene 2: fade
  - AI Video: true (importance: 10)

Scene 2:
  - Effect: static (clarity for explanation)
  - Video Prompt: N/A
  - Transition to Scene 3: dissolve
  - AI Video: false (importance: 5)

Scene 3:
  - Effect: shake (simulates thunder impact)
  - Video Prompt: "Tree branch shaking violently, lightning strike, particles flying"
  - Transition to Scene 4: fade
  - AI Video: true (importance: 9)

Scene 4:
  - Effect: ken_burns_zoom_out (conclusion, perspective)
  - Video Prompt: N/A
  - Transition to End: fade
  - AI Video: false (importance: 6)
```

## 🔗 Dependencies

- TICKET-024 (Image Consistency) - ✅ Complete
- TICKET-023 (Manual Video Workflow) - ✅ Complete
- Current video generation pipeline

## 📊 Estimated Effort

**Total: 5-9 days**
- Core Agent: 2-3 days
- LLM Integration: 1-2 days (optional)
- Integration: 1-2 days
- Advanced Effects: 1-2 days

---

**Priority: MEDIUM**
**Type: Feature / Agent**
**Complexity: MEDIUM-HIGH**
**Impact: HIGH** - Significantly improves video quality and coherence
