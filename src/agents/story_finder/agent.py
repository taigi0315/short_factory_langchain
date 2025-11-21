import os
import logging
import uuid
from langchain_google_genai import ChatGoogleGenerativeAI
from src.agents.story_finder.prompts import STORY_FINDER_TEMPLATE, story_parser
from src.agents.story_finder.models import StoryList, StoryIdea
from src.core.config import settings

# Setup logging
logger = logging.getLogger(__name__)


class StoryFinderAgent:
    def __init__(self):
        """
        Initialize StoryFinderAgent with API validation.
        Raises ValueError if API key is missing in real mode.
        """
        # Validate API key if using real LLM
        if settings.USE_REAL_LLM:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    "GEMINI_API_KEY is required when USE_REAL_LLM=true. "
                    "Please set it in your .env file or environment variables."
                )
            logger.info("✅ StoryFinderAgent initializing with REAL Gemini LLM")
            
            # Initialize LLM with error handling and retries
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=0.7,
                max_retries=3,  # Retry failed requests
                request_timeout=30.0,  # 30 second timeout
            )
            
            # Build the chain
            self.chain = STORY_FINDER_TEMPLATE | self.llm | story_parser
            logger.info(f"StoryFinderAgent initialized successfully. Model: {settings.llm_model_name}")
            
        else:
            logger.info("⚠️ StoryFinderAgent in MOCK mode (USE_REAL_LLM=false)")
            self.llm = None
            self.chain = None

    def find_stories(self, subject: str, num_stories: int = 5) -> StoryList:
        if not settings.USE_REAL_LLM:
            logger.info("Returning mock stories (Mock Mode)")
            return StoryList(stories=[
                StoryIdea(
                    title="Mock Story 1", 
                    summary="A mock summary for testing.", 
                    hook="Did you know this is a mock?", 
                    keywords=["mock", "test", "story"]
                ),
                StoryIdea(
                    title="Mock Story 2", 
                    summary="Another mock summary.", 
                    hook="Here is another mock hook.", 
                    keywords=["mock", "example"]
                ),
            ])

        """
        Generate story ideas for a given subject.
        
        Args:
            subject: Topic to generate stories about
            num_stories: Number of stories to generate (default: 5)
            
        Returns:
            StoryList: List of generated story ideas
            
        Raises:
            Exception: If LLM generation fails after retries
        """
        request_id = str(uuid.uuid4())[:8]
        
        logger.info(
            f"[{request_id}] Story generation started - Subject: {subject[:50]}..., "
            f"Num stories: {num_stories}, Real LLM: {settings.USE_REAL_LLM}"
        )
        
        try:
            # Invoke the chain
            result = self.chain.invoke({
                "subject": subject,
                "num_stories": num_stories
            })
            
            logger.info(
                f"[{request_id}] Story generation completed successfully. "
                f"Generated {len(result.stories)} stories."
            )
            
            return result
            
        except Exception as e:
            logger.error(
                f"[{request_id}] Story generation failed ({type(e).__name__}): {str(e)}",
                exc_info=True
            )
            # Re-raise  to allow fallback decorator to handle
            raise
