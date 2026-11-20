"""Three chunkers. Size counts words split on whitespace, not model tokens.

Each chunk keeps the set of section ids its words came from, so a hit on a chunk can
be mapped back to the units that the queries are judged on.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .corpus import Doc

_SENT = re.compile(r"(?<=[.!?])\s+(?=[A-Z0-9\"'(])")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    units: tuple[str, ...]


def _tagged_words(doc: Doc) -> list[tuple[str, str]]:
    return [(w, s.unit_id) for s in doc.sections for w in s.text.split()]


def _make(doc_id: str, n: int, words: list[tuple[str, str]]) -> Chunk:
    units = tuple(dict.fromkeys(u for _, u in words))
    return Chunk(f"{doc_id}::{n}", " ".join(w for w, _ in words), units)


def fixed(doc: Doc, size: int, overlap: float) -> list[Chunk]:
    """Windows of `size` words. The next window starts `size * (1 - overlap)` words later."""
    words = _tagged_words(doc)
    step = max(1, int(round(size * (1 - overlap))))
    out, start = [], 0
    while start < len(words):
        out.append(_make(doc.doc_id, len(out), words[start : start + size]))
        if start + size >= len(words):
            break
        start += step
    return out


def split_sentences(text: str) -> list[str]:
    return [s for s in _SENT.split(text) if s.strip()]


def _pack(doc_id: str, sents: list[list[tuple[str, str]]], size: int, overlap: float, n0: int):
    """Pack whole sentences into chunks of at most `size` words.

    A sentence longer than `size` is cut into `size`-word pieces. With overlap, the next
    chunk starts with the last sentences of the previous one, up to `size * overlap` words.
    """
    pieces = []
    for s in sents:
        for i in range(0, len(s), size):
            pieces.append(s[i : i + size])
    budget = int(size * overlap)
    out, cur = [], []
    for p in pieces:
        if cur and sum(len(x) for x in cur) + len(p) > size:
            out.append(_make(doc_id, n0 + len(out), [w for x in cur for w in x]))
            carry, total = [], 0
            for x in reversed(cur):
                if total + len(x) > budget or total + len(x) + len(p) > size:
                    break
                carry.insert(0, x)
                total += len(x)
            cur = carry
        cur.append(p)
    if cur:
        out.append(_make(doc_id, n0 + len(out), [w for x in cur for w in x]))
    return out


def _sentences(section) -> list[list[tuple[str, str]]]:
    return [[(w, section.unit_id) for w in s.split()] for s in split_sentences(section.text)]


def sentence(doc: Doc, size: int, overlap: float) -> list[Chunk]:
    """Whole sentences packed up to `size` words. Chunks can cross section borders."""
    sents = [s for sec in doc.sections for s in _sentences(sec)]
    return _pack(doc.doc_id, sents, size, overlap, 0)


def heading(doc: Doc, size: int, overlap: float) -> list[Chunk]:
    """One chunk per section. A section longer than `size` is split by sentences.

    Chunks never cross a section border.
    """
    out: list[Chunk] = []
    for sec in doc.sections:
        out.extend(_pack(doc.doc_id, _sentences(sec), size, overlap, len(out)))
    return out


CHUNKERS = {"fixed": fixed, "sentence": sentence, "heading": heading}


def chunk_corpus(docs: list[Doc], chunker: str, size: int, overlap: float) -> list[Chunk]:
    fn = CHUNKERS[chunker]
    return [c for d in docs for c in fn(d, size, overlap)]
