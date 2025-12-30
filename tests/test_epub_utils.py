"""Tests for epub_utils.py - shared EPUB utilities."""

import zipfile
from pathlib import Path

from epub_utils import EPUB_NAMESPACES, find_opf_path_in_dir, find_opf_path_in_zip, get_opf_dir


class TestEPUBNamespaces:
    """Test EPUB XML namespace definitions."""

    def test_opf_namespace_exists(self):
        """Verify OPF namespace is defined."""
        assert "opf" in EPUB_NAMESPACES
        assert EPUB_NAMESPACES["opf"] == "http://www.idpf.org/2007/opf"

    def test_dc_namespace_exists(self):
        """Verify Dublin Core namespace is defined."""
        assert "dc" in EPUB_NAMESPACES
        assert EPUB_NAMESPACES["dc"] == "http://purl.org/dc/elements/1.1/"

    def test_container_namespace_exists(self):
        """Verify container namespace is defined."""
        assert "container" in EPUB_NAMESPACES
        assert "oasis" in EPUB_NAMESPACES["container"]

    def test_ncx_namespace_exists(self):
        """Verify NCX namespace is defined."""
        assert "ncx" in EPUB_NAMESPACES
        assert "daisy" in EPUB_NAMESPACES["ncx"]

    def test_xhtml_namespace_exists(self):
        """Verify XHTML namespace is defined."""
        assert "xhtml" in EPUB_NAMESPACES
        assert EPUB_NAMESPACES["xhtml"] == "http://www.w3.org/1999/xhtml"

    def test_epub_namespace_exists(self):
        """Verify EPUB namespace is defined."""
        assert "epub" in EPUB_NAMESPACES
        assert "idpf" in EPUB_NAMESPACES["epub"]


class TestFindOPFPathInZip:
    """Test find_opf_path_in_zip() function."""

    def test_find_via_container_xml(self, minimal_epub_zip: zipfile.ZipFile):
        """Find OPF via META-INF/container.xml."""
        opf_path = find_opf_path_in_zip(minimal_epub_zip)

        assert opf_path is not None
        assert opf_path == "OEBPS/content.opf"
        minimal_epub_zip.close()

    def test_fallback_search(self, epub_no_container: Path):
        """Fall back to .opf file search when no container.xml."""
        with zipfile.ZipFile(epub_no_container, "r") as z:
            opf_path = find_opf_path_in_zip(z)

        assert opf_path is not None
        assert opf_path.endswith(".opf")

    def test_not_found_in_empty_epub(self, empty_epub: Path):
        """Return None when no OPF found."""
        with zipfile.ZipFile(empty_epub, "r") as z:
            opf_path = find_opf_path_in_zip(z)

        assert opf_path is None


class TestFindOPFPathInDir:
    """Test find_opf_path_in_dir() function."""

    def test_find_via_container_xml(self, extracted_epub_dir: Path):
        """Find OPF in directory via container.xml."""
        opf_path = find_opf_path_in_dir(extracted_epub_dir)

        assert opf_path is not None
        assert opf_path.name == "content.opf"
        assert opf_path.parent.name == "OEBPS"

    def test_fallback_search_no_container(self, tmp_path: Path, content_opf: str):
        """Fallback search when no container.xml exists."""
        # Create EPUB directory without container.xml
        oebps = tmp_path / "OEBPS"
        oebps.mkdir()
        (oebps / "content.opf").write_text(content_opf)

        opf_path = find_opf_path_in_dir(tmp_path)

        assert opf_path is not None
        assert opf_path.suffix == ".opf"

    def test_not_found_in_empty_dir(self, tmp_path: Path):
        """Return None when no OPF found in directory."""
        opf_path = find_opf_path_in_dir(tmp_path)

        assert opf_path is None


class TestGetOPFDir:
    """Test get_opf_dir() function."""

    def test_returns_parent_directory(self):
        """Test get_opf_dir returns parent of OPF path."""
        opf_path = Path("/book/OEBPS/content.opf")
        opf_dir = get_opf_dir(opf_path)

        assert opf_dir == Path("/book/OEBPS")

    def test_root_level_opf(self):
        """Test with OPF at root level."""
        opf_path = Path("/book/content.opf")
        opf_dir = get_opf_dir(opf_path)

        assert opf_dir == Path("/book")

    def test_deeply_nested_opf(self):
        """Test with deeply nested OPF."""
        opf_path = Path("/a/b/c/d/content.opf")
        opf_dir = get_opf_dir(opf_path)

        assert opf_dir == Path("/a/b/c/d")

    def test_relative_path(self):
        """Test with relative path."""
        opf_path = Path("OEBPS/content.opf")
        opf_dir = get_opf_dir(opf_path)

        assert opf_dir == Path("OEBPS")
