# Intake Desk

Agentic legal intake, triage, and guided-document workflow — a portfolio project demonstrating RAG, multi-step LLM orchestration, schema-validated outputs, and golden-scenario evals for legal self-help contexts.

**Status:** Phase 1 in progress — ~29-doc topic-matrix corpus, pgvector ingest path, citation grounding + refusal checks. Not court-ready filings.

## What it does

1. **Intake** — extract structured facts from a layperson message
2. **Classify** — route to matter type with confidence + human-review flag
3. **Retrieve** — RAG over a curated corpus with mandatory citations
4. **Draft** — section-level outline for advocate review (not court-ready filings)

```
User message → intake → classify → retrieve/RAG → draft outline → human review
```

## Quick start

```bash
cd intake-desk
python3 -m venv --clear .venv
source .venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Set OPENROUTER_API_KEY (chat + embeddings). Optional: bump LLM_MODEL for demos.

docker compose up -d db
make ingest          # chunk + embed corpus into pgvector
uvicorn intake_desk.api.main:app --reload --app-dir src
```

Open http://127.0.0.1:8000/

## Run evals

```bash
python eval/runner.py
```

Requires API keys and (preferably) an ingested pgvector index. Expand `eval/scenarios/` as you harden the pipeline.

## Run tests

```bash
pytest
```

## Project layout

```
intake-desk/
├── corpus/           # manifest + raw public self-help digests (~29 docs)
├── eval/scenarios/   # golden YAML scenarios (~15)
├── src/intake_desk/
│   ├── agents/       # intake, classify, retrieve, draft
│   ├── api/          # FastAPI routes
│   ├── eval/         # eval runner
│   ├── orchestrator/ # pipeline
│   ├── rag/          # chunking, embeddings, pgvector store, grounding
│   └── schemas/      # Pydantic models
├── tests/
└── web/              # minimal demo UI
```

## Build phases

See `~/forge/job-search/notes/legal-engineer-research.md` for the full portfolio plan.

- [x] Phase 0 — scaffold + end-to-end pipeline skeleton
- [~] Phase 1 — comprehensive corpus, pgvector ingest, citation grounding, refusal behavior (code landed; run `make ingest` with API keys)
- [ ] Phase 2 — audit logging polish, schema hardening, classifier tuning
- [ ] Phase 3 — human-in-loop review UI
- [ ] Phase 4 — 30+ golden scenarios, CI eval reporting

## Limitations

- Educational digests — confirm against primary sources before real advocate use
- Decision-support only; not legal advice
- Eval scores are scaffold metrics, not production quality claims

## License

MIT (corpus sources remain under their original licenses; digests are attributed educational summaries)
