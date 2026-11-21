import pytest

from cpu_rag_lab.chunkers import chunk_corpus, fixed, heading, sentence, split_sentences
from cpu_rag_lab.corpus import Doc, Section


def make_doc():
    a = " ".join(f"Alpha{i} sentence end." for i in range(10))  # 30 words
    b = " ".join(f"Beta{i} words go here." for i in range(10))  # 40 words
    return Doc("d", [Section("d#0", "A", a), Section("d#1", "B", b)])


def test_fixed_sizes_and_overlap():
    doc = make_doc()
    no = fixed(doc, 20, 0)
    assert [len(c.text.split()) for c in no] == [20, 20, 20, 10]
    ov = fixed(doc, 20, 0.2)  # step 16
    assert ov[1].text.split()[0] == doc.sections[0].text.split()[16]
    words = [w for c in no for w in c.text.split()]
    assert len(words) == 70


def test_fixed_chunk_tracks_both_sections_when_it_crosses():
    """Broken case: a chunk that spans two sections reporting only the first."""
    c = fixed(make_doc(), 20, 0)[1]  # words 20..39 cross the border at 30
    assert c.units == ("d#0", "d#1")


def test_sentence_chunks_keep_whole_sentences():
    for c in sentence(make_doc(), 10, 0):
        assert c.text.endswith(".")
        assert len(c.text.split()) <= 10


def test_sentence_overlap_repeats_last_sentence():
    chunks = sentence(make_doc(), 12, 0.34)  # budget 4 words, one 3- or 4-word sentence
    first_last = split_sentences(chunks[0].text)[-1]
    assert chunks[1].text.startswith(first_last)


def test_heading_chunks_never_cross_sections():
    for c in heading(make_doc(), 100, 0):
        assert len(c.units) == 1
    assert len(heading(make_doc(), 100, 0)) == 2


def test_long_sentence_is_cut_to_size():
    doc = Doc("x", [Section("x#0", "", " ".join(["w"] * 50) + ".")])
    assert all(len(c.text.split()) <= 16 for c in sentence(doc, 16, 0))


@pytest.mark.parametrize("name", ["fixed", "sentence", "heading"])
def test_every_word_is_covered(name):
    doc = make_doc()
    got = {w for c in chunk_corpus([doc], name, 16, 0.2) for w in c.text.split()}
    assert got == {w for s in doc.sections for w in s.text.split()}
