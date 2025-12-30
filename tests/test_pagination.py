"""Tests for pagination.py - page layout and text flow."""

from unittest.mock import MagicMock

import pytest

from epub_parser import TextBlock, TextStyle, TOCEntry
from pagination import ChapterMapping, PageContent, PaginationResult, Paginator, flatten_toc


class TestPageContent:
    """Test PageContent dataclass."""

    def test_default_values(self):
        """Test default values."""
        page = PageContent(blocks=[])

        assert page.blocks == []
        assert page.page_number == 0
        assert page.is_chapter_start is False
        assert page.chapter_title is None

    def test_with_values(self):
        """Test with custom values."""
        blocks = [TextBlock(text="Hello", style=TextStyle())]
        page = PageContent(
            blocks=blocks,
            page_number=5,
            is_chapter_start=True,
            chapter_title="Chapter 1",
        )

        assert len(page.blocks) == 1
        assert page.page_number == 5
        assert page.is_chapter_start is True
        assert page.chapter_title == "Chapter 1"


class TestChapterMapping:
    """Test ChapterMapping dataclass."""

    def test_creation(self):
        """Test ChapterMapping creation."""
        mapping = ChapterMapping(title="Chapter 1", start_page=1, end_page=10)

        assert mapping.title == "Chapter 1"
        assert mapping.start_page == 1
        assert mapping.end_page == 10

    def test_default_end_page(self):
        """Test default end_page is 0."""
        mapping = ChapterMapping(title="Test", start_page=1)

        assert mapping.end_page == 0


class TestPaginationResult:
    """Test PaginationResult dataclass."""

    def test_creation(self):
        """Test PaginationResult creation."""
        pages = [PageContent(blocks=[])]
        chapters = [ChapterMapping("Ch1", 1, 1)]

        result = PaginationResult(pages=pages, chapters=chapters, total_pages=1)

        assert len(result.pages) == 1
        assert len(result.chapters) == 1
        assert result.total_pages == 1


class TestFlattenTOC:
    """Test flatten_toc() function."""

    def test_empty_toc(self):
        """Empty TOC returns empty list."""
        result = flatten_toc([])
        assert result == []

    def test_flat_toc(self):
        """Flat TOC unchanged."""
        entries = [
            TOCEntry("Ch1", "ch1.html"),
            TOCEntry("Ch2", "ch2.html"),
        ]

        result = flatten_toc(entries)

        assert len(result) == 2
        assert result[0].title == "Ch1"
        assert result[1].title == "Ch2"

    def test_nested_toc(self):
        """Nested TOC flattened."""
        child = TOCEntry("Section 1.1", "s1.1.html", level=1)
        parent = TOCEntry("Chapter 1", "ch1.html", level=0, children=[child])

        result = flatten_toc([parent])

        assert len(result) == 2
        assert result[0].title == "Chapter 1"
        assert result[1].title == "Section 1.1"

    def test_deeply_nested(self):
        """Deeply nested TOC flattened correctly."""
        grandchild = TOCEntry("1.1.1", "1.1.1.html", level=2)
        child = TOCEntry("1.1", "1.1.html", level=1, children=[grandchild])
        parent = TOCEntry("1", "1.html", level=0, children=[child])

        result = flatten_toc([parent])

        assert len(result) == 3
        assert result[0].title == "1"
        assert result[1].title == "1.1"
        assert result[2].title == "1.1.1"

    def test_preserves_order(self):
        """Order is preserved (parent before children)."""
        child1 = TOCEntry("1.1", "1.1.html", level=1)
        child2 = TOCEntry("1.2", "1.2.html", level=1)
        parent = TOCEntry("1", "1.html", level=0, children=[child1, child2])

        result = flatten_toc([parent])

        assert result[0].title == "1"
        assert result[1].title == "1.1"
        assert result[2].title == "1.2"


class TestPaginatorIsChapterHeading:
    """Test Paginator._is_chapter_heading() method."""

    @pytest.fixture
    def mock_renderer(self):
        """Create mock TextRenderer."""
        renderer = MagicMock()
        renderer.estimate_block_height = MagicMock(return_value=50)
        return renderer

    def test_h1_is_chapter(self, mock_renderer):
        """H1 is chapter heading."""
        paginator = Paginator(mock_renderer)
        block = TextBlock(
            text="Chapter 1",
            style=TextStyle(is_heading=True, heading_level=1),
            block_type="heading1",
        )

        assert paginator._is_chapter_heading(block) is True

    def test_h2_is_chapter(self, mock_renderer):
        """H2 is chapter heading."""
        paginator = Paginator(mock_renderer)
        block = TextBlock(
            text="Section",
            style=TextStyle(is_heading=True, heading_level=2),
            block_type="heading2",
        )

        assert paginator._is_chapter_heading(block) is True

    def test_h3_not_chapter(self, mock_renderer):
        """H3 is NOT chapter heading."""
        paginator = Paginator(mock_renderer)
        block = TextBlock(
            text="Subsection",
            style=TextStyle(is_heading=True, heading_level=3),
            block_type="heading3",
        )

        assert paginator._is_chapter_heading(block) is False

    def test_h4_not_chapter(self, mock_renderer):
        """H4 is NOT chapter heading."""
        paginator = Paginator(mock_renderer)
        block = TextBlock(
            text="Minor",
            style=TextStyle(is_heading=True, heading_level=4),
            block_type="heading4",
        )

        assert paginator._is_chapter_heading(block) is False

    def test_paragraph_not_chapter(self, mock_renderer):
        """Paragraph is NOT chapter heading."""
        paginator = Paginator(mock_renderer)
        block = TextBlock(text="Text", style=TextStyle(), block_type="paragraph")

        assert paginator._is_chapter_heading(block) is False

    def test_list_item_not_chapter(self, mock_renderer):
        """List item is NOT chapter heading."""
        paginator = Paginator(mock_renderer)
        block = TextBlock(text="Item", style=TextStyle(), block_type="list_item")

        assert paginator._is_chapter_heading(block) is False


class TestPaginatorPaginate:
    """Test Paginator.paginate() method."""

    @pytest.fixture
    def mock_renderer(self):
        """Create mock TextRenderer with small block heights."""
        renderer = MagicMock()
        # Return small height so multiple blocks fit on a page
        renderer.estimate_block_height = MagicMock(return_value=50)
        return renderer

    def test_empty_content(self, mock_renderer):
        """Empty content returns empty result."""
        paginator = Paginator(mock_renderer)

        result = paginator.paginate(iter([]))

        assert result.total_pages == 0
        assert result.pages == []
        assert result.chapters == []

    def test_single_block(self, mock_renderer):
        """Single block creates one page."""
        paginator = Paginator(mock_renderer)
        blocks = [TextBlock(text="Hello", style=TextStyle(), block_type="paragraph")]

        result = paginator.paginate(iter(blocks))

        assert result.total_pages == 1
        assert len(result.pages) == 1
        assert len(result.pages[0].blocks) == 1

    def test_multiple_blocks_fit_on_page(self, mock_renderer):
        """Multiple small blocks fit on one page."""
        paginator = Paginator(mock_renderer)
        blocks = [
            TextBlock(text="First", style=TextStyle(), block_type="paragraph"),
            TextBlock(text="Second", style=TextStyle(), block_type="paragraph"),
            TextBlock(text="Third", style=TextStyle(), block_type="paragraph"),
        ]

        result = paginator.paginate(iter(blocks))

        # Should fit on one page since mock returns 50px per block
        assert result.total_pages == 1
        assert len(result.pages[0].blocks) == 3

    def test_page_break_on_overflow(self, mock_renderer):
        """New page created when content overflows."""
        # Return large height to force page breaks
        mock_renderer.estimate_block_height = MagicMock(return_value=400)
        paginator = Paginator(mock_renderer)

        blocks = [
            TextBlock(text="First", style=TextStyle(), block_type="paragraph"),
            TextBlock(text="Second", style=TextStyle(), block_type="paragraph"),
            TextBlock(text="Third", style=TextStyle(), block_type="paragraph"),
        ]

        result = paginator.paginate(iter(blocks))

        # Should need multiple pages
        assert result.total_pages > 1

    def test_chapter_heading_starts_new_page(self, mock_renderer):
        """Chapter heading starts a new page."""
        paginator = Paginator(mock_renderer)

        blocks = [
            TextBlock(text="Intro", style=TextStyle(), block_type="paragraph"),
            TextBlock(
                text="Chapter 1",
                style=TextStyle(is_heading=True, heading_level=1),
                block_type="heading1",
            ),
            TextBlock(text="Content", style=TextStyle(), block_type="paragraph"),
        ]

        result = paginator.paginate(iter(blocks))

        # Chapter should start on new page
        assert result.total_pages >= 2

    def test_chapter_tracking(self, mock_renderer):
        """Chapter mappings are tracked correctly."""
        paginator = Paginator(mock_renderer)

        blocks = [
            TextBlock(
                text="Chapter 1",
                style=TextStyle(is_heading=True, heading_level=1),
                block_type="heading1",
            ),
            TextBlock(text="Content 1", style=TextStyle(), block_type="paragraph"),
            TextBlock(
                text="Chapter 2",
                style=TextStyle(is_heading=True, heading_level=1),
                block_type="heading1",
            ),
            TextBlock(text="Content 2", style=TextStyle(), block_type="paragraph"),
        ]

        result = paginator.paginate(iter(blocks))

        # Chapter tracking: first chapter only recorded when second starts,
        # plus final chapter is always recorded at end
        assert len(result.chapters) >= 1
        # Last chapter should be Chapter 2
        assert result.chapters[-1].title == "Chapter 2"

    def test_page_numbering(self, mock_renderer):
        """Pages are numbered correctly."""
        mock_renderer.estimate_block_height = MagicMock(return_value=400)
        paginator = Paginator(mock_renderer)

        blocks = [TextBlock(text=f"Block {i}", style=TextStyle(), block_type="paragraph") for i in range(5)]

        result = paginator.paginate(iter(blocks))

        # Verify page numbers are sequential
        for i, page in enumerate(result.pages, start=1):
            assert page.page_number == i


class TestPaginatorPaginateWithImages:
    """Test Paginator.paginate_with_images() method."""

    @pytest.fixture
    def mock_renderer(self):
        """Create mock TextRenderer."""
        renderer = MagicMock()
        renderer.estimate_block_height = MagicMock(return_value=50)
        return renderer

    def test_same_as_paginate(self, mock_renderer):
        """paginate_with_images currently same as paginate."""
        paginator = Paginator(mock_renderer)
        blocks = [TextBlock(text="Hello", style=TextStyle(), block_type="paragraph")]

        result = paginator.paginate_with_images(iter(blocks))

        assert result.total_pages == 1
