"""The `cpu-rag-lab` command: `run` a grid, `report` the results, `status` of a grid."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .corpus import ROOT
from .grid import FAILED, PENDING, Runner, expand, load_config, states


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="cpu-rag-lab", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run a grid; resumes from the results file")
    r.add_argument("--config", default=str(ROOT / "configs" / "tiny.json"))
    r.add_argument("--results", default=None, help="default grid: results/results.jsonl")
    r.add_argument("--retry-failed", action="store_true")
    r.add_argument("--max-runs", type=int, default=None, help="stop after this many runs")
    s = sub.add_parser("status", help="count pending, done and failed runs")
    s.add_argument("--config", default=str(ROOT / "configs" / "tiny.json"))
    s.add_argument("--results", default=None)
    rep = sub.add_parser("report", help="write the README tables, decision guide and site")
    rep.add_argument("--results", default=str(ROOT / "results" / "results.jsonl"))
    rep.add_argument("--check", action="store_true", help="fail if a generated file is stale")
    a = p.parse_args(argv)

    if a.cmd == "report":
        from .report import write_all

        stale = write_all(Path(a.results), check=a.check)
        if stale:
            print("stale:", ", ".join(stale))
            return 1
        print("report written" if not a.check else "report up to date")
        return 0

    cfg = load_config(a.config)
    fname = "results.jsonl" if cfg["name"] == "default" else f"{cfg['name']}.jsonl"
    results = Path(a.results or ROOT / "results" / fname)
    results.parent.mkdir(parents=True, exist_ok=True)
    if a.cmd == "status":
        st = states(results)
        specs = expand(cfg)
        counts = {k: 0 for k in (PENDING, "done", FAILED)}
        for spec in specs:
            counts[st.get(spec.run_id, PENDING)] += 1
        print(
            f"{cfg['name']}: {len(specs)} runs, " + ", ".join(f"{v} {k}" for k, v in counts.items())
        )
        return 0
    done = {"n": 0}

    def stop(_spec) -> bool:
        done["n"] += 1
        return a.max_runs is not None and done["n"] > a.max_runs

    Runner(cfg, results, retry_failed=a.retry_failed).run(should_stop=stop)
    return 0


if __name__ == "__main__":
    sys.exit(main())
