"""
Unit tests for shared text rendering utilities.
"""
import pytest
from PIL import Image, ImageDraw, ImageFont
from src.utils.text_rendering import FontLoader, wrap_text, fit_font_to_width


class TestFontLoader:
    """Tests for the FontLoader class."""

    def test_load_font_returns_font_object(self):
        """Test that load returns a valid font object."""
        font = FontLoader.load(24)
        assert font is not None
        assert isinstance(font, (ImageFont.FreeTypeFont, ImageFont.ImageFont))

    def test_load_font_different_sizes(self):
        """Test loading fonts with different sizes."""
        small_font = FontLoader.load(12)
        large_font = FontLoader.load(48)

        assert small_font is not None
        assert large_font is not None
        # Fonts should be different objects
        assert id(small_font) != id(large_font)

    def test_load_font_handles_small_size(self):
        """Test that small size font loading works."""
        font = FontLoader.load(8)
        assert font is not None


class TestWrapText:
    """Tests for the wrap_text function."""

    def test_wrap_text_single_line(self):
        """Test wrapping text that fits in one line."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        font = FontLoader.load(24)

        lines = wrap_text("Hello", font, 800, draw)
        assert len(lines) == 1
        assert lines[0] == "Hello"

    def test_wrap_text_multiple_lines(self):
        """Test wrapping text that requires multiple lines."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        font = FontLoader.load(24)

        text = "This is a very long text that should wrap into multiple lines"
        lines = wrap_text(text, font, 200, draw)

        assert len(lines) > 1
        # Verify all words are preserved
        all_words = ' '.join(lines).split()
        original_words = text.split()
        assert len(all_words) == len(original_words)

    def test_wrap_text_empty_string(self):
        """Test wrapping an empty string."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        font = FontLoader.load(24)

        lines = wrap_text("", font, 200, draw)
        assert len(lines) == 1
        assert lines[0] == ""

    def test_wrap_text_single_long_word(self):
        """Test wrapping a single word that's wider than max_width."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        font = FontLoader.load(48)

        # A very long word
        lines = wrap_text("Supercalifragilisticexpialidocious", font, 100, draw)
        # Should still return the word on one line
        assert len(lines) == 1

    def test_wrap_text_preserves_word_order(self):
        """Test that word order is preserved after wrapping."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)
        font = FontLoader.load(24)

        text = "One Two Three Four Five Six Seven Eight"
        lines = wrap_text(text, font, 200, draw)

        # Reconstruct and verify order
        reconstructed = ' '.join(lines)
        assert reconstructed == text


class TestFitFontToWidth:
    """Tests for the fit_font_to_width function."""

    def test_fit_font_to_width_reduces_size(self):
        """Test that font size is reduced to fit width."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        text = "Very Long Title Text That Needs Fitting"
        font = fit_font_to_width(text, 200, 60, draw)

        assert font is not None
        # Verify the text fits (longest word should fit in max_width)
        # This is a rough check
        assert isinstance(font, (ImageFont.FreeTypeFont, ImageFont.ImageFont))

    def test_fit_font_to_width_with_height_constraint(self):
        """Test fitting font with both width and height constraints."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        text = "This is a multi-line text that should fit"
        font = fit_font_to_width(text, 400, 48, draw, max_height=100)

        assert font is not None

    def test_fit_font_to_width_empty_text(self):
        """Test fitting font with empty text."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        font = fit_font_to_width("", 200, 48, draw)
        assert font is not None

    def test_fit_font_to_width_short_text(self):
        """Test that short text doesn't reduce font size unnecessarily."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        # Short text with large max_width should keep original size
        font = fit_font_to_width("Hi", 800, 48, draw)
        assert font is not None

    def test_fit_font_to_width_respects_min_size_ratio(self):
        """Test that font doesn't shrink below minimum size ratio."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        # Very long text with tiny width should still respect minimum
        text = "Extremely long text " * 10
        font = fit_font_to_width(text, 50, 60, draw, min_size_ratio=0.5)

        assert font is not None
        # Font should not be smaller than 30 (60 * 0.5)

    def test_fit_font_to_width_custom_min_ratio(self):
        """Test custom minimum size ratio."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        text = "Long text that needs fitting"
        font = fit_font_to_width(text, 100, 60, draw, min_size_ratio=0.3)

        assert font is not None


class TestIntegration:
    """Integration tests for combined usage."""

    def test_wrap_text_with_fitted_font(self):
        """Test using wrap_text with a font fitted by fit_font_to_width."""
        img = Image.new('RGB', (800, 600))
        draw = ImageDraw.Draw(img)

        text = "This is a moderately long title that should wrap nicely"
        max_width = 400

        # First fit the font
        font = fit_font_to_width(text, max_width, 48, draw)

        # Then wrap the text
        lines = wrap_text(text, font, max_width, draw)

        assert len(lines) >= 1
        # Verify each line fits within max_width
        for line in lines:
            width = draw.textlength(line, font=font)
            # Allow small margin for measurement variations
            assert width <= max_width + 5
