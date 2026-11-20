"""Every number in the README and the decision guide must come from results.jsonl."""

import json
import re

import pytest

from cpu_rag_lab.corpus import ROOT
from cpu_rag_lab.grid import read_jsonl
from cpu_rag_lab.report import CONSTANTS, build, ranked

RESULTS = ROOT / "results" / "results.jsonl"
NUM = re.compile(r"(?<![\w.])\d[\d,]*(?:\.\d+)?")
# Names that hold digits but are not results.
NAMES = re.compile(
    r"(nDCG|Recall|MRR)@\d+|v0\.1\.0-rc1|Python 3\.11|SHA-256|sha256 `[0-9a-f]+`|BSD-3-Clause|"
    r"Apache-2\.0|BY-NC 2\.0|MiniLM-L6-v2|bge-small-en-v1\.5|scifact1000|taskset -c 0-3|"
    r"\d+-core|`[^`]*`|\(https?://[^)]*\)|https?://\S+|\d{4}-\d{2}-\d{2}|@ \d+\.\d+GHz"
)

pytestmark = pytest.mark.skipif(not RESULTS.exists(), reason="no results.jsonl yet")


@pytest.fixture(scope="module")
def built():
    return build(RESULTS)


def numbers(text: str) -> list[str]:
    return NUM.findall(NAMES.sub(" ", text))


def test_guide_file_matches_results(built):
    files, _ = built
    path = ROOT / "docs" / "DECISION_GUIDE.md"
    assert path.read_text() == files[path], "run `cpu-rag-lab report`"


def test_guide_every_number_traces_to_results(built):
    """Broken case: a number typed into the guide by hand, or a stale guide."""
    files, facts = built
    text = files[ROOT / "docs" / "DECISION_GUIDE.md"]
    bad = [n for n in numbers(text) if n not in facts.seen and n not in CONSTANTS]
    assert not bad, f"numbers with no source: {bad[:10]}"


def test_guide_best_setting_matches_raw_rows(built):
    files, _ = built
    text = (ROOT / "docs" / "DECISION_GUIDE.md").read_text()
    rows = [r for r in read_jsonl(RESULTS) if r["status"] == "done"]
    for corpus in {r["corpus"] for r in rows}:
        best = max(
            (r for r in rows if r["corpus"] == corpus),
            key=lambda r: (r["metrics"]["ndcg@10"]["mean"], -r["latency_ms"]["p95"]),
        )
        m = best["metrics"]["ndcg@10"]
        assert f"nDCG@10 {m['mean']:.3f} [{m['lo']:.3f}, {m['hi']:.3f}]" in text
        assert best["run_id"] == ranked(rows, corpus)[0]["run_id"]


def test_readme_numbers_trace_to_results(built):
    files, facts = built
    readme = files[ROOT / "README.md"]
    assert (ROOT / "README.md").read_text() == readme, "run `cpu-rag-lab report`"
    bad = [n for n in numbers(readme) if n not in facts.seen and n not in CONSTANTS]
    assert not bad, f"README numbers with no source: {bad[:10]}"


def test_readme_table_has_intervals_latency_and_ram(built):
    files, _ = built
    readme = files[ROOT / "README.md"]
    for col in (
        "Recall@10 [95% CI]",
        "MRR@10 [95% CI]",
        "nDCG@10 [95% CI]",
        "p95 ms",
        "Peak RAM MB",
    ):
        assert col in readme
    assert re.search(r"\| 1 \| .*\d\.\d{3} \[\d\.\d{3}, \d\.\d{3}\]", readme)


def test_readme_models_have_size_license_revision():
    readme = (ROOT / "README.md").read_text()
    reg = json.loads((ROOT / "models.json").read_text())["models"]
    for name, m in reg.items():
        row = next(line for line in readme.splitlines() if line.startswith(f"| `{name}`"))
        assert m["license"] in row and str(m["size_mb"]) in row and m["revision"] in row


def test_site_opens_from_disk(built):
    """Broken case: the page loads its data with fetch(), which fails from file://."""
    files, _ = built
    html = files[ROOT / "docs" / "index.html"]
    assert (ROOT / "docs" / "index.html").read_text() == html
    assert "fetch(" not in html
    assert not re.search(r'(src|href)="https?://', html)
    data = re.search(r'<script type="application/json" id="data">(.*?)</script>', html, re.S)
    rows = json.loads(data.group(1).replace("<\\/", "</"))
    assert len(rows) == sum(r["status"] == "done" for r in read_jsonl(RESULTS))
    assert html.count("<svg") >= 2
