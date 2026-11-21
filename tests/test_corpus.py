from cpu_rag_lab.corpus import load_tiny, parse_markdown, queries_from_headings

MD = """# Title

Intro words here.

## Install the tool

```bash
pip install secret-code-words
```

You install it with one command and then check the version number printed out.

## Recap

short
"""


def test_parse_drops_code_and_heading_line():
    """Broken case: code blocks or heading text leaking into the section body."""
    doc = parse_markdown("d.md", MD)
    install = [s for s in doc.sections if s.heading == "Install the tool"][0]
    assert "secret" not in install.text
    assert "Install the tool" not in install.text
    assert install.unit_id == "d.md#1"


def test_queries_skip_generic_and_short_sections():
    doc = parse_markdown("d.md", MD + "\n" + "word " * 40)
    qs = queries_from_headings([doc])
    texts = [q.text for q in qs]
    assert "Recap" not in texts
    assert all(len(q.relevant) == 1 for q in qs)


def test_tiny_corpus_has_queries_with_answers():
    c = load_tiny()
    assert len(c.queries) == 8
    units = {s.unit_id for d in c.docs for s in d.sections}
    assert all(q.relevant <= units for q in c.queries)
