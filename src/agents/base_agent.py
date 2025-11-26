from abc import ABC, abstractmethod
from typing import Optional
import structlog
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings

logger = structlog.get_logger()

class BaseAgent(ABC):
    """
    Base class for all AI agents in the ShortFactory pipeline.
    
    Provides common initialization logic including:
    - API key validation
    - LLM initialization
    - Mock mode handling
    - Logging setup
    """
    
    def __init__(
        self,
        agent_name: str,
        temperature: float = 0.7,
        max_retries: int = 3,
        request_timeout: float = 30.0,
        require_llm: bool = True
    ):
        """
        Initialize base agent with common setup.
        
        Args:
            agent_name: Name of the agent (for logging)
            temperature: LLM temperature setting
            max_retries: Number of retry attempts for LLM calls
            request_timeout: Timeout for LLM requests in seconds
            require_llm: Whether this agent requires LLM (False for image/video agents)
        """
        self.agent_name = agent_name
        self.mock_mode = not settings.USE_REAL_LLM
        self.llm: Optional[ChatGoogleGenerativeAI] = None
        
        if require_llm:
            self._initialize_llm(temperature, max_retries, request_timeout)
        
        # Call agent-specific setup
        self._setup()
        
        logger.info(
            f"{agent_name} initialized",
            mode="REAL" if not self.mock_mode else "MOCK"
        )
    
    def _initialize_llm(
        self,
        temperature: float,
        max_retries: int,
        request_timeout: float
    ):
        """Initialize LLM with validation and error handling."""
        if not self.mock_mode:
            if not settings.GEMINI_API_KEY:
                raise ValueError(
                    f"GEMINI_API_KEY is required for {self.agent_name} when USE_REAL_LLM=true. "
                    "Please set it in your .env file or environment variables."
                )
            
            self.llm = ChatGoogleGenerativeAI(
                model=settings.llm_model_name,
                google_api_key=settings.GEMINI_API_KEY,
                temperature=temperature,
                max_retries=max_retries,
                request_timeout=request_timeout,
                # Add explicit error handling/retry config if supported by library
            )
            
            logger.info(
                f"✅ {self.agent_name} initializing with REAL Gemini LLM",
                model=settings.llm_model_name
            )
        else:
            logger.info(f"⚠️ {self.agent_name} in MOCK mode (USE_REAL_LLM=false)")
    
    @abstractmethod
    def _setup(self):
        """
        Agent-specific setup logic.
        Override this method to add custom initialization.
        """
        pass
