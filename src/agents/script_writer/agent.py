import logging
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.script_writer.prompts import SCRIPT_WRITER_AGENT_TEMPLATE, VIDEO_SCRIPT_PARSER
from src.models.models import VideoScript
from src.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)


class ScriptWriterAgent:
    def __init__(self):
        """
        Initialize ScriptWriterAgent with API validation.
        Raises ValueError if API key is missing in real mode.
        """
        # Validate API key if using real LLM
        if settings.USE_REAL_LLM:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is required when USE_REAL_LLM=true. "
                    "Please set it in your .env file or environment variables."
                )
            logger.info("✅ ScriptWriterAgent initializing with REAL Gemini LLM")
        else:
            logger.info("⚠️ ScriptWriterAgent in MOCK mode (USE_REAL_LLM=false)")
        
        # Initialize LLM with error handling
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model_name,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.7,
            max_retries=3,
            request_timeout=45.0,  # Longer timeout for script generation
        )
        
        logger.info(f"ScriptWriterAgent initialized successfully. Model: {settings.llm_model_name}")

    def generate_script(self, subject: str) -> VideoScript:
        """
        Generate video script for a given subject.
        
        Args:
            subject: Topic/story description to generate script for
            
        Returns:
            VideoScript: Generated script with scenes
            
        Raises:
            Exception: If LLM generation fails after retries
        """
        request_id = str(uuid.uuid4())[:8]
        
        logger.info(
            f"[{request_id}] Script generation started",
            extra={
                "request_id": request_id,
                "subject_preview": subject[:100],
                "use_real_llm": settings.USE_REAL_LLM,
            }
        )
        
        try:
            # Build and invoke the chain with the template
            chain = SCRIPT_WRITER_AGENT_TEMPLATE | self.llm | VIDEO_SCRIPT_PARSER
            result = chain.invoke({
                "subject": subject,
                "language": "English",
                "max_video_scenes": settings.MAX_VIDEO_SCENES
            })
            
            logger.info(
                f"[{request_id}] Script generation completed successfully. "
                f"Generated script with {len(result.scenes)} scenes."
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"[{request_id}] Script generation failed: {str(e)}",
                exc_info=True,
                extra={
                    "request_id": request_id,
                    "error_type": type(e).__name__,
                }
            )
            # Re-raise to allow fallback decorator to handle
            raise
