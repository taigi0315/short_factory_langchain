"""
Shared text rendering utilities for video generation.

This module provides common font loading and text wrapping functionality
used across video generation and assembly agents.
"""
from typing import List, Optional
from PIL import ImageFont, ImageDraw


class FontLoader:
    """Centralized font loading with cross-platform fallback logic."""

    FONT_PATHS = [
        "Arial.ttf",  # Windows
        "/System/Library/Fonts/Helvetica.ttc",  # macOS
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux/Docker
    ]

    @staticmethod
    def load(font_size: int) -> ImageFont.FreeTypeFont:
        """
        Load a TrueType font with automatic fallbacks.

        Tries multiple font paths in order and falls back to the default
        bitmap font if none are available.

        Args:
            font_size: Size of the font in pixels

        Returns:
            ImageFont.FreeTypeFont: Loaded font object
        """
        for path in FontLoader.FONT_PATHS:
            try:
                return ImageFont.truetype(path, font_size)
            except (OSError, IOError):
                continue

        # Last resort: use default bitmap font
        return ImageFont.load_default()


def wrap_text(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    draw: ImageDraw.ImageDraw
) -> List[str]:
    """
    Wrap text to fit within a maximum width.

    Splits text into multiple lines, ensuring no line exceeds max_width.
    Words are kept intact and never split mid-word.

    Args:
        text: The text to wrap
        font: Font to use for measuring text width
        max_width: Maximum width in pixels for each line
        draw: ImageDraw object for measuring text

    Returns:
        List[str]: List of text lines, each fitting within max_width

    Example:
        >>> from PIL import Image, ImageDraw
        >>> img = Image.new('RGB', (800, 600))
        >>> draw = ImageDraw.Draw(img)
        >>> font = FontLoader.load(24)
        >>> lines = wrap_text("Hello world this is a long text", font, 200, draw)
        >>> for line in lines:
        ...     print(line)
    """
    words = text.split()
    lines = []
    current_line: List[str] = []

    for word in words:
        test_line = ' '.join(current_line + [word])
        test_width = draw.textlength(test_line, font=font)

        if test_width <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(' '.join(current_line))
            current_line = [word]

    if current_line:
        lines.append(' '.join(current_line))

    return lines if lines else [text]


def fit_font_to_width(
    text: str,
    max_width: int,
    start_font_size: int,
    draw: ImageDraw.ImageDraw,
    max_height: Optional[int] = None,
    min_size_ratio: float = 0.4
) -> ImageFont.FreeTypeFont:
    """
    Automatically reduce font size until text fits within constraints.

    Iteratively reduces font size from start_font_size until the text
    (or longest word) fits within max_width. Optionally also checks
    that wrapped text fits within max_height.

    Args:
        text: The text to fit
        max_width: Maximum width in pixels
        start_font_size: Starting font size to try
        draw: ImageDraw object for measuring text
        max_height: Optional maximum height constraint
        min_size_ratio: Minimum font size as ratio of start size (default 0.4)

    Returns:
        ImageFont.FreeTypeFont: Font sized to fit the constraints

    Example:
        >>> from PIL import Image, ImageDraw
        >>> img = Image.new('RGB', (800, 600))
        >>> draw = ImageDraw.Draw(img)
        >>> font = fit_font_to_width("Long Title Text", 400, 60, draw)
    """
    current_size = start_font_size
    font = FontLoader.load(current_size)

    words = text.split()
    if not words:
        return font

    # Minimum legible size
    min_size = max(20, int(start_font_size * min_size_ratio))

    while current_size > min_size:
        # Find the longest word width
        max_word_w = 0
        for word in words:
            w = draw.textlength(word, font=font)
            if w > max_word_w:
                max_word_w = w

        # Check height constraint if specified
        if max_height:
            lines = wrap_text(text, font, max_width, draw)
            bbox = draw.textbbox((0, 0), "Mg", font=font)
            line_height = int((bbox[3] - bbox[1]) * 1.3)
            total_height = len(lines) * line_height

            if max_word_w <= max_width and total_height <= max_height:
                return font
        elif max_word_w <= max_width:
            return font

        # Reduce font size and try again
        current_size -= 5
        font = FontLoader.load(current_size)

    return font
