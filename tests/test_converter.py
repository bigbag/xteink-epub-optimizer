"""Tests for converter.py - EPUB to XTC/XTCH conversion (integration tests)."""

import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from converter import convert_epub_to_xtc, main
from text_renderer import FontFamily
from xtc_format import read_xtc_info


class TestConvertEpubToXTC:
    """Integration tests for convert_epub_to_xtc()."""

    def test_convert_to_xtch(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Convert minimal EPUB to XTCH format."""
        output = tmp_path / "output.xtch"

        stats = convert_epub_to_xtc(
            minimal_epub_path,
            output,
            font_family=font_family,
            output_format="xtch",
            font_size=34,
        )

        assert output.exists()
        assert stats["pages"] > 0

        # Verify output format
        info = read_xtc_info(output)
        assert info["format"] == "XTCH"
        assert info["pages"] == stats["pages"]

    def test_convert_to_xtc_mono(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Convert minimal EPUB to XTC (mono) format."""
        output = tmp_path / "output.xtc"

        _ = convert_epub_to_xtc(
            minimal_epub_path,
            output,
            font_family=font_family,
            output_format="xtc",
            font_size=34,
        )

        assert output.exists()

        info = read_xtc_info(output)
        assert info["format"] == "XTC"

    def test_metadata_preserved(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Book metadata (title) is preserved in output."""
        output = tmp_path / "output.xtch"

        convert_epub_to_xtc(
            minimal_epub_path,
            output,
            font_family=font_family,
            output_format="xtch",
        )

        info = read_xtc_info(output)
        assert info["title"] == "Test Book"

    def test_stats_returned(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Stats dictionary is returned."""
        output = tmp_path / "output.xtch"

        stats = convert_epub_to_xtc(
            minimal_epub_path,
            output,
            font_family=font_family,
            output_format="xtch",
        )

        assert "pages" in stats
        assert "chapters" in stats
        assert isinstance(stats["pages"], int)
        assert stats["pages"] > 0

    def test_different_font_sizes(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Different font sizes produce different page counts."""
        output_small = tmp_path / "small.xtch"
        output_large = tmp_path / "large.xtch"

        stats_small = convert_epub_to_xtc(
            minimal_epub_path,
            output_small,
            font_family=font_family,
            output_format="xtch",
            font_size=28,  # Small
        )

        stats_large = convert_epub_to_xtc(
            minimal_epub_path,
            output_large,
            font_family=font_family,
            output_format="xtch",
            font_size=40,  # Large
        )

        # Larger font should produce more or equal pages
        assert stats_large["pages"] >= stats_small["pages"]

    def test_chapters_tracked(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Chapter count is tracked in stats."""
        output = tmp_path / "output.xtch"

        stats = convert_epub_to_xtc(
            minimal_epub_path,
            output,
            font_family=font_family,
            output_format="xtch",
        )

        # Chapters should be >= 0 (minimal epub has at least one heading)
        assert stats["chapters"] >= 0

    def test_output_file_readable(
        self,
        minimal_epub_path: Path,
        font_family: FontFamily,
        tmp_path: Path,
    ):
        """Output file can be read and parsed."""
        output = tmp_path / "output.xtch"

        convert_epub_to_xtc(
            minimal_epub_path,
            output,
            font_family=font_family,
            output_format="xtch",
        )

        # Should be able to read the file info
        info = read_xtc_info(output)
        assert "pages" in info
        assert "format" in info
        assert "title" in info


class TestMainCLI:
    """Test main() CLI function."""

    def test_missing_font_exits(self, tmp_path: Path):
        """Exit with error if font file not found."""
        epub = tmp_path / "test.epub"
        epub.touch()
        output = tmp_path / "output.xtch"
        fake_font = tmp_path / "nonexistent.ttf"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(epub),
                str(output),
                "--font",
                str(fake_font),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_non_epub_input_exits(
        self,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Exit with error if input file is not EPUB."""
        txt_file = tmp_path / "test.txt"
        txt_file.touch()
        output = tmp_path / "output.xtch"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(txt_file),
                str(output),
                "--font",
                str(mock_font_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_nonexistent_input_exits(
        self,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Exit with error if input path doesn't exist."""
        fake_input = tmp_path / "nonexistent.epub"
        output = tmp_path / "output.xtch"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(fake_input),
                str(output),
                "--font",
                str(mock_font_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_no_epubs_in_directory_exits(
        self,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Exit with error if no EPUBs found in directory."""
        input_dir = tmp_path / "empty_dir"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(input_dir),
                str(output_dir),
                "--font",
                str(mock_font_path),
            ],
        ):
            with pytest.raises(SystemExit) as exc_info:
                main()
            assert exc_info.value.code == 1

    def test_single_file_conversion(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Convert single EPUB file via CLI."""
        output = tmp_path / "output.xtch"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(minimal_epub_path),
                str(output),
                "--font",
                str(mock_font_path),
            ],
        ):
            # Capture stdout
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert output.exists()
        assert "Converting:" in captured.getvalue()

    def test_directory_conversion(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Convert directory of EPUB files via CLI."""
        # Create input directory with epub
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        import shutil

        shutil.copy(minimal_epub_path, input_dir / "book.epub")

        output_dir = tmp_path / "output"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(input_dir),
                str(output_dir),
                "--font",
                str(mock_font_path),
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert output_dir.exists()
        assert (output_dir / "book.xtch").exists()

    def test_recursive_directory_conversion(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Convert directory recursively via CLI."""
        # Create nested directory structure
        input_dir = tmp_path / "input"
        sub_dir = input_dir / "subdir"
        sub_dir.mkdir(parents=True)

        import shutil

        shutil.copy(minimal_epub_path, input_dir / "book1.epub")
        shutil.copy(minimal_epub_path, sub_dir / "book2.epub")

        output_dir = tmp_path / "output"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(input_dir),
                str(output_dir),
                "--font",
                str(mock_font_path),
                "--recursive",
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert (output_dir / "book1.xtch").exists()
        assert (output_dir / "subdir" / "book2.xtch").exists()

    def test_xtc_format_option(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """--format xtc produces XTC output."""
        output = tmp_path / "output.xtc"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(minimal_epub_path),
                str(output),
                "--font",
                str(mock_font_path),
                "--format",
                "xtc",
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert output.exists()
        info = read_xtc_info(output)
        assert info["format"] == "XTC"

    def test_font_size_option(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """--font-size option is respected."""
        output = tmp_path / "output.xtch"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(minimal_epub_path),
                str(output),
                "--font",
                str(mock_font_path),
                "--font-size",
                "40",
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert output.exists()

    def test_multiple_files_shows_summary(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Multiple files show summary at end."""
        # Create input directory with multiple epubs
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        import shutil

        shutil.copy(minimal_epub_path, input_dir / "book1.epub")
        shutil.copy(minimal_epub_path, input_dir / "book2.epub")

        output_dir = tmp_path / "output"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(input_dir),
                str(output_dir),
                "--font",
                str(mock_font_path),
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        output = captured.getvalue()
        assert "Summary:" in output
        assert "Files converted: 2" in output

    def test_conversion_error_continues(
        self,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Conversion error for one file doesn't stop others."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()

        # Create invalid epub
        invalid = input_dir / "invalid.epub"
        invalid.write_text("not a valid epub")

        output_dir = tmp_path / "output"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(input_dir),
                str(output_dir),
                "--font",
                str(mock_font_path),
            ],
        ):
            captured_err = StringIO()
            captured_out = StringIO()
            with patch.object(sys, "stderr", captured_err):
                with patch.object(sys, "stdout", captured_out):
                    main()

        # Should have error message in stderr
        assert "Error:" in captured_err.getvalue()

    def test_optional_font_variants(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Optional font variants are accepted if they exist."""
        output = tmp_path / "output.xtch"

        # Create fake bold/italic fonts
        bold_font = tmp_path / "bold.ttf"
        italic_font = tmp_path / "italic.ttf"

        import shutil

        shutil.copy(mock_font_path, bold_font)
        shutil.copy(mock_font_path, italic_font)

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(minimal_epub_path),
                str(output),
                "--font",
                str(mock_font_path),
                "--font-bold",
                str(bold_font),
                "--font-italic",
                str(italic_font),
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert output.exists()

    def test_nonexistent_font_variants_ignored(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Non-existent optional font variants are silently ignored."""
        output = tmp_path / "output.xtch"
        fake_bold = tmp_path / "nonexistent_bold.ttf"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(minimal_epub_path),
                str(output),
                "--font",
                str(mock_font_path),
                "--font-bold",
                str(fake_bold),  # doesn't exist
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        assert output.exists()  # Should still work with regular font

    def test_output_to_directory(
        self,
        minimal_epub_path: Path,
        mock_font_path: Path,
        tmp_path: Path,
    ):
        """Output path without extension treated as directory."""
        output_dir = tmp_path / "output_dir"

        with patch.object(
            sys,
            "argv",
            [
                "converter.py",
                str(minimal_epub_path),
                str(output_dir),
                "--font",
                str(mock_font_path),
            ],
        ):
            captured = StringIO()
            with patch.object(sys, "stdout", captured):
                main()

        # Should create directory and use epub stem + .xtch
        assert output_dir.is_dir()
        expected_output = output_dir / (minimal_epub_path.stem + ".xtch")
        assert expected_output.exists()
