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
        default="gemini-1.5-flash",
        description="LLM model to use for text generation"
    )
    
    # ========================================
    # API Keys
    # ========================================
    GEMINI_API_KEY: Optional[str] = Field(default=None, description="Google Gemini API key")
    OPENAI_API_KEY: Optional[str] = Field(default=None, description="OpenAI API key")
    ELEVENLABS_API_KEY: Optional[str] = Field(default=None, description="ElevenLabs voice synthesis API key")
    NANO_BANANA_API_KEY: Optional[str] = Field(default=None, description="NanoBanana image generation API key")
    
    # ========================================
    # External Service URLs
    # ========================================
    NANO_BANANA_API_URL: str = Field(
        default="https://api.nanobanana.com/v1/generate",
        description="NanoBanana API endpoint"
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
    # Application Settings
    # ========================================
    MAX_VIDEO_SCENES: int = Field(default=8, description="Maximum number of scenes per video")
    GENERATED_ASSETS_DIR: str = Field(
        default="generated_assets",
        description="Root directory for generated images/audio/videos"
    )
    
    # ========================================
    # Validators
    # ========================================
    @field_validator('USE_REAL_LLM', 'USE_REAL_IMAGE', 'USE_REAL_VOICE', mode='before')
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


settings = Settings()
