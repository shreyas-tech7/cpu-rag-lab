"""Download the public data and the model once, check every hash, and cache them.

python scripts/fetch_data.py selfmade   # docs from permissive repos, pinned commits
python scripts/fetch_data.py scifact    # SciFact from the AllenAI S3 bucket
python scripts/fetch_data.py models     # all-MiniLM-L6-v2 ONNX from Chroma's S3 bucket
"""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cpu_rag_lab.embedders import cache_dir, model_registry  # noqa: E402

TIMEOUT = 60

SELFMADE = {
    "fastapi/fastapi": {
        "commit": "05e6df7e906c3decba377c37548019973f40bf15",
        "license": "MIT",
        "license_file": "LICENSE",
        "paths": [
            f"docs/en/docs/tutorial/{p}.md"
            for p in (
                "background-tasks bigger-applications body-fields body-multiple-params "
                "body-nested-models body-updates body cookie-params cors debugging "
                "dependencies/classes-as-dependencies dependencies/dependencies-with-yield "
                "dependencies/global-dependencies dependencies/index dependencies/sub-dependencies "
                "encoder extra-data-types extra-models first-steps handling-errors header-params "
                "metadata middleware path-operation-configuration path-params-numeric-validations "
                "path-params query-params-str-validations query-params request-files request-forms "
                "response-model response-status-code schema-extra-example security/first-steps "
                "security/get-current-user security/index security/oauth2-jwt security/simple-oauth2 "
                "sql-databases static-files testing"
            ).split()
        ],
    },
    "astral-sh/uv": {
        "commit": "c99faeeeeb8318d874007b4c48635d009838c1a0",
        "license": "MIT OR Apache-2.0",
        "license_file": "LICENSE-MIT",
        "paths": [
            f"docs/{p}.md"
            for p in (
                "concepts/authentication/http concepts/authentication/git concepts/build-backend "
                "concepts/cache concepts/configuration-files concepts/indexes concepts/projects/build "
                "concepts/projects/config concepts/projects/dependencies concepts/projects/export "
                "concepts/projects/init concepts/projects/layout concepts/projects/run "
                "concepts/projects/sync concepts/projects/workspaces concepts/python-versions "
                "concepts/resolution concepts/tools guides/install-python guides/integration/docker "
                "guides/integration/github guides/integration/jupyter guides/integration/pytorch "
                "guides/package guides/projects guides/scripts guides/tools pip/compile "
                "pip/environments pip/packages reference/storage reference/policies/versioning"
            ).split()
        ],
    },
    "encode/httpx": {
        "commit": "7cff5f79bc78649bbcd3fd9aa7a74c86e0f63016",
        "license": "BSD-3-Clause",
        "license_file": "LICENSE.md",
        "paths": [
            f"docs/{p}.md"
            for p in (
                "advanced/authentication advanced/clients advanced/event-hooks advanced/extensions "
                "advanced/proxies advanced/resource-limits advanced/ssl advanced/text-encodings "
                "advanced/timeouts advanced/transports async compatibility environment_variables "
                "exceptions http2 logging quickstart troubleshooting"
            ).split()
        ],
    },
}

SCIFACT = {
    "url": "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz",
    "sha256": "11c621288d41ac144d29b13b0f8503b3820b7d6e8b1f6ff24dff335c196d76be",
    "license": "CC BY-NC 2.0 (dataset), see https://github.com/allenai/scifact",
}


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as r:  # noqa: S310 - fixed https URLs
        return r.read()


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def fetch_selfmade() -> None:
    out = ROOT / "data" / "selfmade"
    files = []
    for repo, spec in SELFMADE.items():
        base = f"https://raw.githubusercontent.com/{repo}/{spec['commit']}"
        lic = get(f"{base}/{spec['license_file']}")
        lic_path = out / "licenses" / f"{repo.replace('/', '__')}.txt"
        lic_path.parent.mkdir(parents=True, exist_ok=True)
        lic_path.write_bytes(lic)
        for p in spec["paths"]:
            body = get(f"{base}/{p}")
            local = f"{repo.split('/')[1]}/{p.split('docs/', 1)[-1]}"
            dest = out / "raw" / local
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(body)
            files.append(
                {
                    "repo": repo,
                    "commit": spec["commit"],
                    "path": p,
                    "local": local,
                    "license": spec["license"],
                    "sha256": sha(body),
                }
            )
            print("ok", repo, p)
    manifest = {"source": "raw.githubusercontent.com at pinned commits", "files": files}
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")


def fetch_scifact() -> None:
    dest = ROOT / "data" / "scifact"
    if (dest / "data" / "corpus.jsonl").exists():
        print("scifact already cached")
        return
    body = get(SCIFACT["url"])
    if sha(body) != SCIFACT["sha256"]:
        raise SystemExit(f"scifact hash mismatch: {sha(body)}")
    dest.mkdir(parents=True, exist_ok=True)
    tgz = dest / "data.tar.gz"
    tgz.write_bytes(body)
    with tarfile.open(tgz) as t:
        t.extractall(dest, filter="data")
    print("scifact ok", SCIFACT["sha256"])


def fetch_models() -> None:
    for name, spec in model_registry().items():
        if spec["kind"] != "fastembed":
            continue
        dest = cache_dir() / "models" / name
        model_file = dest / spec["subdir"] / "model.onnx"
        if not model_file.exists():
            body = get(spec["url"])
            if sha(body) != spec["archive_sha256"]:
                raise SystemExit(f"{name}: archive hash mismatch {sha(body)}")
            dest.mkdir(parents=True, exist_ok=True)
            tgz = dest / "archive.tar.gz"
            tgz.write_bytes(body)
            with tarfile.open(tgz) as t:
                t.extractall(dest, filter="data")
        got = sha(model_file.read_bytes())
        if got != spec["model_file_sha256"]:
            raise SystemExit(f"{name}: model.onnx hash mismatch {got}")
        print("model ok", name, got[:12])


if __name__ == "__main__":
    jobs = {"selfmade": fetch_selfmade, "scifact": fetch_scifact, "models": fetch_models}
    for arg in sys.argv[1:] or list(jobs):
        jobs[arg]()
