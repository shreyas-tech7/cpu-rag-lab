# Environment

Probed on 2026-11-20 with `curl -sS -o /dev/null -w '%{http_code}' -m 10 <url>`.

| Host | Answer | Used for |
| --- | --- | --- |
| https://huggingface.co | CONNECT 403 (blocked) | FastEmbed models (not reachable) |
| https://storage.googleapis.com | 400 (reachable), `qdrant-fastembed` bucket objects 403 AccessDenied | Old FastEmbed mirror (not usable) |
| https://chroma-onnx-models.s3.amazonaws.com | 206 | all-MiniLM-L6-v2 ONNX export |
| https://scifact.s3-us-west-2.amazonaws.com | 200 | SciFact dataset |
| https://raw.githubusercontent.com | 301 (reachable) | Self-made corpus docs |
| https://pypi.org, https://registry.npmjs.org | reachable | Name checks, packages |
| https://api.groq.com, https://openrouter.ai | CONNECT 403 | Record mode (blocked) |
| https://api.osv.dev, https://semgrep.dev | CONNECT 403 | Not used |
| https://public.ukp.informatik.tu-darmstadt.de (BEIR) | CONNECT 403 | Not used |

Machine: Intel(R) Xeon(R) Processor @ 2.30GHz, 4 cores, 15 GB RAM, Python 3.13.18, uv 0.11.32, FastEmbed 0.9.1. No provider key variables were set.
