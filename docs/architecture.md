# Architecture

## Overview

Intake Desk is a multi-agent pipeline that converts unstructured legal questions into structured intake records, grounded answers, and advocate-review outlines.

## Components

| Layer        | Module                                     | Responsibility                            |
| ------------ | ------------------------------------------ | ----------------------------------------- |
| API          | `src/intake_desk/api`                      | HTTP interface, request validation        |
| Orchestrator | `src/intake_desk/orchestrator/pipeline.py` | Step sequencing, audit log                |
| Agents       | `src/intake_desk/agents/`                  | Intake, classify, retrieve, draft         |
| RAG          | `src/intake_desk/rag/`                     | Chunking, embeddings, pgvector, grounding |
| Schemas      | `src/intake_desk/schemas/`                 | Typed outputs for each stage              |
| Eval         | `src/intake_desk/eval/`                    | Golden scenarios + pass/fail runner       |

## Data flow

```mermaid
flowchart LR
  A[User message] --> B[Intake agent]
  B --> C[Classifier]
  C --> D[Retriever]
  D --> E[Grounding check]
  E --> F[Draft outline]
  F --> G[Human review]
```

## Design choices

- **Citation-required answers:** retrieval agent must ground claims in corpus chunks or refuse.
- **Post-hoc grounding:** bracketed citation ids must map to the retrieved set (`rag/grounding.py`).
- **pgvector persistence:** `make ingest` loads manifest chunks + embeddings; pipeline prefers Postgres when populated, else in-memory fallback.
- **Human review flags:** low-confidence classifications always escalate.
- **Schema validation:** Pydantic models at every agent boundary.
- **Audit log:** each pipeline step records start/end status for debugging and demos.

## Next implementation steps

1. Human-in-loop review UI (approve / edit / reject draft sections)
2. Expand eval suite toward 30+ scenarios and CI reporting
3. Classifier tuning + richer audit/event logging for demos
