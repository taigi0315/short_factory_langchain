"""
Text overlay and title card creation for video generation.

Provides utilities for creating title cards and text overlays with PIL.
"""
import numpy as np
import structlog
from typing import Tuple
from PIL import Image, ImageDraw
from moviepy import ImageClip, VideoClip
from moviepy import vfx

from src.utils.text_rendering import FontLoader, wrap_text, fit_font_to_width
from src.core.video_constants import TEXT_OVERLAY

logger = structlog.get_logger()


class TextOverlay:
    """Handles text overlays and title cards for videos."""

    @staticmethod
    def create_title_card(
        title: str,
        resolution: Tuple[int, int],
        duration: float = 3.0
    ) -> VideoClip:
        """Create a title card with transparent background and colorful centered text.

        Args:
            title: Title text to display
            resolution: Video resolution (width, height)
            duration: Duration of the title card in seconds

        Returns:
            VideoClip with title card
        """
        w, h = resolution

        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Start size: configured ratio of height
        start_font_size = int(h * TEXT_OVERLAY.TITLE_FONT_SIZE_RATIO)

        # Safer margin: configured width ratio
        max_width = int(w * TEXT_OVERLAY.MAX_WIDTH_RATIO)

        # Get font that fits (configured max height ratio)
        max_height = int(h * TEXT_OVERLAY.MAX_HEIGHT_RATIO)
        font = fit_font_to_width(title, max_width, start_font_size, draw, max_height)

        lines = wrap_text(title, font, max_width, draw)

        # Calculate line height
        bbox = draw.textbbox((0, 0), "Mg", font=font)
        line_height = int((bbox[3] - bbox[1]) * 1.3)

        start_y = int(h * 0.10)  # Title starts at 10% from top

        colors = [
            (255, 100, 150, 255),  # Pink
            (255, 150, 100, 255),  # Coral
            (255, 200, 100, 255),  # Orange-yellow
        ]

        for i, line in enumerate(lines):
            line_w = draw.textlength(line, font=font)
            x = (w - line_w) // 2
            y = start_y + (i * line_height)

            color_idx = i % len(colors)
            text_color = colors[color_idx]

            shadow_color = (0, 0, 0, 255)
            shadow_offset = max(2, int(line_height * 0.05))

            # Draw shadow
            for adj in range(-shadow_offset, shadow_offset + 1):
                for adj2 in range(-shadow_offset, shadow_offset + 1):
                    if adj != 0 or adj2 != 0:
                        draw.text((x+adj, y+adj2), line, font=font, fill=shadow_color)

            # Draw text
            draw.text((x, y), line, font=font, fill=text_color)

        img_np = np.array(img)
        title_clip = ImageClip(img_np, transparent=True).with_duration(duration)

        title_clip = title_clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])

        return title_clip

    @staticmethod
    def create_text_overlay(
        text: str,
        resolution: Tuple[int, int],
        duration: float
    ) -> VideoClip:
        """Create text overlay using PIL with text wrapping and sizing.

        Args:
            text: Text to display as overlay
            resolution: Video resolution (width, height)
            duration: Duration of the overlay in seconds

        Returns:
            VideoClip with text overlay
        """
        w, h = resolution

        img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Start size: configured ratio of height
        start_font_size = int(h * TEXT_OVERLAY.SUBTITLE_FONT_SIZE_RATIO)

        # Safer margin: configured width ratio
        max_width = int(w * TEXT_OVERLAY.MAX_WIDTH_RATIO)

        # Get font that fits (configured subtitle max height)
        max_height = int(h * TEXT_OVERLAY.SUBTITLE_HEIGHT_RATIO)
        font = fit_font_to_width(text, max_width, start_font_size, draw, max_height)

        lines = wrap_text(text, font, max_width, draw)

        # Standardize line height
        bbox = draw.textbbox((0, 0), "Mg", font=font)
        line_height = int((bbox[3] - bbox[1]) * 1.2)

        total_text_height = len(lines) * line_height

        # Position at bottom 20% (more space from bottom edge)
        start_y = int(h * 0.80) - (total_text_height // 2)

        shadow_color = (0, 0, 0, 255)
        text_color = (255, 215, 0, 255)

        # Dynamic shadow offset
        shadow_offset = max(1, int(line_height * 0.04))

        for i, line in enumerate(lines):
            line_w = draw.textlength(line, font=font)
            x = (w - line_w) // 2
            y = start_y + (i * line_height)

            # Draw shadow
            for adj in range(-shadow_offset, shadow_offset + 1):
                for adj2 in range(-shadow_offset, shadow_offset + 1):
                    if adj != 0 or adj2 != 0:
                        draw.text((x+adj, y+adj2), line, font=font, fill=shadow_color)

            # Draw text
            draw.text((x, y), line, font=font, fill=text_color)

        img_np = np.array(img)

        txt_clip = ImageClip(img_np, transparent=True)
        txt_clip = txt_clip.with_duration(duration)

        txt_clip = txt_clip.with_effects([vfx.FadeIn(0.5), vfx.FadeOut(0.5)])

        return txt_clip
