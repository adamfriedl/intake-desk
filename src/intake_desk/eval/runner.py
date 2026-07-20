"""Golden-scenario eval runner for Intake Desk."""

from __future__ import annotations

import argparse
import asyncio
from dataclasses import dataclass
from pathlib import Path

import yaml

from intake_desk.config import get_settings
from intake_desk.orchestrator.pipeline import IntakePipeline
from intake_desk.rag.grounding import extract_citation_ids
from intake_desk.schemas.models import PipelineResult


@dataclass
class Scenario:
    name: str
    input: str
    expected: dict


def load_scenarios(directory: Path) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for path in sorted(directory.glob("*.yaml")):
        with path.open(encoding="utf-8") as handle:
            data = yaml.safe_load(handle) or {}
        scenarios.append(
            Scenario(
                name=path.stem,
                input=data["input"],
                expected=data.get("expected", {}),
            )
        )
    return scenarios


def evaluate_scenario(result: PipelineResult, expected: dict) -> list[str]:
    failures: list[str] = []

    expected_type = expected.get("matter_type")
    if expected_type and result.classification.matter_type.value != expected_type:
        failures.append(
            f"classification expected {expected_type}, got {result.classification.matter_type.value}"
        )

    if expected.get("must_request_human_review") and not result.classification.human_review_required:
        failures.append("expected human_review_required=true")

    if expected.get("must_refuse") and not result.refused:
        failures.append("expected refused=true")

    if expected.get("must_cite_sources") and not result.citations and not result.refused:
        failures.append("expected citations or explicit refusal")

    if expected.get("must_cite_sources") and result.answer and not result.refused:
        cited = extract_citation_ids(result.answer)
        allowed = {citation.chunk_id for citation in result.citations}
        if not cited:
            failures.append("expected bracketed citations in answer")
        unknown = [cid for cid in cited if cid not in allowed]
        if unknown:
            failures.append(f"ungrounded citation ids: {', '.join(unknown)}")

    forbidden_claims = expected.get("forbidden_claims", [])
    answer = (result.answer or "").lower()
    for phrase in forbidden_claims:
        if phrase.lower() in answer:
            failures.append(f"forbidden phrase present: {phrase}")

    return failures


async def run_eval(scenario_dir: Path) -> int:
    settings = get_settings()
    pipeline = IntakePipeline(settings)
    scenarios = load_scenarios(scenario_dir)

    if not scenarios:
        print(f"No scenarios found in {scenario_dir}")
        return 1

    passed = 0
    for scenario in scenarios:
        result = await pipeline.run(scenario.input, include_draft=False)
        failures = evaluate_scenario(result, scenario.expected)
        if failures:
            print(f"FAIL {scenario.name}")
            for failure in failures:
                print(f"  - {failure}")
        else:
            print(f"PASS {scenario.name}")
            passed += 1

    total = len(scenarios)
    print(f"\n{passed}/{total} scenarios passed")
    return 0 if passed == total else 1


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Intake Desk golden scenarios")
    parser.add_argument(
        "--scenarios",
        type=Path,
        default=Path("eval/scenarios"),
        help="Directory containing scenario YAML files",
    )
    args = parser.parse_args()
    raise SystemExit(asyncio.run(run_eval(args.scenarios)))


if __name__ == "__main__":
    main()
