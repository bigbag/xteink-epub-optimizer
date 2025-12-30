"""Tests for optimizer.py - CSS sanitization and EPUB optimization."""

import zipfile
from pathlib import Path

from PIL import Image

from config import X4_CSS_FILENAME
from optimizer import (
    add_css_to_manifest,
    calculate_relative_path,
    inject_css_link,
    process_images,
    rebuild_epub,
    remove_font_from_manifest,
    remove_fonts,
    sanitize_css_text,
    sanitize_epub_file,
)


class TestSanitizeCSSText:
    """Test sanitize_css_text() function."""

    # ==========================================================================
    # Font removal tests
    # ==========================================================================

    def test_removes_font_face(self):
        """Remove @font-face blocks."""
        css = "@font-face { font-family: 'Test'; src: url('test.ttf'); }"
        result = sanitize_css_text(css)

        assert "@font-face" not in result

    def test_removes_font_face_multiline(self):
        """Remove multiline @font-face blocks."""
        css = """
@font-face {
    font-family: 'Test';
    src: url('test.ttf');
    font-weight: normal;
}
body { color: black; }
"""
        result = sanitize_css_text(css)

        assert "@font-face" not in result
        assert "color: black" in result

    def test_removes_font_family(self):
        """Remove font-family declarations."""
        css = "body { font-family: 'CustomFont', serif; color: black; }"
        result = sanitize_css_text(css)

        assert "font-family" not in result
        assert "color: black" in result

    def test_keeps_fonts_when_flag_false(self, css_with_fonts: str):
        """Keep fonts when remove_fonts=False."""
        result = sanitize_css_text(css_with_fonts, remove_fonts=False)

        assert "font-family" in result

    # ==========================================================================
    # Layout property removal tests
    # ==========================================================================

    def test_removes_float(self):
        """Remove float declarations."""
        css = "div { float: left; color: red; }"
        result = sanitize_css_text(css)

        assert "float" not in result
        assert "color: red" in result

    def test_removes_float_right(self):
        """Remove float: right."""
        css = ".sidebar { float: right; }"
        result = sanitize_css_text(css)

        assert "float" not in result

    def test_removes_position_absolute(self):
        """Remove position: absolute."""
        css = "div { position: absolute; top: 0; }"
        result = sanitize_css_text(css)

        assert "position" not in result or "absolute" not in result

    def test_removes_position_fixed(self):
        """Remove position: fixed."""
        css = ".header { position: fixed; }"
        result = sanitize_css_text(css)

        assert "fixed" not in result

    def test_keeps_position_relative(self):
        """Keep position: relative (not removed by pattern)."""
        css = "div { position: relative; }"
        result = sanitize_css_text(css)

        # position: relative should be kept (pattern only matches absolute/fixed)
        assert "relative" in result

    def test_removes_display_flex(self):
        """Remove display: flex."""
        css = ".container { display: flex; justify-content: center; }"
        result = sanitize_css_text(css)

        assert "flex" not in result

    def test_removes_display_grid(self):
        """Remove display: grid."""
        css = ".layout { display: grid; grid-template-columns: 1fr 1fr; }"
        result = sanitize_css_text(css)

        assert "grid" not in result or "display" not in result

    def test_removes_fixed_width_px(self):
        """Remove fixed width in pixels."""
        css = "div { width: 500px; }"
        result = sanitize_css_text(css)

        assert "width: 500px" not in result

    def test_removes_fixed_height_px(self):
        """Remove fixed height in pixels."""
        css = "div { height: 300px; }"
        result = sanitize_css_text(css)

        assert "height: 300px" not in result

    def test_keeps_max_width(self):
        """Keep max-width declarations (negative lookbehind in pattern)."""
        css = "img { max-width: 100%; }"
        result = sanitize_css_text(css)

        assert "max-width" in result

    def test_removes_column_count(self):
        """Remove column-count."""
        css = ".text { column-count: 2; }"
        result = sanitize_css_text(css)

        assert "column-count" not in result

    def test_removes_large_text_indent(self):
        """Remove large text-indent values."""
        css = "p { text-indent: -9999px; }"
        result = sanitize_css_text(css)

        assert "-9999px" not in result

    # ==========================================================================
    # Cleanup tests
    # ==========================================================================

    def test_cleans_empty_rules(self):
        """Clean up empty rule blocks after removal."""
        css = "div { float: left; }"
        result = sanitize_css_text(css)

        # Should not have empty braces
        assert "{}" not in result.replace(" ", "")

    def test_cleans_multiple_semicolons(self):
        """Clean up multiple semicolons."""
        css = "div { color: red;; background: blue; }"
        result = sanitize_css_text(css)

        assert ";;" not in result

    def test_preserves_valid_css(self, css_clean: str):
        """Preserve valid CSS that doesn't need sanitization."""
        result = sanitize_css_text(css_clean)

        assert "color: black" in result
        assert "line-height: 1.4" in result
        # Note: margin is removed by the sanitizer (CSS_PATTERNS_TO_REMOVE includes margin)


class TestCalculateRelativePath:
    """Test calculate_relative_path() function."""

    def test_same_directory(self):
        """Calculate path when files are in same directory."""
        from_path = Path("/book/OEBPS/chapter1.xhtml")
        to_path = Path("/book/OEBPS/style.css")

        result = calculate_relative_path(from_path, to_path)

        assert result == "style.css"

    def test_parent_directory(self):
        """Calculate path when target is in parent directory."""
        from_path = Path("/book/OEBPS/text/chapter1.xhtml")
        to_path = Path("/book/OEBPS/style.css")

        result = calculate_relative_path(from_path, to_path)

        assert result == "../style.css"

    def test_child_directory(self):
        """Calculate path when target is in child directory."""
        from_path = Path("/book/OEBPS/chapter1.xhtml")
        to_path = Path("/book/OEBPS/styles/main.css")

        result = calculate_relative_path(from_path, to_path)

        assert result == "styles/main.css"

    def test_sibling_directory(self):
        """Calculate path when target is in sibling directory."""
        from_path = Path("/book/OEBPS/text/chapter1.xhtml")
        to_path = Path("/book/OEBPS/styles/main.css")

        result = calculate_relative_path(from_path, to_path)

        assert result == "../styles/main.css"

    def test_uses_forward_slashes(self):
        """Verify forward slashes are used (not backslashes)."""
        from_path = Path("/book/OEBPS/text/chapter1.xhtml")
        to_path = Path("/book/OEBPS/styles/main.css")

        result = calculate_relative_path(from_path, to_path)

        assert "\\" not in result


class TestInjectCSSLink:
    """Test inject_css_link() function."""

    def test_successful_injection(self, tmp_path: Path):
        """Successfully inject CSS link into HTML file."""
        html_file = tmp_path / "test.xhtml"
        html_file.write_text("<html><head></head><body></body></html>")
        css_file = tmp_path / "style.css"

        result = inject_css_link(html_file, css_file)

        assert result is True
        content = html_file.read_text()
        assert '<link rel="stylesheet"' in content
        assert "style.css" in content

    def test_injection_before_head_close(self, tmp_path: Path):
        """CSS link is injected before </head>."""
        html_file = tmp_path / "test.xhtml"
        html_file.write_text("<html><head><title>Test</title></head><body></body></html>")
        css_file = tmp_path / "style.css"

        inject_css_link(html_file, css_file)

        content = html_file.read_text()
        head_close_pos = content.lower().find("</head>")
        link_pos = content.find('<link rel="stylesheet"')

        assert link_pos < head_close_pos

    def test_skip_if_already_present(self, tmp_path: Path):
        """Skip injection if CSS already present."""
        html_file = tmp_path / "test.xhtml"
        html_file.write_text(f'<html><head><link href="{X4_CSS_FILENAME}"/></head></html>')
        css_file = tmp_path / X4_CSS_FILENAME

        result = inject_css_link(html_file, css_file)

        assert result is False

    def test_no_head_tag(self, tmp_path: Path):
        """Return False if no </head> tag."""
        html_file = tmp_path / "test.xhtml"
        html_file.write_text("<html><body></body></html>")
        css_file = tmp_path / "style.css"

        result = inject_css_link(html_file, css_file)

        assert result is False

    def test_file_not_found(self, tmp_path: Path):
        """Return False if HTML file doesn't exist."""
        html_file = tmp_path / "nonexistent.xhtml"
        css_file = tmp_path / "style.css"

        result = inject_css_link(html_file, css_file)

        assert result is False

    def test_case_insensitive_head(self, tmp_path: Path):
        """Handle uppercase </HEAD> tag."""
        html_file = tmp_path / "test.xhtml"
        html_file.write_text("<html><HEAD></HEAD><body></body></html>")
        css_file = tmp_path / "style.css"

        result = inject_css_link(html_file, css_file)

        assert result is True


class TestAddCSSToManifest:
    """Test add_css_to_manifest() function."""

    def test_adds_css_to_manifest(self, tmp_path: Path, content_opf: str):
        """Add CSS to OPF manifest."""
        opf_path = tmp_path / "content.opf"
        opf_path.write_text(content_opf)

        add_css_to_manifest(opf_path, "styles/x4.css")

        content = opf_path.read_text()
        assert "x4-sanitizer-css" in content
        assert "styles/x4.css" in content

    def test_skips_if_already_exists(self, tmp_path: Path, content_opf: str):
        """Skip if CSS already in manifest."""
        opf_path = tmp_path / "content.opf"
        opf_path.write_text(content_opf)

        # Add twice
        add_css_to_manifest(opf_path, "x4.css")
        add_css_to_manifest(opf_path, "x4.css")

        content = opf_path.read_text()
        # Should only appear once
        assert content.count("x4-sanitizer-css") == 1

    def test_handles_invalid_opf(self, tmp_path: Path):
        """Handle invalid OPF gracefully."""
        opf_path = tmp_path / "bad.opf"
        opf_path.write_text("not valid xml <<>")

        # Should not raise
        add_css_to_manifest(opf_path, "x4.css")


class TestRemoveFontFromManifest:
    """Test remove_font_from_manifest() function."""

    def test_removes_font_from_manifest(self, tmp_path: Path):
        """Remove font reference from manifest."""
        opf_content = '''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <manifest>
    <item id="font1" href="fonts/test.ttf" media-type="application/x-font-ttf"/>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
</package>'''
        opf_path = tmp_path / "content.opf"
        opf_path.write_text(opf_content)

        remove_font_from_manifest(opf_path, "fonts/test.ttf")

        content = opf_path.read_text()
        assert "test.ttf" not in content
        assert "chapter1.xhtml" in content

    def test_handles_missing_manifest(self, tmp_path: Path):
        """Handle OPF without manifest."""
        opf_content = '''<?xml version="1.0"?><package></package>'''
        opf_path = tmp_path / "content.opf"
        opf_path.write_text(opf_content)

        # Should not raise
        remove_font_from_manifest(opf_path, "font.ttf")


class TestRemoveFonts:
    """Test remove_fonts() function."""

    def test_removes_font_files(self, tmp_path: Path):
        """Remove font files from directory."""
        fonts_dir = tmp_path / "fonts"
        fonts_dir.mkdir()
        (fonts_dir / "test.ttf").write_bytes(b"fake font")
        (fonts_dir / "test.otf").write_bytes(b"fake font")
        (fonts_dir / "test.woff").write_bytes(b"fake font")
        (tmp_path / "chapter.xhtml").write_text("<html></html>")

        count = remove_fonts(tmp_path, None)

        assert count == 3
        assert not (fonts_dir / "test.ttf").exists()
        assert not (fonts_dir / "test.otf").exists()
        assert not (fonts_dir / "test.woff").exists()
        assert (tmp_path / "chapter.xhtml").exists()

    def test_returns_zero_when_no_fonts(self, tmp_path: Path):
        """Return 0 when no fonts found."""
        (tmp_path / "chapter.xhtml").write_text("<html></html>")

        count = remove_fonts(tmp_path, None)

        assert count == 0

    def test_removes_all_font_extensions(self, tmp_path: Path):
        """Remove all font file types."""
        extensions = [".ttf", ".otf", ".woff", ".woff2", ".eot"]
        for ext in extensions:
            (tmp_path / f"font{ext}").write_bytes(b"fake")

        count = remove_fonts(tmp_path, None)

        assert count == 5
        for ext in extensions:
            assert not (tmp_path / f"font{ext}").exists()


class TestProcessImages:
    """Test process_images() function."""

    def test_processes_jpg(self, tmp_path: Path):
        """Process JPG images."""
        img = Image.new("RGB", (800, 600), (255, 0, 0))
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        count = process_images(tmp_path)

        assert count == 1
        # Check image was processed
        with Image.open(img_path) as result:
            assert result.mode == "L"  # Grayscale
            assert result.width <= 480

    def test_processes_png(self, tmp_path: Path):
        """Process PNG images and convert to JPG."""
        img = Image.new("RGB", (800, 600), (0, 255, 0))
        img_path = tmp_path / "test.png"
        img.save(img_path)

        count = process_images(tmp_path)

        assert count == 1
        # PNG should be converted to JPG
        assert (tmp_path / "test.jpg").exists()
        assert not (tmp_path / "test.png").exists()

    def test_resizes_wide_images(self, tmp_path: Path):
        """Resize images wider than max_width."""
        img = Image.new("RGB", (1000, 500), (0, 0, 255))
        img_path = tmp_path / "wide.jpg"
        img.save(img_path)

        process_images(tmp_path, max_width=480)

        with Image.open(img_path) as result:
            assert result.width == 480
            assert result.height == 240  # Proportional resize

    def test_keeps_small_images_size(self, tmp_path: Path):
        """Don't resize images smaller than max_width."""
        img = Image.new("RGB", (200, 100), (128, 128, 128))
        img_path = tmp_path / "small.jpg"
        img.save(img_path)

        process_images(tmp_path, max_width=480)

        with Image.open(img_path) as result:
            # Width should remain same (no upscaling)
            assert result.width == 200

    def test_converts_to_grayscale(self, tmp_path: Path):
        """Convert color images to grayscale."""
        img = Image.new("RGB", (100, 100), (255, 0, 0))
        img_path = tmp_path / "color.jpg"
        img.save(img_path)

        process_images(tmp_path)

        with Image.open(img_path) as result:
            assert result.mode == "L"

    def test_handles_rgba_images(self, tmp_path: Path):
        """Handle RGBA images with transparency."""
        img = Image.new("RGBA", (100, 100), (255, 0, 0, 128))
        img_path = tmp_path / "alpha.png"
        img.save(img_path)

        count = process_images(tmp_path)

        assert count == 1
        jpg_path = tmp_path / "alpha.jpg"
        assert jpg_path.exists()

    def test_custom_quality(self, tmp_path: Path):
        """Process with custom JPEG quality."""
        img = Image.new("RGB", (100, 100), (128, 128, 128))
        img_path = tmp_path / "test.jpg"
        img.save(img_path)

        process_images(tmp_path, quality=50)

        # File should exist after processing
        assert img_path.exists()

    def test_skips_non_image_files(self, tmp_path: Path):
        """Skip non-image files."""
        (tmp_path / "text.txt").write_text("hello")
        (tmp_path / "style.css").write_text("body {}")

        count = process_images(tmp_path)

        assert count == 0

    def test_handles_corrupted_image(self, tmp_path: Path):
        """Handle corrupted image gracefully."""
        bad_img = tmp_path / "bad.jpg"
        bad_img.write_bytes(b"not a real image")

        # Should not raise
        count = process_images(tmp_path)

        assert count == 0


class TestRebuildEpub:
    """Test rebuild_epub() function."""

    def test_rebuilds_epub(self, tmp_path: Path):
        """Rebuild EPUB from directory."""
        epub_dir = tmp_path / "epub"
        epub_dir.mkdir()

        # Create mimetype
        (epub_dir / "mimetype").write_text("application/epub+zip")

        # Create content
        oebps = epub_dir / "OEBPS"
        oebps.mkdir()
        (oebps / "chapter.xhtml").write_text("<html></html>")

        # Create META-INF
        meta = epub_dir / "META-INF"
        meta.mkdir()
        (meta / "container.xml").write_text("<container></container>")

        # Rebuild
        out_path = tmp_path / "output.epub"
        rebuild_epub(epub_dir, out_path)

        assert out_path.exists()

        # Verify structure
        with zipfile.ZipFile(out_path, "r") as z:
            names = z.namelist()
            assert "mimetype" in names
            assert "OEBPS/chapter.xhtml" in names
            assert "META-INF/container.xml" in names

    def test_mimetype_first_and_uncompressed(self, tmp_path: Path):
        """Mimetype is first and uncompressed."""
        epub_dir = tmp_path / "epub"
        epub_dir.mkdir()
        (epub_dir / "mimetype").write_text("application/epub+zip")
        (epub_dir / "content.xhtml").write_text("<html></html>")

        out_path = tmp_path / "output.epub"
        rebuild_epub(epub_dir, out_path)

        with zipfile.ZipFile(out_path, "r") as z:
            # Mimetype should be first
            assert z.namelist()[0] == "mimetype"
            # And uncompressed
            info = z.getinfo("mimetype")
            assert info.compress_type == zipfile.ZIP_STORED


class TestSanitizeEpubFile:
    """Test sanitize_epub_file() full pipeline."""

    def test_sanitizes_epub(self, minimal_epub_path: Path, tmp_path: Path):
        """Sanitize a minimal EPUB file."""
        out_path = tmp_path / "sanitized.epub"

        stats = sanitize_epub_file(minimal_epub_path, out_path)

        assert out_path.exists()
        assert "fonts_removed" in stats
        assert "images_processed" in stats
        assert "css_injected" in stats

    def test_injects_css(self, minimal_epub_path: Path, tmp_path: Path):
        """Verify CSS is injected."""
        out_path = tmp_path / "sanitized.epub"

        stats = sanitize_epub_file(minimal_epub_path, out_path)

        assert stats["css_injected"] > 0

        # Verify CSS file in output
        with zipfile.ZipFile(out_path, "r") as z:
            names = z.namelist()
            assert any(X4_CSS_FILENAME in n for n in names)

    def test_removes_fonts_when_enabled(self, tmp_path: Path):
        """Remove fonts when remove_fonts_flag=True."""
        # Create EPUB with font
        epub_dir = tmp_path / "epub"
        epub_dir.mkdir()
        (epub_dir / "mimetype").write_text("application/epub+zip")

        meta = epub_dir / "META-INF"
        meta.mkdir()
        (meta / "container.xml").write_text(
            '''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        )

        (epub_dir / "content.opf").write_text(
            '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <manifest>
    <item id="ch1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="ch1"/></spine>
</package>'''
        )

        (epub_dir / "chapter.xhtml").write_text("<html><head></head><body></body></html>")
        (epub_dir / "font.ttf").write_bytes(b"fake font")

        # Create input EPUB
        input_epub = tmp_path / "input.epub"
        with zipfile.ZipFile(input_epub, "w") as z:
            for f in epub_dir.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(epub_dir))

        # Sanitize
        out_epub = tmp_path / "output.epub"
        stats = sanitize_epub_file(input_epub, out_epub, remove_fonts_flag=True)

        assert stats["fonts_removed"] == 1

        # Verify font not in output
        with zipfile.ZipFile(out_epub, "r") as z:
            assert not any(".ttf" in n for n in z.namelist())

    def test_keeps_fonts_when_disabled(self, tmp_path: Path):
        """Keep fonts when remove_fonts_flag=False."""
        # Create simple EPUB with font
        epub_dir = tmp_path / "epub"
        epub_dir.mkdir()
        (epub_dir / "mimetype").write_text("application/epub+zip")

        meta = epub_dir / "META-INF"
        meta.mkdir()
        (meta / "container.xml").write_text(
            '''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        )

        (epub_dir / "content.opf").write_text(
            '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <manifest>
    <item id="ch1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="ch1"/></spine>
</package>'''
        )

        (epub_dir / "chapter.xhtml").write_text("<html><head></head><body></body></html>")
        (epub_dir / "font.ttf").write_bytes(b"fake font")

        input_epub = tmp_path / "input.epub"
        with zipfile.ZipFile(input_epub, "w") as z:
            for f in epub_dir.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(epub_dir))

        out_epub = tmp_path / "output.epub"
        stats = sanitize_epub_file(input_epub, out_epub, remove_fonts_flag=False)

        assert stats["fonts_removed"] == 0

    def test_processes_images_when_enabled(self, tmp_path: Path):
        """Process images when downscale_images=True."""
        # Create EPUB with image
        epub_dir = tmp_path / "epub"
        epub_dir.mkdir()
        (epub_dir / "mimetype").write_text("application/epub+zip")

        meta = epub_dir / "META-INF"
        meta.mkdir()
        (meta / "container.xml").write_text(
            '''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        )

        (epub_dir / "content.opf").write_text(
            '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <manifest>
    <item id="ch1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="ch1"/></spine>
</package>'''
        )

        (epub_dir / "chapter.xhtml").write_text("<html><head></head><body></body></html>")

        # Create image
        img = Image.new("RGB", (800, 600), (255, 0, 0))
        img.save(epub_dir / "image.jpg")

        input_epub = tmp_path / "input.epub"
        with zipfile.ZipFile(input_epub, "w") as z:
            for f in epub_dir.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(epub_dir))

        out_epub = tmp_path / "output.epub"
        stats = sanitize_epub_file(input_epub, out_epub, downscale_images=True)

        assert stats["images_processed"] == 1

    def test_skips_images_when_disabled(self, tmp_path: Path):
        """Skip images when downscale_images=False."""
        epub_dir = tmp_path / "epub"
        epub_dir.mkdir()
        (epub_dir / "mimetype").write_text("application/epub+zip")

        meta = epub_dir / "META-INF"
        meta.mkdir()
        (meta / "container.xml").write_text(
            '''<?xml version="1.0"?>
<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        )

        (epub_dir / "content.opf").write_text(
            '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf">
  <manifest>
    <item id="ch1" href="chapter.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine><itemref idref="ch1"/></spine>
</package>'''
        )

        (epub_dir / "chapter.xhtml").write_text("<html><head></head><body></body></html>")

        img = Image.new("RGB", (800, 600), (255, 0, 0))
        img.save(epub_dir / "image.jpg")

        input_epub = tmp_path / "input.epub"
        with zipfile.ZipFile(input_epub, "w") as z:
            for f in epub_dir.rglob("*"):
                if f.is_file():
                    z.write(f, f.relative_to(epub_dir))

        out_epub = tmp_path / "output.epub"
        stats = sanitize_epub_file(input_epub, out_epub, downscale_images=False)

        assert stats["images_processed"] == 0
