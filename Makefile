.PHONY: install dev db up api test eval lint ingest

install:
	python3 -m venv --clear .venv
	.venv/bin/pip install -e ".[dev]"

dev: install
	cp -n .env.example .env || true

db:
	docker compose up -d db

up: db
	.venv/bin/uvicorn intake_desk.api.main:app --reload --app-dir src

api:
	.venv/bin/uvicorn intake_desk.api.main:app --reload --app-dir src

ingest: db
	.venv/bin/python -m intake_desk.rag.ingest

test:
	.venv/bin/pytest -m "not integration"

test-integration:
	.venv/bin/pytest -m integration

eval:
	.venv/bin/python eval/runner.py

lint:
	.venv/bin/ruff check src tests
