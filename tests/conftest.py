"""Shared test fixtures for epub-optimizer-xteink tests."""

import zipfile
from pathlib import Path

import pytest
from PIL import Image

# Path to fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures"


# =============================================================================
# Fixture file contents (read from files)
# =============================================================================


@pytest.fixture
def container_xml() -> str:
    """Sample META-INF/container.xml content."""
    return (FIXTURES_DIR / "container.xml").read_text()


@pytest.fixture
def content_opf() -> str:
    """Sample OPF file content."""
    return (FIXTURES_DIR / "content.opf").read_text()


@pytest.fixture
def chapter1_xhtml() -> str:
    """Sample chapter XHTML content."""
    return (FIXTURES_DIR / "chapter1.xhtml").read_text()


@pytest.fixture
def toc_ncx() -> str:
    """Sample NCX TOC content."""
    return (FIXTURES_DIR / "toc.ncx").read_text()


@pytest.fixture
def nav_xhtml() -> str:
    """Sample EPUB3 NAV content."""
    return (FIXTURES_DIR / "nav.xhtml").read_text()


# =============================================================================
# EPUB fixtures
# =============================================================================


@pytest.fixture
def minimal_epub_path(
    tmp_path: Path,
    container_xml: str,
    content_opf: str,
    chapter1_xhtml: str,
    toc_ncx: str,
    nav_xhtml: str,
) -> Path:
    """Create a minimal valid EPUB file."""
    epub_path = tmp_path / "minimal.epub"

    with zipfile.ZipFile(epub_path, "w") as z:
        # mimetype must be first and uncompressed
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # META-INF/container.xml
        z.writestr("META-INF/container.xml", container_xml)

        # OEBPS content
        z.writestr("OEBPS/content.opf", content_opf)
        z.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml)
        z.writestr("OEBPS/toc.ncx", toc_ncx)
        z.writestr("OEBPS/nav.xhtml", nav_xhtml)

    return epub_path


@pytest.fixture
def minimal_epub_zip(minimal_epub_path: Path) -> zipfile.ZipFile:
    """Open minimal EPUB as ZipFile."""
    return zipfile.ZipFile(minimal_epub_path, "r")


@pytest.fixture
def epub_no_container(tmp_path: Path, content_opf: str, chapter1_xhtml: str) -> Path:
    """Create EPUB without META-INF/container.xml (for fallback testing)."""
    epub_path = tmp_path / "no_container.epub"

    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)
        # No container.xml - OPF should be found by fallback search
        z.writestr("OEBPS/content.opf", content_opf)
        z.writestr("OEBPS/chapter1.xhtml", chapter1_xhtml)

    return epub_path


@pytest.fixture
def empty_epub(tmp_path: Path) -> Path:
    """Create empty EPUB (no OPF file)."""
    epub_path = tmp_path / "empty.epub"

    with zipfile.ZipFile(epub_path, "w") as z:
        z.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

    return epub_path


@pytest.fixture
def extracted_epub_dir(
    tmp_path: Path,
    container_xml: str,
    content_opf: str,
    chapter1_xhtml: str,
    toc_ncx: str,
    nav_xhtml: str,
) -> Path:
    """Create an extracted EPUB directory structure."""
    root = tmp_path / "extracted_epub"
    root.mkdir()

    # Create META-INF
    meta_inf = root / "META-INF"
    meta_inf.mkdir()
    (meta_inf / "container.xml").write_text(container_xml)

    # Create OEBPS
    oebps = root / "OEBPS"
    oebps.mkdir()
    (oebps / "content.opf").write_text(content_opf)
    (oebps / "chapter1.xhtml").write_text(chapter1_xhtml)
    (oebps / "toc.ncx").write_text(toc_ncx)
    (oebps / "nav.xhtml").write_text(nav_xhtml)

    return root


# =============================================================================
# Image fixtures
# =============================================================================


@pytest.fixture
def test_image_gray(tmp_path: Path) -> Path:
    """Create a 100x100 grayscale test image."""
    img = Image.new("L", (100, 100), 128)
    path = tmp_path / "test_gray.png"
    img.save(path)
    return path


@pytest.fixture
def test_image_color(tmp_path: Path) -> Path:
    """Create a 100x100 RGB color test image."""
    img = Image.new("RGB", (100, 100), (255, 0, 0))
    path = tmp_path / "test_color.png"
    img.save(path)
    return path


@pytest.fixture
def test_image_480x800(tmp_path: Path) -> Path:
    """Create a display-sized grayscale test image."""
    img = Image.new("L", (480, 800), 200)
    path = tmp_path / "test_480x800.png"
    img.save(path)
    return path


@pytest.fixture
def test_image_gradient(tmp_path: Path) -> Image.Image:
    """Create a gradient image for testing quantization."""
    img = Image.new("L", (256, 1))
    for x in range(256):
        img.putpixel((x, 0), x)
    return img


# =============================================================================
# Font fixtures
# =============================================================================


@pytest.fixture
def mock_font_path(tmp_path: Path) -> Path:
    """Return path to a real font file for testing."""
    # Use the project's Bookerly font if available
    project_font = Path("/mnt/data/tmp/work/dev/personal/epub-optimizer-xteink/fonts/Bookerly.ttf")
    if project_font.exists():
        return project_font

    # Fallback to system font
    system_fonts = [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/TTF/DejaVuSans.ttf"),
        Path("/System/Library/Fonts/Helvetica.ttc"),
    ]
    for font in system_fonts:
        if font.exists():
            return font

    pytest.skip("No font file available for testing")


@pytest.fixture
def font_family(mock_font_path: Path):
    """Create FontFamily with available font."""
    from text_renderer import FontFamily

    return FontFamily(regular=mock_font_path)


# =============================================================================
# HTML parsing fixtures
# =============================================================================


@pytest.fixture
def simple_html() -> str:
    """Simple HTML with one paragraph."""
    return "<p>Hello World</p>"


@pytest.fixture
def formatted_html() -> str:
    """HTML with bold and italic formatting."""
    return "<p>Normal <strong>bold</strong> and <em>italic</em> text.</p>"


@pytest.fixture
def heading_html() -> str:
    """HTML with headings."""
    return "<h1>Title</h1><h2>Subtitle</h2><p>Content</p>"


@pytest.fixture
def list_html() -> str:
    """HTML with list."""
    return "<ul><li>Item 1</li><li>Item 2</li></ul>"


@pytest.fixture
def ignored_tags_html() -> str:
    """HTML with script and style tags to ignore."""
    return "<p>Before</p><script>alert('x')</script><style>.x{}</style><p>After</p>"


# =============================================================================
# CSS fixtures
# =============================================================================


@pytest.fixture
def css_with_fonts() -> str:
    """CSS with @font-face and font-family."""
    return """
@font-face {
    font-family: 'CustomFont';
    src: url('custom.ttf');
}
body {
    font-family: 'CustomFont', serif;
    color: black;
}
"""


@pytest.fixture
def css_with_layout() -> str:
    """CSS with problematic layout properties."""
    return """
.sidebar {
    float: left;
    width: 200px;
}
.modal {
    position: absolute;
    display: flex;
}
.grid {
    display: grid;
}
"""


@pytest.fixture
def css_clean() -> str:
    """Clean CSS that should pass through mostly unchanged."""
    return """
body {
    color: black;
    line-height: 1.4;
}
p {
    margin: 0 0 1em 0;
}
"""
