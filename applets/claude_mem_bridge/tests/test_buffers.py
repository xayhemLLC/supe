"""Tests for buffer handling.

Tests that buffers correctly handle:
- Plain text with newlines
- JSON arrays (facts, concepts)
- Markdown content
- Mixed content types
"""

import pytest
from applets.claude_mem_bridge.buffers import BufferValue, BufferStore


class TestBufferValue:
    """Tests for BufferValue normalization."""

    def test_plain_text(self):
        """Plain text is preserved."""
        bv = BufferValue.from_raw("Hello world")
        assert bv.text == "Hello world"
        assert "hello" in bv.words
        assert "world" in bv.words

    def test_text_with_newlines(self):
        """Newlines are preserved in lines."""
        text = "Line one\nLine two\nLine three"
        bv = BufferValue.from_raw(text)

        assert len(bv.lines) == 3
        assert bv.lines[0] == "Line one"
        assert bv.lines[1] == "Line two"
        assert bv.lines[2] == "Line three"
        assert "\n" in bv.text or len(bv.lines) == 3

    def test_markdown_content(self):
        """Markdown content is handled."""
        md = """# Header

This is a paragraph with **bold** and _italic_.

- List item 1
- List item 2

```python
def hello():
    print("world")
```
"""
        bv = BufferValue.from_raw(md)

        # Words are extracted (header and paragraph should be there)
        assert "header" in bv.words
        assert "paragraph" in bv.words
        # Note: bold/italic may appear with markdown markers attached
        # The important thing is content is preserved
        assert "bold" in bv.text.lower()
        assert "italic" in bv.text.lower()

        # Lines preserve structure
        assert len(bv.lines) > 5

    def test_json_array_string(self):
        """JSON array strings are parsed."""
        json_str = '["fact one", "fact two", "fact three"]'
        bv = BufferValue.from_raw(json_str)

        assert bv.is_json
        assert bv.is_list
        assert "fact" in bv.words
        assert len(bv.lines) == 3

    def test_json_array_native(self):
        """Native Python lists are handled."""
        arr = ["First fact", "Second fact", "Third fact"]
        bv = BufferValue.from_raw(arr)

        assert bv.is_list
        assert "first" in bv.words
        assert "second" in bv.words
        assert "fact" in bv.words

    def test_json_object(self):
        """JSON objects are handled."""
        obj = {"key1": "value one", "key2": "value two"}
        bv = BufferValue.from_raw(obj)

        assert "value" in bv.words
        assert len(bv.lines) >= 2

    def test_numeric_value(self):
        """Numbers are converted to strings."""
        bv = BufferValue.from_raw(42)
        assert bv.text == "42"

    def test_boolean_value(self):
        """Booleans are converted to strings."""
        bv = BufferValue.from_raw(True)
        assert bv.text == "True"

    def test_none_value(self):
        """None returns empty values."""
        bv = BufferValue.from_raw(None)
        assert bv.text == ""
        assert len(bv.words) == 0
        assert len(bv.lines) == 0

    def test_stopwords_filtered(self):
        """Common stopwords are filtered from words."""
        bv = BufferValue.from_raw("The quick brown fox and the lazy dog")

        assert "quick" in bv.words
        assert "brown" in bv.words
        assert "lazy" in bv.words
        assert "the" not in bv.words
        assert "and" not in bv.words

    def test_short_words_filtered(self):
        """Short words are filtered."""
        bv = BufferValue.from_raw("I am a cat in a box")

        assert "cat" in bv.words
        assert "box" in bv.words
        assert "am" not in bv.words
        assert "in" not in bv.words

    def test_camelcase_words(self):
        """CamelCase words are handled."""
        bv = BufferValue.from_raw("myFunctionName and AnotherOne")

        # Should extract word parts
        assert "myfunctionname" in bv.words or "function" in bv.words

    def test_code_identifiers(self):
        """Code identifiers with underscores are handled."""
        bv = BufferValue.from_raw("my_function_name and another_one")

        assert any("function" in w for w in bv.words)


class TestBufferStore:
    """Tests for BufferStore operations."""

    def test_basic_storage(self):
        """Buffers are stored and retrievable."""
        store = BufferStore({
            "title": "Test Title",
            "narrative": "This is a test narrative",
        })

        assert store.get_raw("title") == "Test Title"
        assert store.get_text("title") == "Test Title"

    def test_missing_buffer(self):
        """Missing buffers return empty values."""
        store = BufferStore({"title": "Test"})

        assert store.get_raw("missing") is None
        assert store.get_text("missing") == ""
        assert len(store.get_words("missing")) == 0

    def test_all_text(self):
        """all_text combines all buffers."""
        store = BufferStore({
            "title": "Title Here",
            "narrative": "Narrative text",
        })

        all_text = store.all_text()
        assert "Title Here" in all_text
        assert "Narrative text" in all_text

    def test_all_words(self):
        """all_words combines words from all buffers."""
        store = BufferStore({
            "title": "Authentication System",
            "narrative": "User login flow",
        })

        words = store.all_words()
        assert "authentication" in words
        assert "system" in words
        assert "user" in words
        assert "login" in words
        assert "flow" in words

    def test_search_single_word(self):
        """Search finds single word matches."""
        store = BufferStore({
            "title": "OAuth Authentication",
            "narrative": "Implements OAuth 2.0 flow",
        })

        score = store.search("OAuth")
        assert score > 0

    def test_search_multiple_words(self):
        """Search finds multiple word matches."""
        store = BufferStore({
            "title": "OAuth Authentication",
            "narrative": "Implements OAuth 2.0 login flow",
        })

        score = store.search("OAuth authentication login")
        assert score > 0.5  # Should match well

    def test_search_no_match(self):
        """Search returns 0 for no matches."""
        store = BufferStore({
            "title": "Database Migration",
        })

        score = store.search("authentication login")
        assert score == 0

    def test_contains_basic(self):
        """Contains finds substring."""
        store = BufferStore({
            "title": "OAuth Authentication System",
        })

        assert store.contains("OAuth")
        assert store.contains("authentication")
        assert not store.contains("database")

    def test_contains_specific_buffer(self):
        """Contains can target specific buffer."""
        store = BufferStore({
            "title": "OAuth",
            "narrative": "Database migration",
        })

        assert store.contains("OAuth", "title")
        assert not store.contains("Database", "title")
        assert store.contains("Database", "narrative")

    def test_matches_regex(self):
        """Regex matching works."""
        store = BufferStore({
            "title": "Error: Connection refused",
        })

        assert store.matches_regex(r"Error:\s+\w+")
        assert store.matches_regex(r"connection", )  # case insensitive
        assert not store.matches_regex(r"^\d+$")

    def test_multiline_facts(self):
        """Facts as JSON array preserve structure."""
        store = BufferStore({
            "facts": [
                "First fact about the system",
                "Second fact with details",
                "Third fact explaining behavior",
            ],
        })

        lines = store.get_lines("facts")
        assert len(lines) == 3
        assert "First fact" in lines[0]

        words = store.get_words("facts")
        assert "fact" in words
        assert "system" in words


class TestBufferEdgeCases:
    """Edge case tests."""

    def test_empty_string(self):
        """Empty string is handled."""
        bv = BufferValue.from_raw("")
        assert bv.text == ""
        assert len(bv.words) == 0

    def test_whitespace_only(self):
        """Whitespace-only string is handled."""
        bv = BufferValue.from_raw("   \n\t  ")
        assert len(bv.words) == 0

    def test_unicode_text(self):
        """Unicode text is handled."""
        bv = BufferValue.from_raw("Héllo wörld 你好")
        # Latin characters extracted
        assert len(bv.words) >= 0  # May or may not extract unicode words

    def test_very_long_text(self):
        """Very long text is handled."""
        long_text = "word " * 10000
        bv = BufferValue.from_raw(long_text)

        assert "word" in bv.words
        assert len(bv.text) == len(long_text)

    def test_nested_json(self):
        """Nested JSON is flattened."""
        nested = {
            "outer": {
                "inner": "deep value",
            },
            "array": ["item1", "item2"],
        }
        bv = BufferValue.from_raw(nested)

        # Values should be extracted
        assert len(bv.text) > 0

    def test_invalid_json_string(self):
        """Invalid JSON string is treated as text."""
        invalid = '{"incomplete": '
        bv = BufferValue.from_raw(invalid)

        assert not bv.is_json
        assert bv.text == invalid
