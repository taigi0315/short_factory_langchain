"""
Director Agent

Transforms video scripts into cinematically directed shot lists with visual coherence,
narrative flow, and emotional impact.
"""

import structlog
from typing import List, Optional
import json
from google import genai
from google.genai import types

from src.core.config import settings
from src.models.models import VideoScript, Scene, SceneType
from src.agents.director.models import (
    CinematicDirection,
    DirectedScene,
    DirectedScript,
    StoryBeat,
    EmotionalArc
)
from src.agents.director.cinematic_language import (
    ShotType, CameraMovement, CameraAngle, LightingMood, CompositionRule,
    SHOT_TYPE_GUIDE, CAMERA_MOVEMENT_GUIDE, EMOTION_TO_VISUAL
)

logger = structlog.get_logger()


class DirectorAgent:
    """
    Cinematic Director Agent
    
    Analyzes video scripts and creates detailed cinematic direction including:
    - Shot types and compositions
    - Camera movements and angles
    - Visual continuity between scenes
    - Emotional arc mapping
    - Enhanced prompts for image/video generation
    """
    
    def __init__(self):
        """Initialize the Director Agent"""
        self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        logger.info("DirectorAgent initialized")
    
    async def analyze_script(self, script: VideoScript) -> DirectedScript:
        """
        Analyze script and create cinematic direction.
        
        Args:
            script: VideoScript to analyze
            
        Returns:
            DirectedScript with complete cinematic direction
        """
        logger.info("Analyzing script for cinematic direction", title=script.title, scenes=len(script.scenes))
        
        try:
            # 1. Identify story beats
            story_beats = self._identify_story_beats(script)
            logger.info("Identified story beats", beats=len(story_beats.beats))
            
            # 2. Map emotional arc
            emotional_arc = self._map_emotional_arc(script, story_beats)
            logger.info("Mapped emotional arc", peak_scene=emotional_arc.peak_moment)
            
            # 3. Generate cinematic direction for each scene using LLM
            directed_scenes = await self._generate_cinematic_direction(
                script, story_beats, emotional_arc
            )
            logger.info("Generated cinematic direction", directed_scenes=len(directed_scenes))
            
            # 4. Ensure visual continuity
            directed_scenes = self._ensure_visual_continuity(directed_scenes)
            logger.info("Ensured visual continuity")
            
            # 5. Create directed script
            directed_script = DirectedScript(
                original_script=script,
                directed_scenes=directed_scenes,
                visual_theme=self._determine_visual_theme(script),
                emotional_arc=emotional_arc.overall_arc,
                pacing_notes=self._generate_pacing_notes(directed_scenes),
                director_vision=self._generate_director_vision(script, emotional_arc)
            )
            
            logger.info("Script analysis complete", title=script.title)
            return directed_script
            
        except Exception as e:
            logger.error("Failed to analyze script", error=str(e), exc_info=True)
            # Fallback to basic direction
            return self._create_fallback_direction(script)
    
    def _identify_story_beats(self, script: VideoScript) -> EmotionalArc:
        """Identify narrative beats in the script"""
        beats = []
        
        # Analyze scene types to identify beats
        hook_scenes = [s for s in script.scenes if s.scene_type == SceneType.HOOK]
        explanation_scenes = [s for s in script.scenes if s.scene_type == SceneType.EXPLANATION]
        demo_scenes = [s for s in script.scenes if s.scene_type == SceneType.VISUAL_DEMO]
        conclusion_scenes = [s for s in script.scenes if s.scene_type == SceneType.CONCLUSION]
        
        if hook_scenes:
            beats.append(StoryBeat(
                beat_name="Hook",
                scene_numbers=[s.scene_number for s in hook_scenes],
                purpose="Grab attention and create intrigue",
                emotional_tone="mysterious"
            ))
        
        if explanation_scenes[:len(explanation_scenes)//2]:
            beats.append(StoryBeat(
                beat_name="Setup",
                scene_numbers=[s.scene_number for s in explanation_scenes[:len(explanation_scenes)//2]],
                purpose="Establish context and background",
                emotional_tone="calm"
            ))
        
        if demo_scenes or explanation_scenes[len(explanation_scenes)//2:]:
            development_scenes = demo_scenes + explanation_scenes[len(explanation_scenes)//2:]
            beats.append(StoryBeat(
                beat_name="Development",
                scene_numbers=[s.scene_number for s in development_scenes],
                purpose="Core content delivery",
                emotional_tone="excitement"
            ))
        
        if conclusion_scenes:
            beats.append(StoryBeat(
                beat_name="Resolution",
                scene_numbers=[s.scene_number for s in conclusion_scenes],
                purpose="Wrap up and provide closure",
                emotional_tone="triumph"
            ))
        
        # Find peak moment (usually middle or 2/3 through)
        peak_scene = script.scenes[len(script.scenes) * 2 // 3].scene_number if script.scenes else 1
        
        return EmotionalArc(
            beats=beats,
            overall_arc=f"Journey from {beats[0].emotional_tone} to {beats[-1].emotional_tone}" if beats else "Standard arc",
            peak_moment=peak_scene
        )
    
    def _map_emotional_arc(self, script: VideoScript, story_beats: EmotionalArc) -> EmotionalArc:
        """Map emotional journey through the video"""
        # Already created in _identify_story_beats
        return story_beats
    
    async def _generate_cinematic_direction(
        self,
        script: VideoScript,
        story_beats: EmotionalArc,
        emotional_arc: EmotionalArc
    ) -> List[DirectedScene]:
        """Generate cinematic direction using LLM"""
        
        directed_scenes = []
        
        for i, scene in enumerate(script.scenes):
            # Find which beat this scene belongs to
            beat = next((b for b in story_beats.beats if scene.scene_number in b.scene_numbers), None)
            beat_name = beat.beat_name if beat else "Development"
            beat_emotion = beat.emotional_tone if beat else "calm"
            
            # Get previous and next scenes for context
            prev_scene = script.scenes[i-1] if i > 0 else None
            next_scene = script.scenes[i+1] if i < len(script.scenes) - 1 else None
            
            # Generate direction for this scene
            direction = await self._generate_scene_direction(
                scene, beat_name, beat_emotion, prev_scene, next_scene, i == emotional_arc.peak_moment
            )
            
            directed_scenes.append(DirectedScene(
                original_scene=scene,
                direction=direction,
                story_beat=beat_name
            ))
        
        return directed_scenes
    
    async def _generate_scene_direction(
        self,
        scene: Scene,
        beat_name: str,
        beat_emotion: str,
        prev_scene: Optional[Scene],
        next_scene: Optional[Scene],
        is_peak: bool
    ) -> CinematicDirection:
        """Generate cinematic direction for a single scene using LLM"""
        
        # Create prompt for LLM
        prompt = self._create_director_prompt(scene, beat_name, beat_emotion, prev_scene, next_scene, is_peak)
        
        try:
            # Call Gemini
            response = self.client.models.generate_content(
                model=settings.llm_model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.7,
                    response_mime_type="application/json"
                )
            )
            
            # Parse response
            direction_data = json.loads(response.text)
            
            # Create CinematicDirection object
            direction = CinematicDirection(
                shot_type=ShotType(direction_data.get("shot_type", "medium")),
                camera_movement=CameraMovement(direction_data.get("camera_movement", "static")),
                camera_angle=CameraAngle(direction_data.get("camera_angle", "eye_level")),
                lighting_mood=LightingMood(direction_data.get("lighting_mood", "soft")),
                composition=CompositionRule(direction_data.get("composition", "rule_of_thirds")),
                emotional_purpose=direction_data.get("emotional_purpose", "Engage viewer"),
                narrative_function=direction_data.get("narrative_function", "Advance story"),
                connection_from_previous=direction_data.get("connection_from_previous"),
                connection_to_next=direction_data.get("connection_to_next"),
                enhanced_image_prompt=direction_data.get("enhanced_image_prompt", scene.image_create_prompt),
                enhanced_video_prompt=direction_data.get("enhanced_video_prompt", scene.video_prompt),
                director_notes=direction_data.get("director_notes", "Standard direction")
            )
            
            return direction
            
        except Exception as e:
            logger.warning("LLM direction generation failed, using fallback", error=str(e))
            return self._create_fallback_scene_direction(scene, beat_emotion)
    
    def _create_director_prompt(
        self,
        scene: Scene,
        beat_name: str,
        beat_emotion: str,
        prev_scene: Optional[Scene],
        next_scene: Optional[Scene],
        is_peak: bool
    ) -> str:
        """Create prompt for LLM to generate cinematic direction"""
        
        prompt = f"""You are a master film director creating a shot list for a YouTube Short video.

**Scene Information:**
- Scene Number: {scene.scene_number}
- Scene Type: {scene.scene_type.value}
- Story Beat: {beat_name}
- Emotional Tone: {beat_emotion}
- Is Peak Moment: {is_peak}
- Dialogue: "{scene.dialogue}"
- Current Image Prompt: "{scene.image_create_prompt}"

**Context:**
- Previous Scene: {prev_scene.dialogue[:50] if prev_scene else "None (first scene)"}...
- Next Scene: {next_scene.dialogue[:50] if next_scene else "None (last scene)"}...

**Your Task:**
Create detailed cinematic direction for this scene that:
1. Serves the narrative beat ({beat_name})
2. Evokes the emotional tone ({beat_emotion})
3. Connects visually to previous and next scenes
4. Uses professional cinematography techniques

**Available Options:**
- Shot Types: extreme_wide, wide, medium, medium_close_up, close_up, extreme_close_up
- Camera Movements: static, slow_push_in, fast_push_in, pull_back, pan_left, pan_right, tilt_up, tilt_down, dolly_zoom, crane_up, handheld
- Camera Angles: eye_level, low, high, dutch, overhead
- Lighting Moods: bright, dramatic, soft, harsh, golden_hour, silhouette, chiaroscuro
- Composition Rules: rule_of_thirds, centered, symmetry, leading_lines, frame_within_frame, negative_space, diagonal

**Output JSON Format:**
{{
    "shot_type": "medium_close_up",
    "camera_movement": "slow_push_in",
    "camera_angle": "slightly_low",
    "lighting_mood": "dramatic",
    "composition": "rule_of_thirds",
    "emotional_purpose": "Build tension and intrigue",
    "narrative_function": "Hook viewer with mystery",
    "connection_from_previous": "Continues momentum from wide shot",
    "connection_to_next": "Sets up reveal by building tension",
    "enhanced_image_prompt": "Medium close-up of character, positioned on left third, dramatic side lighting creating shadows, mysterious expression, slightly low angle suggesting hidden knowledge. Photorealistic, professional photography, 8k uhd.",
    "enhanced_video_prompt": "Start: Character's face in shadow, mysterious expression. Action: Slow push-in over 5 seconds, light gradually reveals face. Emotion: Building intrigue and tension. Purpose: Hook viewer with mystery, set up for revelation in next scene. Camera: Smooth dolly push-in, slight upward drift. End: Tight on eyes, ready for cut to wide reveal.",
    "director_notes": "This shot hooks the viewer with mystery. The low angle and dramatic lighting suggest hidden knowledge. The slow push-in builds tension, ending tight on the eyes to create anticipation for the next scene's reveal."
}}

Think like Spielberg, Nolan, or Fincher. Every choice should have PURPOSE and MEANING.
"""
        
        return prompt
    
    def _create_fallback_scene_direction(self, scene: Scene, emotion: str) -> CinematicDirection:
        """Create basic direction when LLM fails"""
        
        # Use emotion-to-visual mapping
        visual_guide = EMOTION_TO_VISUAL.get(emotion, EMOTION_TO_VISUAL["calm"])
        
        return CinematicDirection(
            shot_type=visual_guide["shot_type"],
            camera_movement=visual_guide["camera_movement"],
            camera_angle=visual_guide["camera_angle"],
            lighting=visual_guide["lighting"],
            composition=visual_guide["composition"],
            emotional_purpose=f"Evoke {emotion}",
            narrative_function="Advance story",
            enhanced_image_prompt=scene.image_create_prompt,
            enhanced_video_prompt=scene.video_prompt,
            director_notes=f"Fallback direction for {emotion} emotion"
        )
    
    def _ensure_visual_continuity(self, directed_scenes: List[DirectedScene]) -> List[DirectedScene]:
        """Ensure visual continuity between scenes"""
        
        for i in range(len(directed_scenes)):
            current = directed_scenes[i]
            
            # Add connection notes if missing
            if i > 0 and not current.direction.connection_from_previous:
                prev = directed_scenes[i-1]
                current.direction.connection_from_previous = (
                    f"Follows {prev.direction.shot_type.value} shot with {prev.direction.camera_movement.value}"
                )
            
            if i < len(directed_scenes) - 1 and not current.direction.connection_to_next:
                next_scene = directed_scenes[i+1]
                current.direction.connection_to_next = (
                    f"Transitions to {next_scene.direction.shot_type.value} shot"
                )
        
        return directed_scenes
    
    def _determine_visual_theme(self, script: VideoScript) -> str:
        """Determine overall visual theme"""
        return f"Cinematic storytelling for: {script.title}"
    
    def _generate_pacing_notes(self, directed_scenes: List[DirectedScene]) -> str:
        """Generate pacing notes"""
        return f"{len(directed_scenes)} scenes with varied shot types and camera movements for dynamic pacing"
    
    def _generate_director_vision(self, script: VideoScript, emotional_arc: EmotionalArc) -> str:
        """Generate director's overall vision"""
        return f"Visual journey from {emotional_arc.overall_arc}, using cinematic language to enhance storytelling"
    
    def _create_fallback_direction(self, script: VideoScript) -> DirectedScript:
        """Create basic direction when full analysis fails"""
        logger.warning("Using fallback direction")
        
        directed_scenes = []
        for scene in script.scenes:
            direction = self._create_fallback_scene_direction(scene, "calm")
            directed_scenes.append(DirectedScene(
                original_scene=scene,
                direction=direction,
                story_beat="Standard"
            ))
        
        return DirectedScript(
            original_script=script,
            directed_scenes=directed_scenes,
            visual_theme="Standard visual approach",
            emotional_arc="Standard emotional progression",
            pacing_notes="Standard pacing",
            director_vision="Standard cinematic approach"
        )
