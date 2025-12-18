"""
Custom exception hierarchy for ShortFactory.

Provides specific exception types for different failure modes,
enabling better error handling, logging, and recovery strategies.
"""


class ShortFactoryError(Exception):
    """Base exception for all ShortFactory errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class LLMError(ShortFactoryError):
    """Error during LLM API calls (Gemini, etc.)."""
    pass


class ImageGenerationError(ShortFactoryError):
    """Error during image generation."""
    pass


class VoiceGenerationError(ShortFactoryError):
    """Error during voice synthesis."""
    pass


class VideoGenerationError(ShortFactoryError):
    """Error during video generation (Luma, etc.)."""
    pass


class VideoAssemblyError(ShortFactoryError):
    """Error during video assembly (MoviePy)."""
    pass


class WorkflowError(ShortFactoryError):
    """Error in workflow state management."""
    pass


class ValidationError(ShortFactoryError):
    """Error in data validation."""
    pass


class ConfigurationError(ShortFactoryError):
    """Error in application configuration."""
    pass


class ResourceNotFoundError(ShortFactoryError):
    """Requested resource not found."""
    pass


class APIQuotaExceededError(ShortFactoryError):
    """API quota or rate limit exceeded."""
    pass


class TimeoutError(ShortFactoryError):
    """Operation timed out."""
    pass
