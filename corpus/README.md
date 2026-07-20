# Corpus

Public-education digests used by Intake Desk RAG. These are **attributed educational summaries for portfolio demos**, not scraped copies of copyrighted pamphlets and not legal advice.

## Layout

- `manifest.yaml` — document metadata (`id`, `source_url`, `matter_types`, `jurisdiction`, `topics`, …)
- `raw/` — plain-text digests referenced by `local_path`

## Current coverage (Phase 1+)

| Matter                | Docs | Notes                                                                     |
| --------------------- | ---- | ------------------------------------------------------------------------- |
| `tenant_housing`      | 16   | Oregon notices, lockouts, deposits, DV housing, mobile homes, pests, rent |
| `consumer_debt`       | 13   | FTC-style collection + validation, lawsuits, bankruptcy basics, ID theft  |
| `benefits_denial`     | 10   | SNAP/Medicaid, SSI/SSDI, unemployment, CHIP, appeals, overpayments        |
| out-of-scope referral | 2    | Criminal / immigration (refusal contrast)                                 |

~41 documents, ~30k words. Condensed FTC excerpts use `source_type: primary_public` where noted.

## Sourcing rules

1. Prefer clearly public consumer-education sources (e.g. FTC consumer pages) for federal debt topics.
2. For Oregon housing self-help, use attributed digests pointing at canonical pages such as [Oregon Law Help](https://oregonlawhelp.org/) rather than pasting proprietary text.
3. Never add client data, case files, or firm work product.
4. Keep a short disclaimer at the top of every digest.
5. After adding or editing docs, re-ingest embeddings:

```bash
make ingest
```

## Adding a document

1. Write `corpus/raw/<id>.txt` (700–1200 words preferred; chunk-friendly paragraphs).
2. Add an entry to `manifest.yaml` with `matter_types`, `jurisdiction`, `source_url`, `topics`, `last_updated`, `license_note`.
3. Run `make ingest` (requires Docker Postgres + `OPENROUTER_API_KEY`).
4. Add or update an eval scenario under `eval/scenarios/` when the topic should be regression-tested.
