"""Tests for config.py - configuration constants and helpers."""

from dataclasses import FrozenInstanceError

import pytest

from config import (
    DEFAULT_FONT_SIZE,
    DEFAULT_MAX_WIDTH,
    DEFAULT_QUALITY,
    DISPLAY,
    DISPLAY_HEIGHT,
    DISPLAY_WIDTH,
    HEADING_SIZE_MULTIPLIERS,
    LINE_HEIGHT_RATIO,
    MARGINS,
    MARGINS_CONFIG,
    OPTIMIZER,
    PARAGRAPH_SPACING,
    TYPOGRAPHY,
    X4_CSS,
    X4_CSS_FILENAME,
    XTC_FORMAT,
    XTC_MARK,
    XTCH_MARK,
    XTG_HEADER_SIZE,
    XTG_MARK,
    XTH_MARK,
    get_heading_sizes,
)


class TestDisplayConstants:
    """Test display specification constants."""

    def test_display_width(self):
        """Verify display width is 480 pixels."""
        assert DISPLAY_WIDTH == 480
        assert DISPLAY.WIDTH == 480

    def test_display_height(self):
        """Verify display height is 800 pixels."""
        assert DISPLAY_HEIGHT == 800
        assert DISPLAY.HEIGHT == 800

    def test_display_ppi(self):
        """Verify display PPI is 220."""
        assert DISPLAY.PPI == 220

    def test_display_frozen(self):
        """Test that display config is frozen (immutable)."""
        with pytest.raises(FrozenInstanceError):
            DISPLAY.WIDTH = 100


class TestTypographyConstants:
    """Test typography configuration constants."""

    def test_default_font_size(self):
        """Verify default font size is 34 (~11pt at 220 PPI)."""
        assert DEFAULT_FONT_SIZE == 34
        assert TYPOGRAPHY.DEFAULT_FONT_SIZE == 34

    def test_line_height_ratio(self):
        """Verify line height ratio is 1.4."""
        assert LINE_HEIGHT_RATIO == 1.4
        assert TYPOGRAPHY.LINE_HEIGHT_RATIO == 1.4

    def test_paragraph_spacing(self):
        """Verify paragraph spacing is 16 pixels."""
        assert PARAGRAPH_SPACING == 16
        assert TYPOGRAPHY.PARAGRAPH_SPACING == 16

    def test_min_lines_together(self):
        """Verify widow/orphan control setting."""
        assert TYPOGRAPHY.MIN_LINES_TOGETHER == 2

    def test_typography_frozen(self):
        """Test that typography config is frozen."""
        with pytest.raises(FrozenInstanceError):
            TYPOGRAPHY.DEFAULT_FONT_SIZE = 20


class TestMarginsConstants:
    """Test margin configuration constants."""

    def test_margins_top(self):
        """Verify top margin."""
        assert MARGINS["top"] == 20
        assert MARGINS_CONFIG.TOP == 20

    def test_margins_bottom(self):
        """Verify bottom margin (extra for page number)."""
        assert MARGINS["bottom"] == 40
        assert MARGINS_CONFIG.BOTTOM == 40

    def test_margins_left(self):
        """Verify left margin."""
        assert MARGINS["left"] == 16
        assert MARGINS_CONFIG.LEFT == 16

    def test_margins_right(self):
        """Verify right margin."""
        assert MARGINS["right"] == 16
        assert MARGINS_CONFIG.RIGHT == 16

    def test_margins_frozen(self):
        """Test that margins config is frozen."""
        with pytest.raises(FrozenInstanceError):
            MARGINS_CONFIG.TOP = 50


class TestXTCFormatConstants:
    """Test XTC/XTCH binary format constants."""

    def test_xtg_mark(self):
        """Verify XTG magic number (little-endian 'XTG\\0')."""
        assert XTG_MARK == 0x00475458
        assert XTC_FORMAT.XTG_MARK == 0x00475458

    def test_xth_mark(self):
        """Verify XTH magic number (little-endian 'XTH\\0')."""
        assert XTH_MARK == 0x00485458
        assert XTC_FORMAT.XTH_MARK == 0x00485458

    def test_xtc_mark(self):
        """Verify XTC magic number (little-endian 'XTC\\0')."""
        assert XTC_MARK == 0x00435458
        assert XTC_FORMAT.XTC_MARK == 0x00435458

    def test_xtch_mark(self):
        """Verify XTCH magic number ('XTCH')."""
        assert XTCH_MARK == 0x48435458
        assert XTC_FORMAT.XTCH_MARK == 0x48435458

    def test_xtg_header_size(self):
        """Verify XTG header is 22 bytes."""
        assert XTG_HEADER_SIZE == 22
        assert XTC_FORMAT.XTG_HEADER_SIZE == 22

    def test_xtc_header_size(self):
        """Verify XTC container header is 56 bytes."""
        assert XTC_FORMAT.XTC_HEADER_SIZE == 56

    def test_page_table_entry_size(self):
        """Verify page table entry is 16 bytes."""
        assert XTC_FORMAT.PAGE_TABLE_ENTRY_SIZE == 16

    def test_title_max_size(self):
        """Verify max title size is 128 bytes."""
        assert XTC_FORMAT.TITLE_MAX_SIZE == 128

    def test_xtc_format_frozen(self):
        """Test that XTC format config is frozen."""
        with pytest.raises(FrozenInstanceError):
            XTC_FORMAT.XTG_MARK = 0


class TestOptimizerConstants:
    """Test optimizer default constants."""

    def test_default_max_width(self):
        """Verify default max image width matches display."""
        assert DEFAULT_MAX_WIDTH == 480
        assert OPTIMIZER.MAX_WIDTH == 480

    def test_default_quality(self):
        """Verify default JPEG quality."""
        assert DEFAULT_QUALITY == 75
        assert OPTIMIZER.QUALITY == 75

    def test_default_contrast_boost(self):
        """Verify default contrast boost factor."""
        assert OPTIMIZER.CONTRAST_BOOST == 1.2

    def test_optimizer_frozen(self):
        """Test that optimizer config is frozen."""
        with pytest.raises(FrozenInstanceError):
            OPTIMIZER.MAX_WIDTH = 100


class TestGetHeadingSizes:
    """Test get_heading_sizes() function."""

    def test_default_base_size(self):
        """Test heading sizes with default base (34)."""
        sizes = get_heading_sizes(34)

        # Verify all heading levels are present
        assert set(sizes.keys()) == {1, 2, 3, 4, 5, 6}

        # Verify multipliers
        assert sizes[1] == int(34 * 1.8)  # 61
        assert sizes[2] == int(34 * 1.5)  # 51
        assert sizes[3] == int(34 * 1.3)  # 44
        assert sizes[4] == int(34 * 1.15)  # 39
        assert sizes[5] == int(34 * 1.0)  # 34
        assert sizes[6] == int(34 * 0.9)  # 30

    def test_custom_base_size(self):
        """Test heading sizes with custom base size."""
        sizes = get_heading_sizes(40)

        assert sizes[1] == int(40 * 1.8)  # 72
        assert sizes[2] == int(40 * 1.5)  # 60
        assert sizes[5] == 40  # 100%

    def test_small_base_size(self):
        """Test heading sizes with small base size."""
        sizes = get_heading_sizes(20)

        assert sizes[1] == 36  # 20 * 1.8
        assert sizes[6] == 18  # 20 * 0.9

    def test_multipliers_match(self):
        """Verify sizes match HEADING_SIZE_MULTIPLIERS."""
        base = 34
        sizes = get_heading_sizes(base)

        for level, mult in HEADING_SIZE_MULTIPLIERS.items():
            expected = int(base * mult)
            assert sizes[level] == expected, f"Level {level}: {sizes[level]} != {expected}"


class TestX4CSS:
    """Test the optimized X4 CSS content."""

    def test_x4_css_not_empty(self):
        """Verify X4 CSS content exists."""
        assert len(X4_CSS) > 0

    def test_x4_css_filename(self):
        """Verify X4 CSS filename."""
        assert X4_CSS_FILENAME == "x4-sanitizer.css"

    def test_x4_css_has_body_rules(self):
        """Verify X4 CSS has body styling."""
        assert "body {" in X4_CSS
        assert "font-family: serif" in X4_CSS

    def test_x4_css_has_img_rules(self):
        """Verify X4 CSS has image styling."""
        assert "img {" in X4_CSS
        assert "max-width: 100%" in X4_CSS

    def test_x4_css_removes_float(self):
        """Verify X4 CSS has float override."""
        assert "float: none !important" in X4_CSS
