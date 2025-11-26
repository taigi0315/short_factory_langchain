import logging
import uuid
from typing import Optional
from pydantic import ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableBranch
from src.agents.script_writer.prompts import (
    SCRIPT_WRITER_AGENT_TEMPLATE, 
    VIDEO_SCRIPT_PARSER,
    REAL_STORY_TEMPLATE,
    EDUCATIONAL_TEMPLATE,
    CREATIVE_TEMPLATE
)
from src.models.models import VideoScript, VoiceTone, SceneType, ImageStyle
from src.core.config import settings

logger = logging.getLogger(__name__)


from src.agents.base_agent import BaseAgent

class ScriptWriterAgent(BaseAgent):
    VOICE_TONE_FIXES = {
        "explanation": VoiceTone.SERIOUS,
        "narrative": VoiceTone.CALM,
        "climax": VoiceTone.DRAMATIC,
        "development": VoiceTone.CURIOUS,
        "rising_action": VoiceTone.EXCITED,
        "informative": VoiceTone.SERIOUS,
        "conclusion": VoiceTone.CONFIDENT,
        "hook": VoiceTone.EXCITED
    }
    
    SCENE_TYPE_FIXES = {
        "climax": SceneType.CONCLUSION,
        "rising_action": SceneType.EXPLANATION,
        "development": SceneType.EXPLANATION,
        "resolution": SceneType.CONCLUSION,
        "introduction": SceneType.HOOK,
        "narrative": SceneType.STORY_TELLING,
        "opening": SceneType.HOOK
    }
    
    IMAGE_STYLE_FIXES = {
        "comparison": ImageStyle.BEFORE_AFTER_COMPARISON,
        "split": ImageStyle.SPLIT_SCREEN,
        "character": ImageStyle.CHARACTER_WITH_BACKGROUND,
        "diagram": ImageStyle.DIAGRAM_EXPLANATION,
        "infograph": ImageStyle.INFOGRAPHIC,
        "comic": ImageStyle.COMIC_PANEL,
        "closeup": ImageStyle.CLOSE_UP_REACTION,
        "wide": ImageStyle.WIDE_ESTABLISHING_SHOT
    }
    
    def __init__(self):
        """
        Initialize ScriptWriterAgent with API validation.
        Raises ValueError if API key is missing in real mode.
        """
        super().__init__(
            agent_name="ScriptWriterAgent",
            temperature=0.7,
            max_retries=3,
            request_timeout=30.0
        )

    def _setup(self):
        """Agent-specific setup."""
        if not self.mock_mode:
            prompt_router = RunnableBranch(
                (lambda x: x.get("category") in ["Real Story", "News"], REAL_STORY_TEMPLATE),
                (lambda x: x.get("category") in ["Educational", "Explainer"], EDUCATIONAL_TEMPLATE),
                CREATIVE_TEMPLATE
            )
            
            self.chain = (
                {
                    "subject": lambda x: x["subject"],
                    "language": lambda x: x["language"],
                    "max_video_scenes": lambda x: x["max_video_scenes"],
                    "min_scenes": lambda x: x["min_scenes"],
                    "category": lambda x: x.get("category", "Creative"),
                    "format_instructions": lambda x: VIDEO_SCRIPT_PARSER.get_format_instructions()
                }
                | prompt_router
                | self.llm
                | VIDEO_SCRIPT_PARSER
            )
            logger.info(f"ScriptWriterAgent initialized successfully with Router. Model: {settings.llm_model_name}")
        else:
            self.chain = None
    
    def _validate_and_fix_script(self, script: VideoScript) -> VideoScript:
        """
        Validate script and attempt to fix common LLM errors.
        
        Fixes:
        - Invalid voice_tone values → map to closest valid tone
        - Invalid scene_type values → map to closest valid type
        - Too few scenes → raise error
        
        Args:
            script: VideoScript to validate and fix
            
        Returns:
            VideoScript: Fixed script
            
        Raises:
            ValueError: If script has too few scenes
        """
        if len(script.scenes) < settings.MIN_SCENES:
            raise ValueError(
                f"Script has {len(script.scenes)} scenes, "
                f"minimum is {settings.MIN_SCENES}"
            )
        
        if len(script.scenes) > settings.MAX_SCENES:
            logger.warning(
                f"Script has {len(script.scenes)} scenes, "
                f"maximum is {settings.MAX_SCENES}. Truncating."
            )
            script.scenes = script.scenes[:settings.MAX_SCENES]
        
        fixes_applied = []
        
        for i, scene in enumerate(script.scenes):
            if isinstance(scene.voice_tone, str):
                original_value = scene.voice_tone
                if original_value in self.VOICE_TONE_FIXES:
                    scene.voice_tone = self.VOICE_TONE_FIXES[original_value]
                    fixes_applied.append(
                        f"Scene {i+1}: voice_tone '{original_value}' → '{scene.voice_tone.value}'"
                    )
                    logger.warning(
                        f"Fixed invalid voice_tone in scene {i+1}: "
                        f"'{original_value}' → '{scene.voice_tone.value}'"
                    )
            
            if isinstance(scene.scene_type, str):
                original_value = scene.scene_type
                if original_value in self.SCENE_TYPE_FIXES:
                    scene.scene_type = self.SCENE_TYPE_FIXES[original_value]
                    fixes_applied.append(
                        f"Scene {i+1}: scene_type '{original_value}' → '{scene.scene_type.value}'"
                    )
                    logger.warning(
                        f"Fixed invalid scene_type in scene {i+1}: "
                        f"'{original_value}' → '{scene.scene_type.value}'"
                    )
            
            if isinstance(scene.image_style, str):
                original_value = scene.image_style
                if original_value in self.IMAGE_STYLE_FIXES:
                    scene.image_style = self.IMAGE_STYLE_FIXES[original_value]
                    fixes_applied.append(
                        f"Scene {i+1}: image_style '{original_value}' → '{scene.image_style.value}'"
                    )
                    logger.warning(
                        f"Fixed invalid image_style in scene {i+1}: "
                        f"'{original_value}' → '{scene.image_style.value}'"
                    )
        
        if fixes_applied:
            logger.info(f"Applied {len(fixes_applied)} automatic fixes to script")
            for fix in fixes_applied:
                logger.info(f"  - {fix}")
        
        return script
    
    def generate_script(
        self,
        subject: str,
        language: str = "English",
        category: str = "Creative",
        max_scenes: Optional[int] = None,
        max_retries: int = 3
    ) -> VideoScript:
        """
        Generate video script for a given subject with automatic retry on validation errors.
        
        Args:
            subject: Topic/story description to generate script for
            language: Language for the script (default: English)
            category: Story category (News, Educational, Creative) for style routing
            max_scenes: Maximum number of scenes (default: settings.MAX_SCENES)
            max_retries: Maximum number of retry attempts (default: 3)
            
        Returns:
            VideoScript: Generated script with scenes
            
        Raises:
            Exception: If LLM generation fails after all retries
        """
        # Mock mode - return early
        if not settings.USE_REAL_LLM:
            logger.info("Returning mock script (Mock Mode)")
            from src.api.mock_data import get_mock_script
            from src.api.schemas.scripts import ScriptGenerationRequest
            
            dummy_req = ScriptGenerationRequest(
                story_title="Mock Title",
                story_premise="Mock Premise",
                story_genre="Mock Genre",
                story_audience="Mock Audience",
                duration="30s"
            )
            return get_mock_script(dummy_req).script
        
        request_id = str(uuid.uuid4())[:8]
        max_video_scenes = max_scenes if max_scenes is not None else settings.MAX_SCENES
        
        logger.info(
            f"[{request_id}] Script generation started - Subject: {subject[:50]}..., "
            f"Category: {category}, Language: {language}, "
            f"Min scenes: {settings.MIN_SCENES}, Max scenes: {max_video_scenes}"
        )
        
        last_error = None
        
        for attempt in range(max_retries):
            try:
                result = self.chain.invoke({
                    "subject": subject,
                    "language": language,
                    "category": category,
                    "max_video_scenes": max_video_scenes,
                    "min_scenes": settings.MIN_SCENES
                })
                
                result = self._validate_and_fix_script(result)
                
                logger.info(
                    f"[{request_id}] Script generation completed successfully "
                    f"(attempt {attempt + 1}/{max_retries}). "
                    f"Generated script with {len(result.scenes)} scenes."
                )
                
                return result
                
            except ValidationError as e:
                last_error = e
                logger.warning(
                    f"[{request_id}] Validation error on attempt {attempt + 1}/{max_retries}: {str(e)}"
                )
                
                if attempt < max_retries - 1:
                    logger.info(f"[{request_id}] Retrying script generation...")
                else:
                    logger.error(
                        f"[{request_id}] All retry attempts exhausted. "
                        f"Script generation failed with validation errors."
                    )
                    
            except ValueError as e:
                # Scene count errors
                last_error = e
                logger.error(
                    f"[{request_id}] Scene count validation failed on attempt {attempt + 1}/{max_retries}: {str(e)}"
                )
                
                if attempt < max_retries - 1:
                    logger.info(f"[{request_id}] Retrying with adjusted parameters...")
                else:
                    logger.error(f"[{request_id}] Failed to generate script with required scene count")
                    
            except Exception as e:
                last_error = e
                logger.error(
                    f"[{request_id}] Script generation failed on attempt {attempt + 1}/{max_retries} "
                    f"({type(e).__name__}): {str(e)}",
                    exc_info=True
                )
                
                if attempt < max_retries - 1:
                    logger.info(f"[{request_id}] Retrying...")
                else:
                    logger.error(f"[{request_id}] All retry attempts exhausted")
        
        # If we get here, all retries failed
        logger.error(f"[{request_id}] Script generation failed after {max_retries} attempts")
        raise last_error if last_error else Exception("Script generation failed")
