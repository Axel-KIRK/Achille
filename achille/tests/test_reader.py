import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from memory.reader import _strip_frontmatter, read_header

def test_strip_frontmatter_with_header():
    text = "---\ndescription: test\nkeywords: a, b\n---\n\nActual content here."
    assert _strip_frontmatter(text) == "Actual content here."

def test_strip_frontmatter_without_header():
    assert _strip_frontmatter("Just plain content.") == "Just plain content."

def test_strip_frontmatter_empty():
    assert _strip_frontmatter("") == ""

def test_read_header_parses_yaml():
    text = "---\ndescription: Identity facts\nkeywords: age, name\nlast_consolidated: 2026-03-22\nlines: 45\n---\n\nContent."
    header = read_header(text=text)
    assert header["description"] == "Identity facts"
    assert header["keywords"] == "age, name"
    assert header["lines"] == 45

def test_read_header_no_frontmatter():
    assert read_header(text="No header here.") == {}
