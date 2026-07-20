# AGENTS.md

Repo-specific guidance for AI coding agents. Cross-repo Definition of Done: Cursor rule `forge-agent-dod` + `verify` skill.

## What this repo is

Agentic legal intake, triage, and guided-document workflow — portfolio project (RAG, multi-step LLM orchestration, schema-validated outputs, golden-scenario evals). Phase 1 scaffold; not court-ready filings.

## Stack conventions

- Python package under `src/intake_desk/` — FastAPI API, pipeline stages (intake → classify → retrieve → draft).
- Evals under `eval/`; docker compose for local DB.
- Prefer matching existing neighbor modules before inventing new pipeline stages.

## Verify

```bash
python3 -m py_compile $(find src eval -name '*.py' 2>/dev/null)
# Prefer when deps installed:
#   pytest
#   python eval/runner.py
```

## Gotchas

- Needs `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` in `.env` for live LLM/embeddings — keep gitignored.
- Don't present placeholder-corpus eval scores as production-ready metrics.
