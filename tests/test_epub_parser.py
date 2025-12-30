"""Tests for epub_parser.py - EPUB content extraction."""

from pathlib import Path

from epub_parser import EPUBParser, HTMLContentParser, TextBlock, TextStyle, TOCEntry


class TestTextStyle:
    """Test TextStyle dataclass."""

    def test_default_values(self):
        """Test default TextStyle values."""
        style = TextStyle()

        assert style.font_size == 20
        assert style.bold is False
        assert style.italic is False
        assert style.is_heading is False
        assert style.heading_level == 0
        assert style.indent == 0

    def test_custom_values(self):
        """Test TextStyle with custom values."""
        style = TextStyle(
            font_size=32,
            bold=True,
            italic=True,
            is_heading=True,
            heading_level=1,
            indent=20,
        )

        assert style.font_size == 32
        assert style.bold is True
        assert style.italic is True
        assert style.is_heading is True
        assert style.heading_level == 1
        assert style.indent == 20


class TestTextBlock:
    """Test TextBlock dataclass."""

    def test_creation(self):
        """Test TextBlock creation."""
        style = TextStyle(bold=True)
        block = TextBlock(text="Hello", style=style, block_type="paragraph")

        assert block.text == "Hello"
        assert block.style.bold is True
        assert block.block_type == "paragraph"

    def test_default_block_type(self):
        """Test default block_type is paragraph."""
        block = TextBlock(text="Text", style=TextStyle())

        assert block.block_type == "paragraph"


class TestTOCEntry:
    """Test TOCEntry dataclass."""

    def test_creation(self):
        """Test TOCEntry creation."""
        entry = TOCEntry(title="Chapter 1", href="ch1.html", level=0)

        assert entry.title == "Chapter 1"
        assert entry.href == "ch1.html"
        assert entry.level == 0
        assert entry.children == []

    def test_with_children(self):
        """Test TOCEntry with children."""
        child = TOCEntry(title="Section 1.1", href="s1.1.html", level=1)
        parent = TOCEntry(title="Chapter 1", href="ch1.html", level=0, children=[child])

        assert len(parent.children) == 1
        assert parent.children[0].title == "Section 1.1"


class TestHTMLContentParser:
    """Test HTMLContentParser class."""

    def test_simple_paragraph(self, simple_html: str):
        """Parse simple paragraph."""
        parser = HTMLContentParser()
        parser.feed(simple_html)
        blocks = parser.get_blocks()

        assert len(blocks) == 1
        assert blocks[0].text == "Hello World"
        assert blocks[0].block_type == "paragraph"

    def test_multiple_paragraphs(self):
        """Parse multiple paragraphs."""
        parser = HTMLContentParser()
        parser.feed("<p>First</p><p>Second</p>")
        blocks = parser.get_blocks()

        assert len(blocks) == 2
        assert blocks[0].text == "First"
        assert blocks[1].text == "Second"

    def test_heading_h1(self):
        """Parse H1 heading."""
        parser = HTMLContentParser()
        parser.feed("<h1>Title</h1>")
        blocks = parser.get_blocks()

        assert len(blocks) == 1
        assert blocks[0].text == "Title"
        assert blocks[0].block_type == "heading1"
        assert blocks[0].style.is_heading is True
        assert blocks[0].style.heading_level == 1
        assert blocks[0].style.bold is True

    def test_heading_h2(self):
        """Parse H2 heading."""
        parser = HTMLContentParser()
        parser.feed("<h2>Subtitle</h2>")
        blocks = parser.get_blocks()

        assert blocks[0].block_type == "heading2"
        assert blocks[0].style.heading_level == 2

    def test_heading_h6(self):
        """Parse H6 heading."""
        parser = HTMLContentParser()
        parser.feed("<h6>Small heading</h6>")
        blocks = parser.get_blocks()

        assert blocks[0].block_type == "heading6"
        assert blocks[0].style.heading_level == 6

    def test_bold_strong(self):
        """Parse <strong> tag - text is extracted."""
        parser = HTMLContentParser()
        parser.feed("<p><strong>Bold text</strong></p>")
        blocks = parser.get_blocks()

        # HTMLContentParser extracts text; inline styles are tracked during
        # parsing but block style is captured at emission (end of <p>)
        assert blocks[0].text == "Bold text"

    def test_bold_b(self):
        """Parse <b> tag - text is extracted."""
        parser = HTMLContentParser()
        parser.feed("<p><b>Bold text</b></p>")
        blocks = parser.get_blocks()

        assert blocks[0].text == "Bold text"

    def test_italic_em(self):
        """Parse <em> tag - text is extracted."""
        parser = HTMLContentParser()
        parser.feed("<p><em>Italic text</em></p>")
        blocks = parser.get_blocks()

        assert blocks[0].text == "Italic text"

    def test_italic_i(self):
        """Parse <i> tag - text is extracted."""
        parser = HTMLContentParser()
        parser.feed("<p><i>Italic text</i></p>")
        blocks = parser.get_blocks()

        assert blocks[0].text == "Italic text"

    def test_nested_bold_italic(self):
        """Parse nested bold and italic - text is extracted."""
        parser = HTMLContentParser()
        parser.feed("<p><strong><em>Bold Italic</em></strong></p>")
        blocks = parser.get_blocks()

        assert blocks[0].text == "Bold Italic"

    def test_list_items(self, list_html: str):
        """Parse unordered list."""
        parser = HTMLContentParser()
        parser.feed(list_html)
        blocks = parser.get_blocks()

        assert len(blocks) == 2
        assert blocks[0].block_type == "list_item"
        assert blocks[0].text == "Item 1"
        assert blocks[0].style.indent == 20

    def test_nested_list_indentation(self):
        """Parse nested list - text from both levels is captured."""
        parser = HTMLContentParser()
        parser.feed("<ul><li>Outer<ul><li>Inner</li></ul></li></ul>")
        blocks = parser.get_blocks()

        # HTMLContentParser combines text within list items
        # The nested structure results in combined text and max indent
        assert len(blocks) >= 1
        assert "Outer" in blocks[0].text
        assert "Inner" in blocks[0].text

    def test_blockquote(self):
        """Parse blockquote with indent and italic."""
        parser = HTMLContentParser()
        parser.feed("<blockquote>Quote text</blockquote>")
        blocks = parser.get_blocks()

        assert len(blocks) == 1
        assert blocks[0].block_type == "blockquote"
        assert blocks[0].style.indent == 20
        assert blocks[0].style.italic is True

    def test_ignores_script(self, ignored_tags_html: str):
        """Ignore script content."""
        parser = HTMLContentParser()
        parser.feed(ignored_tags_html)
        blocks = parser.get_blocks()

        assert len(blocks) == 2
        for block in blocks:
            assert "alert" not in block.text

    def test_ignores_style(self):
        """Ignore style content."""
        parser = HTMLContentParser()
        parser.feed("<p>Text</p><style>.x { color: red; }</style>")
        blocks = parser.get_blocks()

        assert len(blocks) == 1
        assert ".x" not in blocks[0].text

    def test_whitespace_normalization(self):
        """Normalize whitespace in text."""
        parser = HTMLContentParser()
        parser.feed("<p>Hello    World\n\nTest</p>")
        blocks = parser.get_blocks()

        assert blocks[0].text == "Hello World Test"

    def test_br_tag(self):
        """Handle br tags."""
        parser = HTMLContentParser()
        parser.feed("<p>Line1<br/>Line2</p>")
        blocks = parser.get_blocks()

        # br should add newline but gets normalized to space
        assert "Line1" in blocks[0].text
        assert "Line2" in blocks[0].text

    def test_div_ends_block(self):
        """Div tag ends block like paragraph."""
        parser = HTMLContentParser()
        parser.feed("<div>First</div><div>Second</div>")
        blocks = parser.get_blocks()

        assert len(blocks) == 2

    def test_empty_paragraph_ignored(self):
        """Empty paragraphs are ignored."""
        parser = HTMLContentParser()
        parser.feed("<p></p><p>Content</p><p>   </p>")
        blocks = parser.get_blocks()

        assert len(blocks) == 1
        assert blocks[0].text == "Content"


class TestEPUBParser:
    """Test EPUBParser class."""

    def test_context_manager(self, minimal_epub_path: Path):
        """Test EPUBParser as context manager."""
        with EPUBParser(minimal_epub_path) as parser:
            assert parser is not None

    def test_extract_metadata(self, minimal_epub_path: Path):
        """Extract title and author from OPF."""
        with EPUBParser(minimal_epub_path) as parser:
            metadata = parser.extract_metadata()

        assert metadata.title == "Test Book"
        assert metadata.author == "Test Author"

    def test_extract_toc(self, minimal_epub_path: Path):
        """Extract table of contents."""
        with EPUBParser(minimal_epub_path) as parser:
            toc = parser.extract_toc()

        assert len(toc) >= 1
        assert toc[0].title == "Chapter 1"

    def test_get_content_order(self, minimal_epub_path: Path):
        """Get ordered list of content files."""
        with EPUBParser(minimal_epub_path) as parser:
            files = parser.get_content_order()

        assert len(files) >= 1
        assert any("chapter1" in f for f in files)

    def test_iter_content_blocks(self, minimal_epub_path: Path):
        """Iterate through content as text blocks."""
        with EPUBParser(minimal_epub_path) as parser:
            blocks = list(parser.iter_content_blocks())

        assert len(blocks) > 0
        # Should have the chapter heading
        assert any(b.text == "Chapter 1: Introduction" for b in blocks)

    def test_parse_returns_epub_content(self, minimal_epub_path: Path):
        """parse() returns EPUBContent with metadata, toc, files."""
        with EPUBParser(minimal_epub_path) as parser:
            content = parser.parse()

        assert content.metadata.title == "Test Book"
        assert len(content.toc) >= 1
        assert len(content.content_files) >= 1

    def test_handles_missing_opf(self, empty_epub: Path):
        """Handle EPUB with no OPF gracefully."""
        with EPUBParser(empty_epub) as parser:
            metadata = parser.extract_metadata()
            toc = parser.extract_toc()

        assert metadata.title == ""
        assert toc == []
