from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional, List


class Settings(BaseSettings):
    """
    Centralized application configuration.
    All environment variables should be defined here.
    """
    
    # ========================================
    # LLM Configuration
    # ========================================
    llm_model_name: str = Field(
        default="gemini-2.5-flash",
        description="LLM model to use for text generation"
    )
    
    # ========================================
    # API Keys
    # ========================================
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key (used for both text and image generation)")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None, description="ElevenLabs voice synthesis API key")
    TAVILY_API_KEY: Optional[str] = Field(default=None, description="Tavily Search API key")
    
    VOICE_SETTINGS_OVERRIDE: str = Field(
        default="{}",
        description="JSON string to override voice settings per tone (e.g. {'excited': {'stability': 0.1}})"
    )
    
    # ========================================
    # Feature Flags (Mock vs Real mode)
    # ========================================
    USE_REAL_LLM: bool = Field(
        default=False,
        description="Use real Gemini LLM (true) or mock data (false)"
    )
    USE_REAL_IMAGE: bool = Field(
        default=False,
        description="Use real image generation (true) or placeholders (false)"
    )
    USE_REAL_VOICE: bool = Field(
        default=False,
        description="Use real ElevenLabs (true) or gTTS mock (false)"
    )
    
    # ========================================
    # Error Handling & Development Mode
    # ========================================
    DEV_MODE: bool = Field(
        default=True,
        description="Development mode: show all errors, no silent fallbacks. Set to false for production."
    )
    FAIL_FAST: bool = Field(
        default=True,
        description="Stop on first error instead of continuing with partial results"
    )
    
    # ========================================
    # Application Settings
    # ========================================
    MIN_SCENES: int = Field(
        default=4,
        ge=2,
        le=20,
        description="Minimum number of scenes in generated scripts"
    )
    MAX_SCENES: int = Field(
        default=15,
        ge=2,
        le=40,
        description="Maximum number of scenes in generated scripts"
    )
    DEFAULT_SCENE_DURATION: float = Field(
        default=3.0,
        ge=1.0,
        le=10.0,
        description="Default duration for scenes without audio (seconds)"
    )
    GENERATED_ASSETS_DIR: str = Field(
        default="generated_assets",
        description="Root directory for generated images/audio/videos"
    )
    IMAGE_ASPECT_RATIO: str = Field(
        default="9:16",
        description="Target aspect ratio for generated images (e.g., '9:16', '16:9', '1:1')"
    )

    # ========================================
    # Standardized Retry Settings
    # ========================================
    DEFAULT_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Default maximum number of retries for operations"
    )
    DEFAULT_RETRY_INITIAL_DELAY: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Default initial retry delay in seconds"
    )
    DEFAULT_RETRY_MAX_DELAY: float = Field(
        default=60.0,
        ge=1.0,
        le=300.0,
        description="Default maximum retry delay in seconds"
    )
    DEFAULT_RETRY_EXPONENTIAL_BASE: float = Field(
        default=2.0,
        ge=1.1,
        le=10.0,
        description="Default exponential backoff base"
    )

    # ========================================
    # Video Generation Settings
    # ========================================
    VIDEO_RESOLUTION: str = Field(default="1080p", description="Video resolution (1080p or 720p)")
    VIDEO_FPS: int = Field(default=30, description="Video frames per second")
    
    # AI Video Generation
    VIDEO_GENERATION_PROVIDER: str = Field(default="mock", description="Provider for AI video generation: 'mock', 'luma', 'runway'")
    LUMA_API_KEY: Optional[str] = Field(default=None, description="Luma Dream Machine API key")
    VIDEO_QUALITY: str = Field(default="medium", description="FFmpeg preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)")
    MAX_AI_VIDEOS_PER_SCRIPT: int = Field(default=2, ge=0, le=10, description="Maximum number of AI videos to generate per script")
    
    # ========================================
    # Image Generation Retry Settings
    # ========================================
    IMAGE_GENERATION_MAX_RETRIES: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum number of retry attempts for image generation per scene"
    )
    IMAGE_GENERATION_RETRY_DELAYS: List[int] = Field(
        default=[5, 15, 30, 60],
        description="Retry delay sequence in seconds (e.g., [5, 15, 30, 60] means: 1st retry after 5s, 2nd after 15s, etc.)"
    )
    IMAGE_GENERATION_SCENE_DELAY: int = Field(
        default=5,
        ge=1,
        le=60,
        description="Delay in seconds between successful scene image generations to prevent rate limiting"
    )
    
    # Video Upload Settings
    MAX_VIDEO_UPLOAD_SIZE_MB: int = Field(default=100, description="Maximum video upload size in MB")
    ALLOWED_VIDEO_FORMATS: List[str] = Field(default=[".mp4", ".mov", ".webm"], description="Allowed video formats")
    
    # ========================================
    # Audio Generation Settings
    # ========================================
    DEFAULT_VOICE_ID: str = Field(
        default="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        description="Default ElevenLabs voice ID"
    )
    VOICE_STABILITY: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Voice stability (0.0-1.0, higher = more consistent)"
    )
    VOICE_SIMILARITY: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Voice similarity boost (0.0-1.0, higher = closer to original)"
    )
    
    # ========================================
    # Validators
    # ========================================
    @field_validator('MAX_SCENES')
    @classmethod
    def validate_scene_range(cls, v, info):
        """Ensure MAX_SCENES >= MIN_SCENES."""
        min_scenes = info.data.get('MIN_SCENES', 4)
        if v < min_scenes:
            raise ValueError(f'MAX_SCENES ({v}) must be >= MIN_SCENES ({min_scenes})')
        return v
    
    @field_validator('USE_REAL_LLM', 'USE_REAL_IMAGE', 'USE_REAL_VOICE', 'DEV_MODE', 'FAIL_FAST', mode='before')
    @classmethod
    def parse_bool(cls, v):
        """Parse boolean from string env vars."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in ('true', '1', 'yes', 'on')
        return False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
