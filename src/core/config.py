from pydantic_settings import BaseSettings
from pydantic import Field, field_validator
from typing import Optional


class Settings(BaseSettings):
    """
    Centralized application configuration.
    All environment variables should be defined here.
    """
    
    # ========================================
    # LLM Configuration
    # ========================================
    llm_model_name: str = Field(
        default="gemini-2.0-flash",
        description="LLM model to use for text generation"
    )
    
    # ========================================
    # API Keys
    # ========================================
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key (used for both text and image generation)")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None, description="ElevenLabs voice synthesis API key")
    
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
        default=8,
        ge=2,
        le=20,
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

    # ========================================
    # Video Generation Settings
    # ========================================
    VIDEO_RESOLUTION: str = Field(default="1080p", description="Video resolution (1080p or 720p)")
    VIDEO_FPS: int = Field(default=30, description="Video frames per second")
    VIDEO_QUALITY: str = Field(default="medium", description="FFmpeg preset (ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow)")
    
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
        case_sensitive = False  # Allow USE_REAL_LLM or use_real_llm
        extra = "ignore"  # Ignore deprecated env vars like NANO_BANANA_API_KEY


settings = Settings()
