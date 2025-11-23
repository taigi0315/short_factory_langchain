# TICKET-025 Integration Plan

## Phase 3: Integration into Workflow

### Goal
Integrate VideoEffectAgent into the video generation pipeline so that:
1. After script generation, VideoEffectAgent analyzes the script
2. Recommendations are applied to scenes
3. Scene editor UI shows recommended effects
4. Final video uses the intelligent recommendations

### Integration Points

#### 1. Script Generation API (`/api/scripts/generate`)
**Location:** `src/api/routes/scripts.py`

**Changes:**
- After `ScriptWriterAgent` generates script
- Call `VideoEffectAgent.analyze_script(script)`
- Store recommendations with the script
- Return recommendations in API response

#### 2. Scene Model Enhancement
**Location:** `src/models/models.py`

**Changes:**
- Add optional fields to `Scene` model:
  - `recommended_effect: Optional[str]` - Agent's effect recommendation
  - `recommended_ai_video: Optional[bool]` - Whether AI video is recommended
  - `effect_reasoning: Optional[str]` - Why this effect was chosen

#### 3. Scene Editor Integration
**Location:** `frontend/src/components/SceneEditor.tsx`

**Changes:**
- Display recommended effect as default value
- Show AI video recommendation badge
- Allow users to override recommendations
- Show reasoning on hover/tooltip

#### 4. Video Generation Integration
**Location:** `src/agents/video_gen/agent.py`

**Changes:**
- Use recommended effects when building video
- Prioritize scenes with `recommended_ai_video=true`
- Fall back to defaults if no recommendation

### Implementation Steps

1. ✅ Create VideoEffectAgent (DONE)
2. ✅ Test VideoEffectAgent (DONE)
3. ⏳ Update Scene model with recommendation fields
4. ⏳ Integrate into script generation API
5. ⏳ Update frontend to display recommendations
6. ⏳ Test end-to-end workflow

### API Response Example

```json
{
  "script": {
    "title": "The Power of Thunder",
    "scenes": [
      {
        "scene_number": 1,
        "dialogue": "...",
        "recommended_effect": "shake",
        "recommended_ai_video": true,
        "effect_reasoning": "Effect 'shake': Rapid shake effect | Scene type: hook | High importance (10/10) | AI video recommended for quality"
      }
    ]
  },
  "effect_recommendations": [
    {
      "scene_number": 1,
      "effect": "shake",
      "video_prompt": "...",
      "transition_to_next": "fade",
      "recommend_ai_video": true,
      "reasoning": "..."
    }
  ]
}
```

### UI Mockup

```
Scene 1: Hook
┌─────────────────────────────────────────────┐
│ Dialogue: "Did you know thunder..."        │
│                                             │
│ Effect: [shake ▼] 💡 Recommended           │
│ AI Video: ✅ Recommended (High Impact)      │
│ ℹ️ Shake effect for dramatic impact        │
└─────────────────────────────────────────────┘
```
