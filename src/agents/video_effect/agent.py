"""
Video Effect Agent

Intelligent agent for selecting video effects, transitions, and generating
video prompts based on story flow and scene context.
"""
import logging
from typing import Optional, List, Dict
from dataclasses import dataclass

from src.models.models import VideoScript, Scene, SceneType, TransitionType

logger = logging.getLogger(__name__)


@dataclass
class EffectRecommendation:
    """Recommendation for a scene's visual treatment"""
    scene_number: int
    effect: str
    video_prompt: Optional[str]
    transition_to_next: TransitionType
    recommend_ai_video: bool
    reasoning: str


class VideoEffectAgent:
    """
    Intelligent agent for video effects, transitions, and motion planning.
    
    Analyzes the entire script to make cohesive decisions about:
    - Visual effects for each scene
    - Transitions between scenes
    - Video generation prompts
    - AI video vs. image+effect recommendations
    """
    
    # Available effects with their characteristics
    EFFECTS = {
        'ken_burns_zoom_in': {
            'description': 'Slow zoom into image',
            'use_cases': ['building tension', 'focus', 'hook scenes', 'revelation'],
            'energy': 'medium'
        },
        'ken_burns_zoom_out': {
            'description': 'Slow zoom out from image',
            'use_cases': ['conclusion', 'revealing context', 'perspective shift'],
            'energy': 'medium'
        },
        'pan_left': {
            'description': 'Horizontal pan left',
            'use_cases': ['progression', 'time passage', 'exploration'],
            'energy': 'low'
        },
        'pan_right': {
            'description': 'Horizontal pan right',
            'use_cases': ['discovery', 'exploration', 'continuation'],
            'energy': 'low'
        },
        'static': {
            'description': 'No movement',
            'use_cases': ['clarity', 'explanation', 'stability', 'text-heavy'],
            'energy': 'none'
        },
        'shake': {
            'description': 'Rapid shake effect',
            'use_cases': ['action', 'impact', 'thunder', 'earthquake', 'shock'],
            'energy': 'high'
        },
        'tilt_up': {
            'description': 'Vertical tilt upward',
            'use_cases': ['revelation', 'awe', 'looking up', 'grandeur'],
            'energy': 'low'
        },
        'tilt_down': {
            'description': 'Vertical tilt downward',
            'use_cases': ['grounding', 'detail', 'looking down', 'focus'],
            'energy': 'low'
        }
    }
    
    def __init__(self):
        """Initialize the Video Effect Agent"""
        logger.info("VideoEffectAgent initialized")
    
    def analyze_script(
        self, 
        script: VideoScript,
        max_ai_videos: int = 2
    ) -> List[EffectRecommendation]:
        """
        Analyze entire script and make decisions about effects, transitions, and video generation.
        
        Args:
            script: The video script to analyze
            max_ai_videos: Maximum number of scenes to recommend for AI video generation
            
        Returns:
            List of EffectRecommendation for each scene
        """
        logger.info(f"Analyzing script: {script.title} ({len(script.scenes)} scenes)")
        
        recommendations = []
        
        for i, scene in enumerate(script.scenes):
            prev_scene = script.scenes[i - 1] if i > 0 else None
            next_scene = script.scenes[i + 1] if i < len(script.scenes) - 1 else None
            
            # Select effect
            effect = self.select_effect_for_scene(scene, prev_scene, next_scene, script)
            
            # Generate video prompt if needed
            video_prompt = None
            if scene.needs_animation and scene.video_prompt:
                video_prompt = self.enhance_video_prompt(scene, effect, script)
            
            # Select transition
            transition = self.select_transition(scene, next_scene) if next_scene else TransitionType.FADE
            
            # Recommend AI video
            recommend_ai = self.recommend_ai_video(scene, effect)
            
            # Generate reasoning
            reasoning = self._generate_reasoning(scene, effect, recommend_ai)
            
            recommendations.append(EffectRecommendation(
                scene_number=scene.scene_number,
                effect=effect,
                video_prompt=video_prompt,
                transition_to_next=transition,
                recommend_ai_video=recommend_ai,
                reasoning=reasoning
            ))
        
        # Apply budget constraint for AI videos
        recommendations = self._apply_ai_video_budget(recommendations, max_ai_videos)
        
        logger.info(f"Analysis complete. {sum(1 for r in recommendations if r.recommend_ai_video)} scenes recommended for AI video")
        
        return recommendations
    
    def select_effect_for_scene(
        self,
        scene: Scene,
        prev_scene: Optional[Scene],
        next_scene: Optional[Scene],
        script: VideoScript
    ) -> str:
        """
        Select optimal effect based on scene context using rule-based logic.
        
        Args:
            scene: Current scene
            prev_scene: Previous scene (if any)
            next_scene: Next scene (if any)
            script: Full script for context
            
        Returns:
            Effect name (e.g., 'ken_burns_zoom_in')
        """
        # Check for specific keywords in dialogue/prompts that suggest effects
        dialogue_lower = (scene.dialogue or "").lower()
        prompt_lower = (scene.image_create_prompt or "").lower()
        video_prompt_lower = (scene.video_prompt or "").lower()
        
        combined_text = f"{dialogue_lower} {prompt_lower} {video_prompt_lower}"
        
        # Scene type based selection (primary logic)
        if scene.scene_type == SceneType.HOOK:
            # Hook scenes need attention-grabbing effects
            # Check for vertical movement keywords first
            if any(word in combined_text for word in ['look up', 'rise', 'ascend', 'sky', 'tall', 'tower', 'tilt up']):
                return 'tilt_up'
            if any(word in combined_text for word in ['look down', 'descend', 'ground', 'below', 'tilt down']):
                return 'tilt_down'
            # Check for action keywords
            if any(word in combined_text for word in ['strike', 'hit', 'crash', 'shake', 'earthquake', 'impact', 'explode']):
                return 'shake'
            if scene.video_importance >= 8:
                return 'ken_burns_zoom_in'  # Build tension
            return 'ken_burns_zoom_in'
        
        elif scene.scene_type == SceneType.CONCLUSION:
            # Conclusions often benefit from zoom out (perspective)
            return 'ken_burns_zoom_out'
        
        elif scene.scene_type == SceneType.VISUAL_DEMO:
            # Check for vertical movement keywords first
            if any(word in combined_text for word in ['look up', 'rise', 'ascend', 'sky', 'tall', 'tower', 'tilt up']):
                return 'tilt_up'
            if any(word in combined_text for word in ['look down', 'descend', 'ground', 'below', 'tilt down']):
                return 'tilt_down'
            # Check for specific action keywords
            if any(word in combined_text for word in ['strike', 'hit', 'crash', 'shake', 'impact']):
                return 'shake'
            # Visual demos benefit from panning to show details
            if 'left' in combined_text or 'before' in combined_text:
                return 'pan_left'
            elif 'right' in combined_text or 'after' in combined_text:
                return 'pan_right'
            return 'pan_right'  # Default for demos
        
        elif scene.scene_type == SceneType.EXPLANATION:
            # Explanations work best with static or subtle effects
            if scene.video_importance >= 7:
                return 'ken_burns_zoom_in'  # Add some interest
            return 'static'
        
        # Check for vertical movement keywords (secondary logic)
        if any(word in combined_text for word in ['look up', 'rise', 'ascend', 'sky', 'tall', 'tower']):
            return 'tilt_up'
        
        if any(word in combined_text for word in ['look down', 'descend', 'ground', 'below', 'detail']):
            return 'tilt_down'
        
        # Default based on importance
        if scene.video_importance >= 7:
            return 'ken_burns_zoom_in'
        
        return 'static'
    
    def enhance_video_prompt(
        self,
        scene: Scene,
        effect: str,
        script: VideoScript
    ) -> str:
        """
        Generate or enhance video prompt for AI video generation.
        
        Args:
            scene: Scene to generate prompt for
            effect: Selected effect
            script: Full script for context
            
        Returns:
            Enhanced video prompt
        """
        base_prompt = scene.video_prompt or scene.image_create_prompt
        
        # Add effect-specific instructions
        effect_instructions = {
            'shake': "Add rapid shaking motion to simulate impact or震動",
            'ken_burns_zoom_in': "Slowly zoom into the focal point",
            'ken_burns_zoom_out': "Slowly zoom out to reveal context",
            'pan_left': "Pan camera smoothly from right to left",
            'pan_right': "Pan camera smoothly from left to right",
            'tilt_up': "Tilt camera upward gradually",
            'tilt_down': "Tilt camera downward gradually",
            'static': "Minimal movement, focus on subject"
        }
        
        effect_instruction = effect_instructions.get(effect, "")
        
        # Construct enhanced prompt
        enhanced = f"""{base_prompt}

Camera Motion: {effect_instruction}
Duration: 5-8 seconds
Aspect Ratio: 9:16 (vertical)
Style: {script.global_visual_style if hasattr(script, 'global_visual_style') else 'Cinematic'}
Mood: {scene.voice_tone.value if hasattr(scene.voice_tone, 'value') else 'neutral'}"""
        
        return enhanced.strip()
    
    def select_transition(
        self,
        current_scene: Scene,
        next_scene: Optional[Scene]
    ) -> TransitionType:
        """
        Select optimal transition between scenes.
        
        Args:
            current_scene: Current scene
            next_scene: Next scene (if any)
            
        Returns:
            TransitionType
        """
        if not next_scene:
            return TransitionType.FADE
        
        # Fast-paced content uses cuts
        if current_scene.voice_tone.value in ['excited', 'dramatic'] and \
           next_scene.voice_tone.value in ['excited', 'dramatic']:
            return TransitionType.NONE  # Direct cut
        
        # Comparison scenes use slides
        if current_scene.scene_type == SceneType.COMPARISON or \
           next_scene.scene_type == SceneType.COMPARISON:
            return TransitionType.SLIDE_LEFT
        
        # Visual demos to conclusions use dissolve
        if current_scene.scene_type == SceneType.VISUAL_DEMO and \
           next_scene.scene_type == SceneType.CONCLUSION:
            return TransitionType.DISSOLVE
        
        # Hook to explanation uses zoom
        if current_scene.scene_type == SceneType.HOOK and \
           next_scene.scene_type == SceneType.EXPLANATION:
            return TransitionType.ZOOM_IN
        
        # Default: fade (smooth and safe)
        return TransitionType.FADE
    
    def recommend_ai_video(
        self,
        scene: Scene,
        effect: str
    ) -> bool:
        """
        Decide if scene should use AI video generation vs. image+effect.
        
        Args:
            scene: Scene to evaluate
            effect: Selected effect
            
        Returns:
            True if AI video is recommended
        """
        # High importance scenes are strong candidates
        if scene.video_importance >= 9:
            return True
        
        # Complex effects benefit from AI video
        if effect in ['shake', 'tilt_up', 'tilt_down'] and scene.video_importance >= 7:
            return True
        
        # Scenes marked as needing animation with detailed prompts
        if scene.needs_animation and scene.video_prompt and len(scene.video_prompt) > 100:
            if scene.video_importance >= 7:
                return True
        
        # Simple effects work fine with image+effect
        return False
    
    def _apply_ai_video_budget(
        self,
        recommendations: List[EffectRecommendation],
        max_ai_videos: int
    ) -> List[EffectRecommendation]:
        """
        Apply budget constraint by limiting AI video recommendations.
        
        Keeps only the top N scenes by importance.
        """
        # Sort by importance (need to get from original scenes)
        # For now, just take the first max_ai_videos that are recommended
        ai_video_recs = [r for r in recommendations if r.recommend_ai_video]
        
        if len(ai_video_recs) <= max_ai_videos:
            return recommendations
        
        # Keep only top max_ai_videos
        # This is simplified - in production, sort by scene importance
        for i, rec in enumerate(recommendations):
            if rec.recommend_ai_video and i >= max_ai_videos:
                rec.recommend_ai_video = False
                rec.reasoning += " (Budget constraint: using image+effect instead)"
        
        return recommendations
    
    def _generate_reasoning(
        self,
        scene: Scene,
        effect: str,
        recommend_ai: bool
    ) -> str:
        """Generate human-readable reasoning for decisions"""
        effect_info = self.EFFECTS.get(effect, {})
        
        reasoning_parts = []
        
        # Effect reasoning
        reasoning_parts.append(f"Effect '{effect}': {effect_info.get('description', 'N/A')}")
        
        # Scene type reasoning
        reasoning_parts.append(f"Scene type: {scene.scene_type.value}")
        
        # Importance reasoning
        if scene.video_importance >= 8:
            reasoning_parts.append(f"High importance ({scene.video_importance}/10)")
        
        # AI video reasoning
        if recommend_ai:
            reasoning_parts.append("AI video recommended for quality")
        else:
            reasoning_parts.append("Image+effect sufficient")
        
        return " | ".join(reasoning_parts)
