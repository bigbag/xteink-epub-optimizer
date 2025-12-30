"""Tests for text_renderer.py - PIL-based text rendering."""

from pathlib import Path

from PIL import Image

from config import DISPLAY_HEIGHT, DISPLAY_WIDTH
from epub_parser import TextBlock, TextStyle
from text_renderer import FontFamily, TextRenderer


class TestFontFamily:
    """Test FontFamily dataclass."""

    def test_get_path_regular(self, mock_font_path: Path):
        """Get regular font path."""
        ff = FontFamily(regular=mock_font_path)
        assert ff.get_path() == mock_font_path

    def test_get_path_bold(self, mock_font_path: Path):
        """Get bold font path when available."""
        bold_path = mock_font_path  # Using same font for test
        ff = FontFamily(regular=mock_font_path, bold=bold_path)
        assert ff.get_path(bold=True) == bold_path

    def test_get_path_italic(self, mock_font_path: Path):
        """Get italic font path when available."""
        italic_path = mock_font_path
        ff = FontFamily(regular=mock_font_path, italic=italic_path)
        assert ff.get_path(italic=True) == italic_path

    def test_get_path_bold_italic(self, mock_font_path: Path):
        """Get bold-italic font path when available."""
        bi_path = mock_font_path
        ff = FontFamily(regular=mock_font_path, bold_italic=bi_path)
        assert ff.get_path(bold=True, italic=True) == bi_path

    def test_fallback_bold_to_regular(self, mock_font_path: Path):
        """Fallback to regular when bold not available."""
        ff = FontFamily(regular=mock_font_path)
        assert ff.get_path(bold=True) == mock_font_path

    def test_fallback_italic_to_regular(self, mock_font_path: Path):
        """Fallback to regular when italic not available."""
        ff = FontFamily(regular=mock_font_path)
        assert ff.get_path(italic=True) == mock_font_path

    def test_fallback_bold_italic_to_bold(self, mock_font_path: Path):
        """Fallback bold-italic to bold when bi not available."""
        ff = FontFamily(regular=mock_font_path, bold=mock_font_path)
        result = ff.get_path(bold=True, italic=True)
        assert result == mock_font_path

    def test_fallback_bold_italic_to_italic(self, mock_font_path: Path):
        """Fallback bold-italic to italic when bold/bi not available."""
        italic_path = mock_font_path
        ff = FontFamily(regular=mock_font_path, italic=italic_path)
        result = ff.get_path(bold=True, italic=True)
        assert result == italic_path

    def test_full_fallback_chain(self, mock_font_path: Path):
        """Test full fallback chain for bold-italic."""
        ff = FontFamily(regular=mock_font_path)
        result = ff.get_path(bold=True, italic=True)
        assert result == mock_font_path


class TestTextRenderer:
    """Test TextRenderer class."""

    def test_creation(self, font_family: FontFamily):
        """Create TextRenderer."""
        renderer = TextRenderer(font_family)
        assert renderer is not None
        assert renderer.base_font_size == 34  # Default

    def test_custom_base_font_size(self, font_family: FontFamily):
        """Create TextRenderer with custom font size."""
        renderer = TextRenderer(font_family, base_font_size=40)
        assert renderer.base_font_size == 40

    def test_get_font(self, font_family: FontFamily):
        """Get font returns FreeTypeFont."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)
        assert font is not None

    def test_font_caching(self, font_family: FontFamily):
        """Same font/size returns cached instance."""
        renderer = TextRenderer(font_family)
        font1 = renderer.get_font(20)
        font2 = renderer.get_font(20)
        assert font1 is font2

    def test_different_sizes_not_cached_together(self, font_family: FontFamily):
        """Different sizes return different fonts."""
        renderer = TextRenderer(font_family)
        font1 = renderer.get_font(20)
        font2 = renderer.get_font(30)
        assert font1 is not font2


class TestTextRendererWrapText:
    """Test TextRenderer.wrap_text() method."""

    def test_empty_string(self, font_family: FontFamily):
        """Empty string returns empty list."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)
        lines = renderer.wrap_text("", font, 400)
        assert lines == []

    def test_single_word(self, font_family: FontFamily):
        """Single word that fits returns one line."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)
        lines = renderer.wrap_text("Hello", font, 400)
        assert len(lines) == 1
        assert lines[0] == "Hello"

    def test_wraps_long_text(self, font_family: FontFamily):
        """Long text wraps to multiple lines."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)
        long_text = "This is a very long sentence that should definitely wrap to multiple lines"
        lines = renderer.wrap_text(long_text, font, 200)
        assert len(lines) > 1

    def test_preserves_all_words(self, font_family: FontFamily):
        """All words are preserved after wrapping."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)
        text = "One Two Three Four Five"
        lines = renderer.wrap_text(text, font, 100)

        # Join all lines and compare
        result = " ".join(lines)
        assert "One" in result
        assert "Five" in result


class TestTextRendererMeasureText:
    """Test TextRenderer.measure_text() method."""

    def test_returns_width_height(self, font_family: FontFamily):
        """measure_text returns (width, height)."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)
        width, height = renderer.measure_text("Hello", font)

        assert width > 0
        assert height > 0

    def test_longer_text_wider(self, font_family: FontFamily):
        """Longer text has greater width."""
        renderer = TextRenderer(font_family)
        font = renderer.get_font(20)

        w1, _ = renderer.measure_text("Hi", font)
        w2, _ = renderer.measure_text("Hello World", font)

        assert w2 > w1


class TestTextRendererEstimateBlockHeight:
    """Test TextRenderer.estimate_block_height() method."""

    def test_returns_positive_height(self, font_family: FontFamily):
        """Estimate returns positive height."""
        renderer = TextRenderer(font_family)
        block = TextBlock(text="Hello", style=TextStyle())

        height = renderer.estimate_block_height(block, 400)

        assert height > 0

    def test_longer_text_taller(self, font_family: FontFamily):
        """Longer text that wraps has greater height."""
        renderer = TextRenderer(font_family)

        short_block = TextBlock(text="Hi", style=TextStyle())
        long_block = TextBlock(
            text="This is a very long paragraph that will definitely need to wrap to multiple lines",
            style=TextStyle(),
        )

        h1 = renderer.estimate_block_height(short_block, 200)
        h2 = renderer.estimate_block_height(long_block, 200)

        assert h2 > h1

    def test_heading_affects_height(self, font_family: FontFamily):
        """Heading style affects height (larger font)."""
        renderer = TextRenderer(font_family)

        regular_block = TextBlock(text="Text", style=TextStyle())
        heading_block = TextBlock(
            text="Text",
            style=TextStyle(is_heading=True, heading_level=1),
        )

        h1 = renderer.estimate_block_height(regular_block, 400)
        h2 = renderer.estimate_block_height(heading_block, 400)

        assert h2 > h1  # Heading should be taller due to larger font


class TestTextRendererRenderPage:
    """Test TextRenderer.render_page() method."""

    def test_returns_image(self, font_family: FontFamily):
        """render_page returns PIL Image."""
        renderer = TextRenderer(font_family)
        blocks = [TextBlock(text="Hello", style=TextStyle())]

        image = renderer.render_page(blocks, page_number=1)

        assert isinstance(image, Image.Image)

    def test_image_dimensions(self, font_family: FontFamily):
        """Image has correct display dimensions."""
        renderer = TextRenderer(font_family)
        blocks = [TextBlock(text="Hello", style=TextStyle())]

        image = renderer.render_page(blocks, page_number=1)

        assert image.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)

    def test_image_mode_grayscale(self, font_family: FontFamily):
        """Image is grayscale (mode 'L')."""
        renderer = TextRenderer(font_family)
        blocks = [TextBlock(text="Hello", style=TextStyle())]

        image = renderer.render_page(blocks, page_number=1)

        assert image.mode == "L"

    def test_empty_blocks(self, font_family: FontFamily):
        """Handle empty blocks list."""
        renderer = TextRenderer(font_family)

        image = renderer.render_page([], page_number=1)

        assert image is not None
        assert image.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)


class TestTextRendererRenderChapterTitle:
    """Test TextRenderer.render_chapter_title() method."""

    def test_returns_image(self, font_family: FontFamily):
        """render_chapter_title returns PIL Image."""
        renderer = TextRenderer(font_family)

        image = renderer.render_chapter_title("Test Chapter", chapter_num=1)

        assert isinstance(image, Image.Image)

    def test_image_dimensions(self, font_family: FontFamily):
        """Image has correct display dimensions."""
        renderer = TextRenderer(font_family)

        image = renderer.render_chapter_title("Test Chapter", chapter_num=1)

        assert image.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
