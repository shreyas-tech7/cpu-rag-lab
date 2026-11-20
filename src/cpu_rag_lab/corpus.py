"""Corpora and queries.

A corpus is a list of documents. Each document is a list of sections. A section is
the unit that a query can be relevant to. A query lists the ids of its relevant units.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Section:
    unit_id: str
    heading: str
    text: str


@dataclass
class Doc:
    doc_id: str
    sections: list[Section]


@dataclass
class Query:
    query_id: str
    text: str
    relevant: set[str] = field(default_factory=set)


@dataclass
class Corpus:
    name: str
    docs: list[Doc]
    queries: list[Query]


ROOT = Path(__file__).resolve().parents[2]

_FENCE = re.compile(r"^(```|~~~)")
_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_NOISE = re.compile(r"\{\*.*?\*\}|<[^>]+>|\{\s*#[^}]*\}|!!!\s*\w+.*$|///.*$")
_GENERIC = {
    "recap",
    "example",
    "examples",
    "note",
    "notes",
    "summary",
    "overview",
    "about",
    "info",
    "tip",
    "next steps",
    "technical details",
    "see also",
    "usage",
    "introduction",
}
MIN_SECTION_WORDS = 30


def parse_markdown(doc_id: str, text: str) -> Doc:
    """Split Markdown into sections at headings. Code blocks and include tags are dropped.

    The heading line is kept out of the section text, so a heading query does not get a
    free exact match on its own line.
    """
    sections: list[Section] = []
    heading, buf, in_code = "", [], False
    count = 0

    def flush() -> None:
        nonlocal count
        body = " ".join(" ".join(buf).split())
        if body:
            sections.append(Section(f"{doc_id}#{count}", heading, body))
            count += 1

    for line in text.splitlines():
        if _FENCE.match(line.strip()):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = _HEADING.match(line)
        if m:
            flush()
            heading, buf = _NOISE.sub("", m.group(2)).strip(), []
            continue
        buf.append(_NOISE.sub(" ", line))
    flush()
    return Doc(doc_id, sections)


def queries_from_headings(docs: list[Doc]) -> list[Query]:
    """Make one query per useful section heading. The section is the right answer.

    This is a proxy. Headings are short and written by the same authors as the text.
    Generic headings, repeated headings and sections under MIN_SECTION_WORDS are skipped.
    """
    seen: dict[str, int] = {}
    for d in docs:
        for s in d.sections:
            seen[s.heading.lower()] = seen.get(s.heading.lower(), 0) + 1
    out = []
    for d in docs:
        for s in d.sections:
            h = s.heading.strip()
            key = h.lower()
            if not h or key in _GENERIC or seen[key] > 1 or len(h.split()) < 2:
                continue
            if len(s.text.split()) < MIN_SECTION_WORDS:
                continue
            out.append(Query(f"q{len(out)}", h, {s.unit_id}))
    return out


def load_selfmade(root: Path | None = None) -> Corpus:
    root = root or ROOT / "data" / "selfmade"
    manifest = json.loads((root / "manifest.json").read_text())
    docs = []
    for item in manifest["files"]:
        text = (root / "raw" / item["local"]).read_text(encoding="utf-8")
        doc = parse_markdown(item["local"], text)
        if doc.sections:
            docs.append(doc)
    return Corpus("selfmade", docs, queries_from_headings(docs))


def load_scifact(root: Path | None = None, max_docs: int | None = None, seed: int = 0) -> Corpus:
    """SciFact (Wadden et al. 2020): 5,183 abstracts and the 300 dev claims as queries.

    Relevance comes from each claim's cited_doc_ids, as in the BEIR test split.
    With max_docs, the corpus keeps every cited abstract and fills the rest with
    abstracts drawn at random with `seed`. A smaller pool is an easier task.
    """
    root = root or ROOT / "data" / "scifact" / "data"
    docs = []
    for line in (root / "corpus.jsonl").read_text().splitlines():
        r = json.loads(line)
        did = str(r["doc_id"])
        text = " ".join(r["abstract"])
        docs.append(Doc(did, [Section(did, r["title"], f"{r['title']}. {text}")]))
    queries = []
    for line in (root / "claims_dev.jsonl").read_text().splitlines():
        r = json.loads(line)
        rel = {str(x) for x in r["cited_doc_ids"]}
        if rel:
            queries.append(Query(str(r["id"]), r["claim"], rel))
    name = "scifact"
    if max_docs and max_docs < len(docs):
        import random

        cited = {u for q in queries for u in q.relevant}
        rest = sorted(d.doc_id for d in docs if d.doc_id not in cited)
        keep = cited | set(random.Random(seed).sample(rest, max(0, max_docs - len(cited))))
        docs = [d for d in docs if d.doc_id in keep]
        name = f"scifact{max_docs}"
    return Corpus(name, docs, queries)


def load_tiny() -> Corpus:
    """A built-in toy corpus for unit tests and the tiny grid. Needs no download."""
    md = (Path(__file__).parent / "tiny.md").read_text()
    docs = [parse_markdown("tiny.md", md)]
    return Corpus("tiny", docs, queries_from_headings(docs))


LOADERS = {
    "selfmade": load_selfmade,
    "scifact": load_scifact,
    "scifact1000": lambda: load_scifact(max_docs=1000, seed=0),
    "tiny": load_tiny,
}


def load(name: str) -> Corpus:
    return LOADERS[name]()
