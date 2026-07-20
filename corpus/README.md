# Corpus

Public-education digests used by Intake Desk RAG. These are **attributed educational summaries for portfolio demos**, not scraped copies of copyrighted pamphlets and not legal advice.

## Layout

- `manifest.yaml` — document metadata (`id`, `source_url`, `matter_types`, `jurisdiction`, `topics`, …)
- `raw/` — plain-text digests referenced by `local_path`

## Sourcing rules

1. Prefer clearly public consumer-education sources (e.g. FTC consumer pages) for federal debt topics.
2. For Oregon housing self-help, use attributed digests pointing at canonical pages such as [Oregon Law Help](https://oregonlawhelp.org/) rather than pasting proprietary text.
3. Never add client data, case files, or firm work product.
4. Keep a short disclaimer at the top of every digest.
5. After adding or editing docs, re-ingest embeddings:

```bash
make ingest
```

## Topic matrix (Phase 1)

| Matter            | Approx. docs | Examples                                                      |
| ----------------- | ------------ | ------------------------------------------------------------- |
| `tenant_housing`  | 12           | notices, habitability, lockouts, FED process, deposits        |
| `consumer_debt`   | 10           | collection comms, validation, lawsuits, medical debt          |
| `benefits_denial` | 7            | notice anatomy, appeals, overpayments, SNAP/Medicaid overview |

## Adding a document

1. Write `corpus/raw/<id>.txt` (several hundred words; chunk-friendly paragraphs).
2. Add an entry to `manifest.yaml` with `matter_types`, `jurisdiction`, `source_url`, `topics`, `last_updated`, `license_note`.
3. Run `make ingest` (requires Docker Postgres + `OPENAI_API_KEY`).
4. Add or update an eval scenario under `eval/scenarios/` when the topic should be regression-tested.
