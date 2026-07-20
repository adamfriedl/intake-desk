# Intake Desk

Agentic legal intake, triage, and guided-document workflow — a portfolio project demonstrating RAG, multi-step LLM orchestration, schema-validated outputs, and golden-scenario evals for legal self-help contexts.

**Status:** Phase 1 + review UI MVP — OpenRouter LLM/embeddings, pgvector RAG, citation grounding, advocate review UI, 16/16 evals. Not court-ready filings.

## What it does

1. **Intake** — extract structured facts from a layperson message
2. **Classify** — route to matter type with confidence + human-review flag
3. **Retrieve** — RAG over a curated corpus with mandatory citations
4. **Draft** — section-level outline for advocate review (not court-ready filings)
5. **Review** — approve, edit, or reject draft sections in the web UI

```
User message → intake → classify → retrieve/RAG → draft outline → advocate review
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
make up              # API on :8000
```

Open http://127.0.0.1:8000/ — run intake, click citations to view source chunks, review draft sections.

## Run evals

```bash
make eval
```

Requires API keys and an ingested pgvector index. Current scaffold: **16/16** golden scenarios passing.

## Run tests

```bash
make test                 # unit tests only (CI default)
make test-integration     # retrieval smoke tests (needs API key + ingest)
```

## Project layout

```
intake-desk/
├── corpus/           # manifest + raw self-help digests (~29 docs)
├── eval/scenarios/   # golden YAML scenarios (16)
├── src/intake_desk/
│   ├── agents/       # intake, classify, retrieve, draft
│   ├── api/          # FastAPI routes + review endpoints
│   ├── eval/         # eval runner
│   ├── orchestrator/ # pipeline
│   ├── rag/          # chunking, embeddings, pgvector, grounding
│   ├── review/       # in-memory advocate session store
│   └── schemas/      # Pydantic models
├── tests/
└── web/              # advocate review UI
```

## Build phases

See `~/forge/job-search/notes/legal-engineer-research.md` for the full portfolio plan.

- [x] Phase 0 — scaffold + end-to-end pipeline skeleton
- [x] Phase 1 — corpus, pgvector ingest, citation grounding, refusal behavior
- [ ] Phase 2 — audit logging polish, schema hardening, classifier tuning
- [x] Phase 3 — human-in-loop review UI (MVP)
- [~] Phase 4 — 30+ golden scenarios, CI eval reporting (unit CI landed)

## Limitations

- Mix of educational digests and condensed FTC public excerpts — confirm against primary sources
- Decision-support only; not legal advice
- Review sessions are in-memory (restart clears them)
- Eval scores are scaffold metrics, not production quality claims

## License

MIT (corpus sources remain under their original licenses; digests are attributed educational summaries)
