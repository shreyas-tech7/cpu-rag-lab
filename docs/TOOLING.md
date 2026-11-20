# Tooling

| Tool | Source | Version | Why | Check result |
| --- | --- | --- | --- | --- |
| superpowers skills | already in the session (claude.ai account) | as installed | plans, TDD, debugging, verification | used by hand. `writing-plans` format followed for docs/PLAN.md without loading the skill, to save tokens |
| ponytail, caveman, humanizer | `npx skills add ...` | none | code style, terse progress, doc pass | not installed. The permission system denied the install command. Their rules were applied by hand |
| gitleaks | `go install github.com/zricethezav/gitleaks/v8@latest` | v8.30.1 | secret scan before each commit | installed, runs clean with one allowlisted public sample JWT (see .gitleaks.toml) |
| actionlint | `go install github.com/rhysd/actionlint/cmd/actionlint@latest` | v1.7.12 | workflow lint | installed, both workflows pass |
| pip-audit | `uv tool install pip-audit` | latest on 2026-11-20 | dependency audit | installed |
| ruff | PyPI (dev extra) | from lock at install time | lint, format, `--select S` security rules | runs in init.sh |
| graphify, cisco-ai-skill-scanner, pre-commit | `uv tool install` | not installed | not needed: under 30 source files, no new skills installed, gitleaks runs directly | skipped |
