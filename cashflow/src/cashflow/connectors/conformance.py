"""Connector conformance suite: every definition reproduces its golden fixtures.

The checks run in ``test/unit/test_connectors.py``. After changing a definition, regenerate the
golden files and review every changed value:

    uv run update-golden
    git diff ../connectors/fixtures/
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cashflow.connectors.registry import Connector, load_registry
from cashflow.utils.config import get_settings


def fixture_cases(connectors_dir: Path, connector_id: str) -> list[Path]:
    return sorted(p for p in (connectors_dir / "fixtures" / connector_id).glob("*/") if p.is_dir())


def fixture_input(case: Path) -> Path:
    inputs = sorted(case.glob("input.*"))
    if len(inputs) != 1:
        raise ValueError(f"{case}: expected exactly one input.* file, found {len(inputs)}")
    return inputs[0]


def actual_output(connector: Connector, case: Path) -> dict[str, Any]:
    return connector.parse(fixture_input(case).read_bytes()).to_json()


def write_golden(connector: Connector, case: Path) -> None:
    text = json.dumps(actual_output(connector, case), indent=2, ensure_ascii=False) + "\n"
    (case / "expected.json").write_text(text, encoding="utf-8")


def main() -> None:
    connectors_dir = get_settings().connectors_dir
    for connector_id, connector in load_registry(connectors_dir).connectors.items():
        for case in fixture_cases(connectors_dir, connector_id):
            write_golden(connector, case)
            print(f"{connector_id}/{case.name}: expected.json written")


if __name__ == "__main__":
    main()
