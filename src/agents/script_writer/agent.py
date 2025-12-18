import structlog
import uuid
from typing import Optional
from pydantic import ValidationError

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
from src.core.retry import retry_with_backoff

logger = structlog.get_logger()


from src.agents.base_agent import BaseAgent

class ScriptWriterAgent(BaseAgent):
    """
    Agent responsible for generating video scripts.

    Note: Enum validation is handled automatically by Pydantic validators
    in the Scene model, so no manual fixing is needed here.
    """

    def __init__(self) -> None:
        """
        Initialize ScriptWriterAgent with API validation.
        Raises ValueError if API key is missing in real mode.
        """
        super().__init__(
            agent_name="ScriptWriterAgent",
            temperature=settings.DEFAULT_LLM_TEMPERATURE,
            max_retries=settings.DEFAULT_MAX_RETRIES,
            request_timeout=settings.DEFAULT_REQUEST_TIMEOUT
        )

    def _setup(self) -> None:
        """Agent-specific setup."""
        if not self.mock_mode:
            if not self.llm:
                raise RuntimeError("LLM not initialized")

            prompt_router: RunnableBranch = RunnableBranch(
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

        # Note: Enum validation is now handled by Pydantic validators
        # in the Scene model, so no manual fixing needed here
        return script
    
    async def generate_script(
        self,
        subject: str,
        language: str = "English",
        category: str = "Creative",
        max_scenes: Optional[int] = None,
        max_retries: int = settings.DEFAULT_MAX_RETRIES
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
        
        try:
            # Call the decorated internal method
            result = await self._generate_script_internal(
                subject=subject,
                language=language,
                category=category,
                max_video_scenes=max_video_scenes,
                request_id=request_id
            )
            
            from typing import cast
            return cast(VideoScript, result)
            
        except Exception as e:
            logger.error(f"[{request_id}] Script generation failed after retries: {e}")
            raise

    @retry_with_backoff(operation_name="script generation")
    async def _generate_script_internal(
        self,
        subject: str,
        language: str,
        category: str,
        max_video_scenes: int,
        request_id: str
    ) -> VideoScript:
        """Internal method to generate script with retries."""
        
        try:
            # Use ainvoke for async execution
            result = await self.chain.ainvoke({
                "subject": subject,
                "language": language,
                "category": category,
                "max_video_scenes": max_video_scenes,
                "min_scenes": settings.MIN_SCENES
            })
            
            result = self._validate_and_fix_script(result)
            
            logger.info(
                f"[{request_id}] Script generation completed successfully. "
                f"Generated script with {len(result.scenes)} scenes."
            )
            
            from typing import cast
            return cast(VideoScript, result)
            
        except ValidationError as e:
            logger.warning(f"[{request_id}] Validation error: {str(e)}")
            raise # Retry decorator will catch this
            
        except ValueError as e:
            logger.error(f"[{request_id}] Scene count validation failed: {str(e)}")
            raise # Retry decorator will catch this
            
        except Exception as e:
            logger.error(
                f"[{request_id}] Script generation failed ({type(e).__name__}): {str(e)}",
                exc_info=True
            )
            raise # Retry decorator will catch this
