"""
Video generation constants and configuration values.

This module centralizes all magic numbers and configuration values used in
video generation and assembly, making them easy to tune and maintain.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class TextOverlayConfig:
    """Configuration for text overlays on video clips."""

    # Font size as ratio of video height
    TITLE_FONT_SIZE_RATIO: float = 0.03  # 3% of height
    SUBTITLE_FONT_SIZE_RATIO: float = 0.025  # 2.5% of height

    # Text positioning and sizing constraints
    MAX_WIDTH_RATIO: float = 0.80  # 80% of width (10% padding each side)
    SUBTITLE_WIDTH_RATIO: float = 0.65  # 65% for subtitles (more conservative)
    MAX_HEIGHT_RATIO: float = 0.25  # 25% of height for title
    SUBTITLE_HEIGHT_RATIO: float = 0.20  # 20% of height for subtitles

    # Font sizing constraints
    MIN_FONT_SIZE_RATIO: float = 0.4  # 40% of start size as minimum
    MIN_LEGIBLE_SIZE: int = 20  # Absolute minimum font size in pixels

    # Line spacing
    LINE_HEIGHT_MULTIPLIER: float = 1.3  # 130% of font height
    SUBTITLE_LINE_HEIGHT: float = 1.2  # 120% for subtitles

    # Positioning from edges
    TITLE_TOP_MARGIN_RATIO: float = 0.10  # 10% from top
    SUBTITLE_BOTTOM_MARGIN_RATIO: float = 0.15  # 15% from bottom

    # Title card duration
    TITLE_CARD_DURATION: float = 3.0  # seconds


@dataclass(frozen=True)
class VideoEffectConfig:
    """Configuration for video effects and transformations."""

    # Ken Burns effect zoom factors
    KEN_BURNS_ZOOM_SMALL: float = 0.1  # 10% zoom
    KEN_BURNS_ZOOM_MEDIUM: float = 0.15  # 15% zoom
    KEN_BURNS_ZOOM_LARGE: float = 0.2  # 20% zoom

    # Pan speed (pixels per second equivalent)
    PAN_SPEED: float = 100.0

    # Transition effects
    FADE_DURATION: float = 0.5  # seconds
    CROSSFADE_DURATION: float = 0.3  # seconds

    # Scene duration defaults
    DEFAULT_SCENE_DURATION: float = 8.0  # seconds
    MIN_SCENE_DURATION: float = 2.0  # seconds
    MAX_SCENE_DURATION: float = 15.0  # seconds


# Global instances for easy access
TEXT_OVERLAY = TextOverlayConfig()
VIDEO_EFFECTS = VideoEffectConfig()
