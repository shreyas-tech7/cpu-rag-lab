"""Write the README tables, the decision guide and the static site from results.jsonl.

Nobody types a number. Every measured number in these files passes through `Facts`, which
records it. The tests regenerate the files and check every number against results.jsonl.
"""

from __future__ import annotations

import json
import math
import re
import statistics
from html import escape
from pathlib import Path

from .corpus import ROOT
from .grid import DONE, FAILED, read_jsonl
from .svg import bars, scatter

CORPUS_NAMES = {
    "selfmade": "self-made docs (fastapi, uv, httpx)",
    "scifact1000": "SciFact, 1,000-abstract pool",
    "scifact": "SciFact, full pool",
    "tiny": "tiny toy corpus",
}
RETRIEVER_ORDER = ("bm25", "dense", "hybrid")
# Numbers that are part of the method, not results. The number-match test allows these.
CONSTANTS = {"95", "0", "20", "1000", "2", "2048", "60", "100", "256", "32", "5", "10", "4", "1"}
BEGIN, END = "<!-- BEGIN:{} -->", "<!-- END:{} -->"


class Facts:
    """Formats numbers and keeps every formatted string it hands out."""

    def __init__(self) -> None:
        self.seen: set[str] = set()

    def f(self, x: float, nd: int = 3) -> str:
        s = f"{x:,.{nd}f}"
        self.seen.add(s)
        return s

    def i(self, x: int | float) -> str:
        s = f"{round(x):,}"
        self.seen.add(s)
        return s

    def ci(self, m: dict) -> str:
        return f"{self.f(m['mean'])} [{self.f(m['lo'])}, {self.f(m['hi'])}]"


def latest_rows(rows: list[dict]) -> list[dict]:
    """One row per run id. A run retried with --retry-failed keeps only its last row."""
    last: dict[str, dict] = {}
    for r in rows:
        last[r["run_id"]] = r
    return list(last.values())


def done_rows(rows: list[dict]) -> list[dict]:
    return [r for r in rows if r["status"] == DONE]


def label(r: dict, facts: Facts | None = None) -> str:
    size = facts.i(r["size"]) if facts else str(r["size"])
    ov = facts.i(r["overlap"] * 100) if facts else f"{r['overlap'] * 100:.0f}"
    model = "" if r["model"] == "-" else f" ({r['model']})"
    return f"{r['retriever']}{model}, {r['chunker']} {size} words, {ov}% overlap"


def ranked(rows: list[dict], corpus: str, metric: str = "ndcg@10") -> list[dict]:
    """Best first by mean, then by lower p95 latency, then by run id."""
    rs = [r for r in rows if r["corpus"] == corpus]
    return sorted(
        rs, key=lambda r: (-r["metrics"][metric]["mean"], r["latency_ms"]["p95"], r["run_id"])
    )


def corpora(rows: list[dict]) -> list[str]:
    return list(dict.fromkeys(r["corpus"] for r in rows))


def top_table(rows: list[dict], corpus: str, facts: Facts, n: int = 5) -> str:
    head = (
        "| # | Retriever | Chunker | Size (words) | Overlap | Recall@10 [95% CI] | MRR@10 [95% CI] "
        "| nDCG@10 [95% CI] | p50 ms | p95 ms | Peak RAM MB | Build s |\n"
        "|---|---|---|---|---|---|---|---|---|---|---|---|\n"
    )
    lines = []
    for k, r in enumerate(ranked(rows, corpus)[:n], 1):
        model = "" if r["model"] == "-" else f" ({r['model']})"
        lines.append(
            f"| {facts.i(k)} | {r['retriever']}{model} | {r['chunker']} | {facts.i(r['size'])} | "
            f"{facts.i(r['overlap'] * 100)}% | {facts.ci(r['metrics']['recall@10'])} | "
            f"{facts.ci(r['metrics']['mrr@10'])} | {facts.ci(r['metrics']['ndcg@10'])} | "
            f"{facts.f(r['latency_ms']['p50'], 2)} | {facts.f(r['latency_ms']['p95'], 2)} | "
            f"{facts.i(r['peak_rss_mb'])} | {facts.f(r['index_build_s'], 2)} |"
        )
    return head + "\n".join(lines)


def tie_note(top: list[dict], metric: str = "ndcg@10") -> str:
    """A sentence for under a top table, only when every row's interval overlaps the best row's."""
    if len(top) < 2:
        return ""
    best = top[0]["metrics"][metric]
    if all(
        r["metrics"][metric]["lo"] <= best["hi"] and r["metrics"][metric]["hi"] >= best["lo"]
        for r in top
    ):
        rows = "these five rows" if len(top) == 5 else "these rows"
        return f"The intervals of {rows} overlap, so treat them as a tie."
    return ""


def run_facts(rows: list[dict]) -> dict:
    """Totals for the whole grid."""
    done = done_rows(rows)
    return {
        "runs": len(rows),
        "done": len(done),
        "failed": sum(r["status"] == FAILED for r in rows),
        # fsum gives the same answer on every Python version (sum() changed in 3.12).
        "wall_s": round(math.fsum(r.get("wall_s", 0) for r in rows), 3),
        "peak_rss_mb": max((r["peak_rss_mb"] for r in done), default=0),
        "memory_limit_mb": max((r["memory_limit_mb"] for r in rows), default=0),
        "grids": sorted({r["grid"] for r in rows}),
        "dates": sorted({r["date"] for r in rows}),
        "cpu": sorted({r["cpu"] for r in rows}),
        "threads": sorted({r["threads"] for r in rows}),
        "seeds": sorted({r["seed"] for r in rows}),
        "models": sorted({r["model"] for r in rows if r["model"] != "-"}),
    }


def status_block(rows: list[dict], facts: Facts) -> str:
    t = run_facts(rows)
    pools = []
    for c in corpora(rows):
        r = next(x for x in rows if x["corpus"] == c)
        pools.append(f"{c} ({facts.i(r['n_docs'])} docs, {facts.i(r['n_queries'])} queries)")
    return (
        f"Grid `{', '.join(t['grids'])}`: {facts.i(t['done'])} of {facts.i(t['runs'])} runs done, "
        f"{facts.i(t['failed'])} failed, {facts.f(t['wall_s'] / 60, 1)} minutes of run time, "
        f"peak RSS {facts.i(t['peak_rss_mb'])} MB. Run on {', '.join(t['dates'])}, "
        f"{', '.join(t['cpu'])}, {', '.join(str(x) for x in t['threads'])} threads, "
        f"bootstrap seed {', '.join(str(x) for x in t['seeds'])}. Corpora: {', '.join(pools)}."
    )


def cost_block(rows: list[dict], facts: Facts) -> str:
    done = done_rows(rows)
    lines = [
        "| Corpus | Retriever | Median build s | Median p50 ms per query | Median peak RAM MB |",
        "|---|---|---|---|---|",
    ]
    for c in corpora(done):
        for ret in RETRIEVER_ORDER:
            rs = [r for r in done if r["corpus"] == c and r["retriever"] == ret]
            if not rs:
                continue
            lines.append(
                f"| {c} | {ret} | {facts.f(statistics.median(r['index_build_s'] for r in rs), 2)} | "
                f"{facts.f(statistics.median(r['latency_ms']['p50'] for r in rs), 2)} | "
                f"{facts.i(statistics.median(r['peak_rss_mb'] for r in rs))} |"
            )
    return "\n".join(lines)


def models_block(facts: Facts) -> str:
    """Model facts come from models.json, the pinned model list, not from a run."""
    reg = json.loads((ROOT / "models.json").read_text())
    lines = ["| Model | Kind | Size MB | License | Pinned revision |", "|---|---|---|---|---|"]
    for name, m in reg["models"].items():
        rev = m["revision"]
        if m.get("model_file_sha256"):
            rev += f", model.onnx sha256 `{m['model_file_sha256'][:16]}`"
        lines.append(
            f"| `{name}` {m.get('hf_name', '')} | {m['kind']} | {m['size_mb']} | {m['license']} | {rev} |"
        )
    lines.append("")
    lines.append("Hashes are shortened here. The full SHA-256 values are in `models.json`.")
    lines.append("")
    lines.append("Blocked on the build machine:")
    lines.append("")
    for name, why in reg["blocked"].items():
        lines.append(f"- `{name}`: {why}")
    text = "\n".join(lines)
    facts.seen.update(re.findall(r"\d[\d,]*(?:\.\d+)?", text))
    return text


def _mean(rows: list[dict], key=lambda r: r["metrics"]["ndcg@10"]["mean"]) -> float:
    return statistics.fmean(key(r) for r in rows)


def guide(rows: list[dict], facts: Facts) -> str:
    """The decision guide. Every sentence with a number is built from results."""
    done = done_rows(rows)
    t = run_facts(rows)
    out = [
        "# Decision guide",
        "",
        "This guide is written by `cpu-rag-lab report` from `results/results.jsonl`. Do not edit it by hand.",
        "",
        f"Source: {facts.i(t['done'])} finished runs on {', '.join(t['dates'])}, "
        f"{', '.join(t['cpu'])}, {', '.join(str(x) for x in t['threads'])} threads. "
        f"Model: {', '.join(t['models']) or 'none'}. Intervals are 95% percentile bootstrap "
        "intervals over queries, 1000 resamples, seed 0. Main score: nDCG@10.",
        "",
    ]
    for c in corpora(done):
        rk = ranked(done, c)
        best = rk[0]
        bm = best["metrics"]["ndcg@10"]
        out += [f"## {CORPUS_NAMES.get(c, c)}", ""]
        out.append(
            f"- **Best setting:** {label(best, facts)}. nDCG@10 {facts.ci(bm)}, "
            f"Recall@10 {facts.ci(best['metrics']['recall@10'])}, "
            f"p95 latency {facts.f(best['latency_ms']['p95'], 2)} ms, "
            f"{facts.i(best['n_queries'])} queries."
        )
        tied = [r for r in rk[1:] if r["metrics"]["ndcg@10"]["mean"] >= bm["lo"]]
        noun = "setting has" if len(tied) == 1 else "settings have"
        out.append(
            f"- **Close calls:** {facts.i(len(tied))} other {noun} a mean nDCG@10 inside the "
            "best setting's interval. Treat them as ties with this many queries."
        )
        fast = min([best] + tied, key=lambda r: (r["latency_ms"]["p95"], r["run_id"]))
        out.append(
            f"- **Fast pick inside that interval:** {label(fast, facts)}. nDCG@10 "
            f"{facts.f(fast['metrics']['ndcg@10']['mean'])}, p95 latency "
            f"{facts.f(fast['latency_ms']['p95'], 2)} ms, build {facts.f(fast['index_build_s'], 2)} s."
        )
        out += ["", "### Retriever", ""]
        out.append(
            "| Retriever | Best nDCG@10 [95% CI] | Its setting | Mean nDCG@10 over all its runs | Median p50 ms |"
        )
        out.append("|---|---|---|---|---|")
        per_ret = {}
        for ret in RETRIEVER_ORDER:
            rs = [r for r in rk if r["retriever"] == ret]
            if not rs:
                continue
            per_ret[ret] = rs
            out.append(
                f"| {ret} | {facts.ci(rs[0]['metrics']['ndcg@10'])} | {label(rs[0], facts)} | "
                f"{facts.f(_mean(rs))} | {facts.f(statistics.median(r['latency_ms']['p50'] for r in rs), 2)} |"
            )
        if {"bm25", "dense"} <= per_ret.keys():
            b, d = (
                per_ret["bm25"][0]["metrics"]["ndcg@10"],
                per_ret["dense"][0]["metrics"]["ndcg@10"],
            )
            win = "dense" if d["mean"] > b["mean"] else "bm25"
            sep = d["lo"] > b["hi"] or b["lo"] > d["hi"]
            out += [
                "",
                f"Best dense against best BM25: {win} is ahead, and the intervals "
                + ("do not overlap." if sep else "overlap, so the gap may be noise."),
            ]
        singles = [per_ret[r][0] for r in per_ret if r != "hybrid"]
        if "hybrid" in per_ret and singles:
            h = per_ret["hybrid"][0]["metrics"]["ndcg@10"]
            o = max(singles, key=lambda r: r["metrics"]["ndcg@10"]["mean"])["metrics"]["ndcg@10"]
            ahead = "ahead of" if h["mean"] > o["mean"] else "behind"
            sep = h["lo"] > o["hi"] or o["lo"] > h["hi"]
            out.append(
                f"Best hybrid search with reciprocal rank fusion is {ahead} the best single "
                f"retriever ({facts.f(h['mean'])} against {facts.f(o['mean'])}), and the "
                + (
                    "intervals do not overlap."
                    if sep
                    else "intervals overlap, so the gap may be noise."
                )
            )
        out += ["", "### Chunk size", ""]
        sizes = sorted({r["size"] for r in rk})
        out.append(
            "Mean over the other settings at each size. Build time is the mean index build time."
        )
        out.append("")
        out.append("| Retriever | " + " | ".join(f"{facts.i(s)} words" for s in sizes) + " |")
        out.append("|---|" + "---|" * len(sizes))
        for ret, rs in per_ret.items():
            cells = []
            for s in sizes:
                at = [r for r in rs if r["size"] == s]
                if not at:
                    cells.append("no finished run")
                    continue
                cells.append(
                    f"nDCG {facts.f(_mean(at))}, p50 {facts.f(_mean(at, lambda r: r['latency_ms']['p50']), 2)} ms, "
                    f"build {facts.f(_mean(at, lambda r: r['index_build_s']), 2)} s"
                )
            out.append(f"| {ret} | " + " | ".join(cells) + " |")
        by_size = {s: _mean([r for r in rk if r["size"] == s]) for s in sizes}  # rk is done rows
        top_size = max(by_size, key=lambda s: by_size[s])
        out += [
            "",
            f"Across all retrievers, {facts.i(top_size)}-word chunks score best on average "
            f"(mean nDCG@10 {facts.f(by_size[top_size])}).",
        ]
        out += ["", "### Overlap and chunker", ""]
        for key, name in (("overlap", "Overlap"), ("chunker", "Chunker")):
            vals = sorted({r[key] for r in rk}, key=str)
            parts = []
            for v in vals:
                shown = f"{facts.i(v * 100)}%" if key == "overlap" else v
                parts.append(f"{shown}: {facts.f(_mean([r for r in rk if r[key] == v]))}")
            out.append(f"- **{name}**, mean nDCG@10: " + ", ".join(parts) + ".")
        out.append("")
    out += [
        "## Memory and time",
        "",
        f"- Highest peak RSS in a finished run: {facts.i(t['peak_rss_mb'])} MB. The guard "
        f"stops any run over {facts.i(t['memory_limit_mb'])} MB.",
        f"- Total run time of the grid: {facts.f(t['wall_s'] / 60, 1)} minutes "
        f"for {facts.i(t['done'])} runs.",
        f"- Failed runs: {facts.i(t['failed'])}.",
        "",
        "## Limits",
        "",
        "- Self-made queries are section headings. They are a proxy for real questions and favor words that the docs already use.",
        "- The SciFact pool is cut down for time. A smaller pool makes retrieval easier than the full benchmark.",
        "- MiniLM reads at most 256 tokens, so long chunks are cut short for dense search.",
        "- A retrieved chunk gives credit to every section its words come from. A long fixed or sentence chunk can span several short sections, while a heading chunk spans one. This favors long chunks a little and heading chunks on the self-made corpus.",
        "- One machine, one model and one seed for the bootstrap. Timings move with the machine.",
        "",
    ]
    return "\n".join(out)


CSS = """
:root{--bg:#ffffff;--fg:#1b1f24;--muted:#57606a;--line:#d0d7de;--card:#f6f8fa;
--s1:#2f6fdd;--s2:#e07b39;--s3:#2a9d6f;--s4:#9a59c9}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){--bg:#0d1117;--fg:#e6edf3;
--muted:#9aa4ae;--line:#30363d;--card:#161b22;--s1:#6ea8ff;--s2:#f3a46b;--s3:#5fd3a2;--s4:#c79bf2}}
:root[data-theme="dark"]{--bg:#0d1117;--fg:#e6edf3;--muted:#9aa4ae;--line:#30363d;--card:#161b22;
--s1:#6ea8ff;--s2:#f3a46b;--s3:#5fd3a2;--s4:#c79bf2}
body{background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,sans-serif;margin:0 auto;
max-width:1100px;padding:16px}
h1,h2{line-height:1.2}.muted{color:var(--muted)}
.chart{width:100%;max-width:680px;background:var(--card);border-radius:8px;margin:8px 0}
.chart .ct{fill:var(--fg);font-weight:600;font-size:13px}.chart .ax{fill:var(--muted);font-size:11px}
.chart .grid{stroke:var(--line)}.chart .wh{stroke:var(--fg);stroke-width:1.5}
.wrap{overflow-x:auto}table{border-collapse:collapse;font-size:13px;width:100%}
th,td{border-bottom:1px solid var(--line);padding:4px 6px;text-align:left;white-space:nowrap}
th{cursor:pointer;background:var(--card)}select{font:inherit}
"""

JS = """
const rows = JSON.parse(document.getElementById('data').textContent);
const cols = ['corpus','retriever','model','chunker','size','overlap','recall@5','recall@10','mrr@10','ndcg@10',
  'p50','p95','peak_rss_mb','index_build_s'];
let sortKey = 'ndcg@10', desc = true;
function val(r, c){
  if (c in r.metrics) return r.metrics[c].mean;
  if (c === 'p50' || c === 'p95') return r.latency_ms[c];
  return r[c];
}
function cell(r, c){
  if (c in r.metrics){const m=r.metrics[c];return m.mean.toFixed(3)+' ['+m.lo.toFixed(3)+', '+m.hi.toFixed(3)+']';}
  const v = val(r, c); return typeof v === 'number' ? String(v) : v;
}
function draw(){
  const pick = document.getElementById('corpus').value;
  const rs = rows.filter(r => pick === 'all' || r.corpus === pick)
    .sort((a,b) => { const x=val(a,sortKey), y=val(b,sortKey); return (x<y?-1:x>y?1:0)*(desc?-1:1); });
  const t = document.getElementById('runs');
  t.replaceChildren();
  const head = t.insertRow();
  cols.forEach(c => { const th = document.createElement('th'); th.textContent = c;
    th.onclick = () => { desc = (sortKey === c) ? !desc : true; sortKey = c; draw(); };
    head.appendChild(th); });
  rs.forEach(r => { const tr = t.insertRow();
    cols.forEach(c => { tr.insertCell().textContent = cell(r, c); }); });
}
document.getElementById('corpus').onchange = draw;
draw();
"""


def site(rows: list[dict], facts: Facts) -> str:
    done = done_rows(rows)
    t = run_facts(rows)
    charts = []
    for c in corpora(done):
        rk = [r for r in done if r["corpus"] == c]
        rets = [x for x in RETRIEVER_ORDER if any(r["retriever"] == x for r in rk)]
        # Only sizes where every retriever has a finished run, so no bar is a made-up zero.
        sizes = sorted(
            s
            for s in {r["size"] for r in rk}
            if all(any(r["size"] == s and r["retriever"] == x for r in rk) for x in rets)
        )
        series = {}
        for ret in rets:
            rs = [r for r in rk if r["retriever"] == ret]
            if rs:
                best = []
                for s in sizes:
                    m = max(
                        (r for r in rs if r["size"] == s),
                        key=lambda r: r["metrics"]["ndcg@10"]["mean"],
                    )["metrics"]["ndcg@10"]
                    best.append((m["mean"], m["lo"], m["hi"]))
                series[ret] = best
        charts.append(
            bars(
                f"{c}: best nDCG@10 by chunk size (words), 95% CI", [str(s) for s in sizes], series
            )
        )
        pts = [
            (
                r["run_id"],
                r["latency_ms"]["p50"],
                r["metrics"]["ndcg@10"]["mean"],
                RETRIEVER_ORDER.index(r["retriever"]),
            )
            for r in rk
        ]
        charts.append(
            scatter(
                f"{c}: nDCG@10 against p50 latency, every run",
                pts,
                "p50 latency per query, ms (log)",
                "nDCG@10",
            )
        )
    opts = "".join(f'<option value="{escape(c)}">{escape(c)}</option>' for c in corpora(done))
    data = json.dumps(done, sort_keys=True).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>cpu-rag-lab results</title><style>{CSS}</style></head><body>
<h1>cpu-rag-lab results</h1>
<p class="muted">{escape(status_block(rows, facts))} This page opens from disk. All data is inside it.</p>
<p>Read the <a href="DECISION_GUIDE.md">decision guide</a> for the takeaways. Bars show the best run at each size, with its 95% interval. Colors: blue BM25, orange dense, green hybrid.</p>
{"".join(charts)}
<h2>Every run</h2>
<p><label>Corpus <select id="corpus"><option value="all">all</option>{opts}</select></label> <span class="muted">Click a column to sort.</span></p>
<div class="wrap"><table id="runs"></table></div>
<p class="muted">Generated by <code>cpu-rag-lab report</code> from results/results.jsonl, {facts.i(t["done"])} runs.</p>
<script type="application/json" id="data">{data}</script>
<script>{JS}</script>
</body></html>
"""  # noqa: S608 - this builds HTML, not SQL


def replace_block(text: str, name: str, content: str) -> str:
    b, e = BEGIN.format(name), END.format(name)
    pat = re.compile(re.escape(b) + r".*?" + re.escape(e), re.S)
    if not pat.search(text):
        raise ValueError(f"README has no {b} block")
    return pat.sub(lambda _: f"{b}\n{content}\n{e}", text)


def readme_blocks(rows: list[dict], facts: Facts) -> dict[str, str]:
    done = done_rows(rows)
    blocks = {
        "status": status_block(rows, facts),
        "cost": cost_block(rows, facts),
        "models": models_block(facts),
    }
    tops = []
    for c in corpora(done):
        tops.append(
            f"**{CORPUS_NAMES.get(c, c)}**, top 5 of {facts.i(len(ranked(done, c)))} runs by nDCG@10:\n"
        )
        tops.append(top_table(done, c, facts))
        note = tie_note(ranked(done, c)[:5])
        if note:
            tops += ["", note]
        tops.append("")
    blocks["results"] = "\n".join(tops).rstrip()
    return blocks


def build(results: Path) -> tuple[dict[Path, str], Facts]:
    rows = latest_rows(read_jsonl(results))
    facts = Facts()
    out: dict[Path, str] = {}
    readme = (ROOT / "README.md").read_text()
    for name, content in readme_blocks(rows, facts).items():
        readme = replace_block(readme, name, content)
    out[ROOT / "README.md"] = readme
    out[ROOT / "docs" / "DECISION_GUIDE.md"] = guide(rows, facts)
    out[ROOT / "docs" / "index.html"] = site(rows, facts)
    summary = run_facts(rows)
    out[ROOT / "results" / "summary.json"] = json.dumps(summary, indent=2, sort_keys=True) + "\n"
    return out, facts


def write_all(results: Path, check: bool = False) -> list[str]:
    files, _ = build(results)
    stale = []
    for path, text in files.items():
        if check:
            if not path.exists() or path.read_text() != text:
                stale.append(str(path.relative_to(ROOT)))
        else:
            path.write_text(text)
    return stale
