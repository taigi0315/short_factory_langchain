# TICKET-023: Manual Video Upload Workflow (EPIC)

## 🎯 Overview

Transform the dev pipeline into a scene-by-scene editor that allows users to manually create and upload AI videos for specific scenes while keeping automated image+effect generation for others. This hybrid approach provides cost control and quality flexibility.

## 🎬 User Workflow

### Current Flow (Automated)
```
Story Finder → Script Writer → Generate All Images → Generate All Audio → Build Video
```

### New Flow (Hybrid Manual/Auto)
```
Story Finder → Script Writer → Scene-by-Scene Editor → Build Final Video
```

## 📋 Requirements

### Phase 1: Scene-by-Scene UI Editor

**Scene Grid Layout:**
Each scene should display in a row with these columns:

| Scene # | Script/Dialogue | Image | Video | Effect | Actions |
|---------|----------------|-------|-------|--------|---------|
| 1 | [dialogue text] | [img preview] | [video preview] | [dropdown] | [buttons] |
| 2 | [dialogue text] | [img preview] | [video preview] | [dropdown] | [buttons] |
| ... | ... | ... | ... | ... | ... |

**Column Details:**

1. **Scene Number & Script**
   - Scene number badge
   - Dialogue text (editable?)
   - Voice tone indicator
   - Scene type badge

2. **Image Column**
   - Placeholder initially
   - "Generate Image" button
   - Image preview when generated
   - "Download Image" button (downloads PNG)
   - "Regenerate" button

3. **Video Column**
   - Placeholder initially
   - "Copy Video Prompt" button (copies `video_prompt` to clipboard)
   - "Upload Video" button (accepts .mp4, .mov, .webm)
   - Video preview when uploaded
   - "Remove Video" button
   - Status indicator: "Using uploaded video" or "Will use image+effect"

4. **Effect Column**
   - Dropdown selector with options:
     - Ken Burns (zoom in)
     - Ken Burns (zoom out)
     - Pan Left
     - Pan Right
     - Static (no effect)
   - AI-suggested effect shown by default (from script)
   - User can override

5. **Actions Column**
   - "Generate Image" button
   - "Download Image" button
   - "Copy Video Prompt" button
   - "Upload Video" button

### Phase 2: Video Prompt Copy Feature

**Copy Button Behavior:**
```
When user clicks "Copy Video Prompt":
1. Get scene.video_prompt from script
2. If video_prompt exists, copy it
3. If not, generate a default prompt:
   "Animate this image: [scene.visual_description]"
4. Show toast: "Video prompt copied! Paste in Veo3/Grok/etc."
```

**Prompt Format:**
```
Scene [X]: [scene.visual_description]

Animation: [scene.video_prompt or default]

Duration: [audio_duration] seconds
Aspect Ratio: 9:16 (vertical)
```

### Phase 3: Video Upload & Storage

**Upload Functionality:**
- Accept video files: .mp4, .mov, .webm
- Validate video:
  - Max size: 100MB
  - Aspect ratio: 9:16 preferred (warn if different)
  - Duration: should match audio duration (warn if different)
- Store in: `generated_assets/videos/scenes/scene_[N]_[hash].mp4`
- Update scene metadata with video path

**Video Preview:**
- Show thumbnail
- Play on hover
- Duration indicator
- File size indicator

### Phase 4: Final Video Assembly

**"Build Final Video" Button:**
- Located at bottom of scene editor
- Shows preview of what will be used:
  - "X scenes with uploaded videos"
  - "Y scenes with image+effect"
- Confirmation dialog before building

**Assembly Logic:**
```python
for scene in scenes:
    if scene.uploaded_video_path exists:
        use uploaded_video
    else:
        use image + selected_effect
    
    combine with audio
```

## 🎨 UI Mockup

```
┌─────────────────────────────────────────────────────────────────┐
│  📝 Script: "K-Pop Demon Hunters"                               │
│  ✓ 7 scenes generated                                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Scene 1 - HOOK                                    [importance: 10]│
├─────────────────────────────────────────────────────────────────┤
│ 📝 Dialogue: "Did you know K-Pop videos hide ancient magic?"   │
│                                                                  │
│ 🖼️ Image          📹 Video           🎬 Effect      ⚡ Actions  │
│ ┌──────────┐     ┌──────────┐      ┌──────────┐   ┌─────────┐ │
│ │          │     │          │      │Ken Burns │   │Generate │ │
│ │  [img]   │     │ No video │      │ Zoom In ▼│   │  Image  │ │
│ │          │     │          │      └──────────┘   └─────────┘ │
│ └──────────┘     └──────────┘                     ┌─────────┐ │
│ [Download]       [Copy Prompt]                    │ Upload  │ │
│                  [Upload Video]                   │ Video   │ │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│ Scene 2 - EXPLANATION                             [importance: 5]│
├─────────────────────────────────────────────────────────────────┤
│ 📝 Dialogue: "Ancient Korean shamanism meets modern pop..."    │
│                                                                  │
│ 🖼️ Image          📹 Video           🎬 Effect      ⚡ Actions  │
│ ┌──────────┐     ┌──────────┐      ┌──────────┐   ┌─────────┐ │
│ │          │     │ ▶️ VIDEO │      │  Static  │   │Generate │ │
│ │  [img]   │     │ uploaded │      │    ▼     │   │  Image  │ │
│ │          │     │ 5.2s     │      └──────────┘   └─────────┘ │
│ └──────────┘     └──────────┘                     ┌─────────┐ │
│ [Download]       [Remove Video]                   │ Upload  │ │
│                  [Copy Prompt]                    │ Video   │ │
└─────────────────────────────────────────────────────────────────┘

... (more scenes)

┌─────────────────────────────────────────────────────────────────┐
│                    📊 Summary                                    │
│  • 2 scenes with uploaded videos                                │
│  • 5 scenes will use image + effect                             │
│                                                                  │
│              [🎬 Build Final Video]                             │
└─────────────────────────────────────────────────────────────────┘
```

## 🏗️ Technical Implementation

### Backend Changes

#### 1. New API Endpoints

```python
# Image generation per scene
POST /api/dev/generate-scene-image
{
  "scene_number": 1,
  "script_id": "abc123",
  "prompt": "..."
}

# Video upload
POST /api/dev/upload-scene-video
{
  "scene_number": 1,
  "script_id": "abc123",
  "video_file": <multipart>
}

# Get video prompt for copying
GET /api/dev/scene-video-prompt/{script_id}/{scene_number}

# Final video assembly
POST /api/dev/build-final-video
{
  "script_id": "abc123",
  "scene_configs": [
    {
      "scene_number": 1,
      "use_uploaded_video": true,
      "video_path": "...",
      "effect": "ken_burns_zoom_in"
    },
    ...
  ]
}
```

#### 2. Data Model Updates

```python
class Scene(BaseModel):
    # ... existing fields ...
    uploaded_video_path: Optional[str] = None
    selected_effect: str = "ken_burns_zoom_in"  # User-selected effect
    image_path: Optional[str] = None
    audio_path: Optional[str] = None
```

#### 3. Video Assembly Logic

```python
class VideoGenAgent:
    def build_from_scene_configs(
        self,
        scenes: List[Scene],
        scene_configs: List[SceneConfig]
    ) -> str:
        """Build video using mix of uploaded videos and image+effect"""
        clips = []
        
        for scene, config in zip(scenes, scene_configs):
            if config.use_uploaded_video and config.video_path:
                # Use uploaded video
                clip = VideoFileClip(config.video_path)
            else:
                # Use image + effect
                clip = self._create_image_clip_with_effect(
                    scene.image_path,
                    config.effect,
                    duration
                )
            
            # Add audio
            clip = clip.set_audio(AudioFileClip(scene.audio_path))
            clips.append(clip)
        
        return self._assemble_final_video(clips)
```

### Frontend Changes

#### 1. New Components

```typescript
// SceneEditor.tsx - Main scene-by-scene editor
interface SceneEditorProps {
  script: VideoScript;
  onBuildVideo: (configs: SceneConfig[]) => void;
}

// SceneRow.tsx - Individual scene row
interface SceneRowProps {
  scene: Scene;
  onImageGenerate: () => void;
  onVideoUpload: (file: File) => void;
  onEffectChange: (effect: string) => void;
  onCopyPrompt: () => void;
}

// VideoUploader.tsx - Video upload component
interface VideoUploaderProps {
  sceneNumber: number;
  onUpload: (file: File) => void;
  maxSize: number;
}
```

#### 2. State Management

```typescript
interface SceneState {
  sceneNumber: number;
  imageUrl?: string;
  videoUrl?: string;
  selectedEffect: string;
  isGeneratingImage: boolean;
  isUploadingVideo: boolean;
}

const [sceneStates, setSceneStates] = useState<SceneState[]>([]);
```

## 📝 Implementation Phases

### Phase 1: Backend Foundation (2-3 days)
- [ ] Add `uploaded_video_path` and `selected_effect` to Scene model
- [ ] Create scene image generation endpoint
- [ ] Create video upload endpoint with validation
- [ ] Create video prompt getter endpoint
- [ ] Update VideoGenAgent to support mixed video/image sources

### Phase 2: Scene Editor UI (3-4 days)
- [ ] Create SceneEditor component with grid layout
- [ ] Create SceneRow component
- [ ] Implement image generation per scene
- [ ] Add image download functionality
- [ ] Add effect selector dropdown

### Phase 3: Video Upload (2-3 days)
- [ ] Create VideoUploader component
- [ ] Implement video file validation
- [ ] Add video preview player
- [ ] Implement "Copy Video Prompt" functionality
- [ ] Add video removal functionality

### Phase 4: Final Assembly (2 days)
- [ ] Create "Build Final Video" button with summary
- [ ] Implement mixed video assembly logic
- [ ] Add progress indicator for video building
- [ ] Test end-to-end workflow

### Phase 5: Polish & UX (1-2 days)
- [ ] Add loading states and progress bars
- [ ] Add error handling and user feedback
- [ ] Add keyboard shortcuts
- [ ] Add bulk actions (generate all images, etc.)
- [ ] Mobile responsive design

## 🎯 Success Criteria

- [ ] User can generate images one scene at a time
- [ ] User can download any generated image
- [ ] User can copy video prompt to clipboard
- [ ] User can upload custom videos for any scene
- [ ] User can select/change effects for each scene
- [ ] System correctly builds final video using mix of uploaded videos and image+effect
- [ ] Video quality matches uploaded videos when used
- [ ] Audio syncs correctly with both video types

## 💡 Future Enhancements

- Batch image generation (generate all at once)
- Video trimming/editing in UI
- Effect preview before building
- Save/load scene configurations
- Collaborative editing (multiple users)
- Template scenes (reuse across scripts)

## 📊 Estimated Effort

**Total: 10-14 days**
- Backend: 4-5 days
- Frontend: 5-7 days  
- Testing & Polish: 1-2 days

## 🔗 Dependencies

- TICKET-022 (AI Video Generation Logic) - ✅ Complete
- Current video assembly pipeline
- File upload infrastructure
- Frontend state management

---

**Priority: HIGH**
**Type: EPIC / Feature**
**Complexity: HIGH**
**Impact: HIGH** - Transforms the entire workflow
