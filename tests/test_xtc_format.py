"""Tests for xtc_format.py - XTG/XTH/XTC/XTCH binary encoding."""

import struct
from pathlib import Path

import numpy as np
from PIL import Image

from config import XTG_HEADER_SIZE, XTG_MARK, XTH_MARK
from xtc_format import (
    BookMetadata,
    ChapterInfo,
    encode_xtg_header,
    encode_xtg_page,
    encode_xth_header,
    encode_xth_page,
    quantize_to_4_levels,
    read_xtc_info,
    write_xtc_container,
)


class TestEncodeXTGHeader:
    """Test encode_xtg_header() function."""

    def test_header_length(self):
        """XTG header is 22 bytes."""
        header = encode_xtg_header(480, 800, 48000)
        assert len(header) == 22

    def test_magic_number(self):
        """Header starts with XTG magic number."""
        header = encode_xtg_header(480, 800, 48000)
        mark = struct.unpack("<I", header[:4])[0]
        assert mark == XTG_MARK

    def test_dimensions_in_header(self):
        """Width and height are correctly encoded."""
        header = encode_xtg_header(480, 800, 48000)
        _, width, height = struct.unpack("<IHH", header[:8])
        assert width == 480
        assert height == 800

    def test_data_size_in_header(self):
        """Data size is correctly encoded."""
        header = encode_xtg_header(480, 800, 48000)
        # Format: mark(4) + width(2) + height(2) + colorMode(1) + compression(1) + dataSize(4)
        data_size = struct.unpack("<I", header[10:14])[0]
        assert data_size == 48000

    def test_different_dimensions(self):
        """Test with different dimensions."""
        header = encode_xtg_header(320, 480, 19200)
        _, width, height = struct.unpack("<IHH", header[:8])
        assert width == 320
        assert height == 480


class TestEncodeXTHHeader:
    """Test encode_xth_header() function."""

    def test_header_length(self):
        """XTH header is 22 bytes."""
        header = encode_xth_header(480, 800, 96000)
        assert len(header) == 22

    def test_magic_number(self):
        """Header starts with XTH magic number."""
        header = encode_xth_header(480, 800, 96000)
        mark = struct.unpack("<I", header[:4])[0]
        assert mark == XTH_MARK

    def test_different_from_xtg(self):
        """XTH header has different magic than XTG."""
        xtg_header = encode_xtg_header(480, 800, 48000)
        xth_header = encode_xth_header(480, 800, 96000)

        xtg_mark = struct.unpack("<I", xtg_header[:4])[0]
        xth_mark = struct.unpack("<I", xth_header[:4])[0]

        assert xtg_mark != xth_mark


class TestQuantizeTo4Levels:
    """Test quantize_to_4_levels() function."""

    def test_white_pixels(self):
        """White pixels (255) -> level 0."""
        img = Image.new("L", (10, 10), 255)
        result = quantize_to_4_levels(img)
        assert np.all(result == 0)

    def test_black_pixels(self):
        """Black pixels (0) -> level 3."""
        img = Image.new("L", (10, 10), 0)
        result = quantize_to_4_levels(img)
        assert np.all(result == 3)

    def test_light_gray(self):
        """Light gray (170) -> level 1."""
        img = Image.new("L", (10, 10), 170)
        result = quantize_to_4_levels(img)
        assert np.all(result == 1)

    def test_dark_gray(self):
        """Dark gray (85) -> level 2."""
        img = Image.new("L", (10, 10), 85)
        result = quantize_to_4_levels(img)
        assert np.all(result == 2)

    def test_threshold_at_212(self):
        """Threshold at 212: 213->0, 212->1."""
        img = Image.new("L", (2, 1))
        img.putpixel((0, 0), 213)
        img.putpixel((1, 0), 212)
        result = quantize_to_4_levels(img)
        assert result[0, 0] == 0
        assert result[0, 1] == 1

    def test_threshold_at_127(self):
        """Threshold at 127: 128->1, 127->2."""
        img = Image.new("L", (2, 1))
        img.putpixel((0, 0), 128)
        img.putpixel((1, 0), 127)
        result = quantize_to_4_levels(img)
        assert result[0, 0] == 1
        assert result[0, 1] == 2

    def test_threshold_at_42(self):
        """Threshold at 42: 43->2, 42->3."""
        img = Image.new("L", (2, 1))
        img.putpixel((0, 0), 43)
        img.putpixel((1, 0), 42)
        result = quantize_to_4_levels(img)
        assert result[0, 0] == 2
        assert result[0, 1] == 3

    def test_rgb_input_converted(self):
        """RGB input is auto-converted to grayscale."""
        img = Image.new("RGB", (10, 10), (255, 255, 255))
        result = quantize_to_4_levels(img)
        assert np.all(result == 0)

    def test_output_shape(self):
        """Output shape matches input."""
        img = Image.new("L", (100, 50), 128)
        result = quantize_to_4_levels(img)
        assert result.shape == (50, 100)


class TestEncodeXTGPage:
    """Test encode_xtg_page() function."""

    def test_page_has_header(self):
        """XTG page starts with header."""
        img = Image.new("L", (480, 800), 255)
        encoded = encode_xtg_page(img)

        mark = struct.unpack("<I", encoded[:4])[0]
        assert mark == XTG_MARK

    def test_page_size(self):
        """XTG page total size is header + data."""
        img = Image.new("L", (480, 800), 255)
        encoded = encode_xtg_page(img)

        expected_data = (480 // 8) * 800  # 60 * 800 = 48000
        assert len(encoded) == XTG_HEADER_SIZE + expected_data

    def test_white_image_encoded(self):
        """White image encodes to 0xFF bytes (1-bit per pixel)."""
        img = Image.new("L", (8, 1), 255)
        encoded = encode_xtg_page(img)
        data = encoded[XTG_HEADER_SIZE:]

        # 8 white pixels = 0b11111111 = 0xFF
        assert data[0] == 0xFF

    def test_black_image_encoded(self):
        """Black image encodes to 0x00 bytes."""
        img = Image.new("L", (8, 1), 0)
        encoded = encode_xtg_page(img)
        data = encoded[XTG_HEADER_SIZE:]

        # 8 black pixels = 0b00000000 = 0x00
        assert data[0] == 0x00

    def test_width_padding(self):
        """Width not multiple of 8 gets padded."""
        img = Image.new("L", (10, 1), 255)
        encoded = encode_xtg_page(img)

        # 10 pixels -> ceil(10/8) = 2 bytes per row
        _, _, _, _, _, data_size = struct.unpack("<IHHBBI", encoded[:14])
        assert data_size == 2

    def test_alternating_pixels(self):
        """Test alternating black/white pixels."""
        img = Image.new("L", (8, 1))
        for x in range(8):
            img.putpixel((x, 0), 255 if x % 2 == 0 else 0)

        encoded = encode_xtg_page(img)
        data = encoded[XTG_HEADER_SIZE:]

        # Pattern: W B W B W B W B = 10101010 = 0xAA
        assert data[0] == 0xAA


class TestEncodeXTHPage:
    """Test encode_xth_page() function."""

    def test_page_has_xth_header(self):
        """XTH page starts with XTH header."""
        img = Image.new("L", (480, 800), 128)
        encoded = encode_xth_page(img)

        mark = struct.unpack("<I", encoded[:4])[0]
        assert mark == XTH_MARK

    def test_header_contains_dimensions(self):
        """XTH header contains correct dimensions."""
        img = Image.new("L", (480, 800), 128)
        encoded = encode_xth_page(img)

        _, width, height = struct.unpack("<IHH", encoded[:8])
        assert width == 480
        assert height == 800

    def test_page_has_two_bit_planes(self):
        """XTH page has data for two bit planes."""
        img = Image.new("L", (480, 800), 128)
        encoded = encode_xth_page(img)

        # Should have header + 2 planes of data
        assert len(encoded) > XTG_HEADER_SIZE


class TestWriteReadXTCContainer:
    """Test write_xtc_container() and read_xtc_info()."""

    def test_write_read_xtch(self, tmp_path: Path):
        """Write and read XTCH container."""
        output = tmp_path / "test.xtch"

        # Create test pages
        img = Image.new("L", (480, 800), 200)
        pages = [encode_xth_page(img), encode_xth_page(img)]
        chapters = [ChapterInfo("Chapter 1", 1, 2)]
        metadata = BookMetadata(title="Test Book", author="Test Author")

        write_xtc_container(output, pages, chapters, metadata, is_grayscale=True)

        assert output.exists()

        info = read_xtc_info(output)
        assert info["format"] == "XTCH"
        assert info["pages"] == 2
        assert info["title"] == "Test Book"

    def test_write_read_xtc_mono(self, tmp_path: Path):
        """Write and read XTC (mono) container."""
        output = tmp_path / "test.xtc"

        img = Image.new("L", (480, 800), 255)
        pages = [encode_xtg_page(img)]
        metadata = BookMetadata(title="Mono Book")

        write_xtc_container(output, pages, [], metadata, is_grayscale=False)

        info = read_xtc_info(output)
        assert info["format"] == "XTC"
        assert info["pages"] == 1
        assert info["title"] == "Mono Book"

    def test_title_truncation(self, tmp_path: Path):
        """Long titles are truncated to 127 chars."""
        output = tmp_path / "test.xtch"

        img = Image.new("L", (480, 800), 200)
        pages = [encode_xth_page(img)]
        long_title = "A" * 200  # Longer than 128 byte limit
        metadata = BookMetadata(title=long_title)

        write_xtc_container(output, pages, [], metadata, is_grayscale=True)

        info = read_xtc_info(output)
        assert len(info["title"]) <= 127

    def test_empty_title(self, tmp_path: Path):
        """Empty title is handled."""
        output = tmp_path / "test.xtch"

        img = Image.new("L", (480, 800), 200)
        pages = [encode_xth_page(img)]
        metadata = BookMetadata()

        write_xtc_container(output, pages, [], metadata, is_grayscale=True)

        info = read_xtc_info(output)
        assert info["title"] == ""

    def test_multiple_pages(self, tmp_path: Path):
        """Write container with multiple pages."""
        output = tmp_path / "test.xtch"

        img = Image.new("L", (480, 800), 200)
        pages = [encode_xth_page(img) for _ in range(5)]
        metadata = BookMetadata(title="Multi-Page Book")

        write_xtc_container(output, pages, [], metadata, is_grayscale=True)

        info = read_xtc_info(output)
        assert info["pages"] == 5


class TestBookMetadata:
    """Test BookMetadata dataclass."""

    def test_default_values(self):
        """Default metadata has empty strings."""
        meta = BookMetadata()
        assert meta.title == ""
        assert meta.author == ""

    def test_with_values(self):
        """Metadata with values."""
        meta = BookMetadata(title="Test", author="Author")
        assert meta.title == "Test"
        assert meta.author == "Author"


class TestChapterInfo:
    """Test ChapterInfo dataclass."""

    def test_creation(self):
        """Create chapter info."""
        chapter = ChapterInfo("Chapter 1", 1, 10)
        assert chapter.title == "Chapter 1"
        assert chapter.start_page == 1
        assert chapter.end_page == 10
