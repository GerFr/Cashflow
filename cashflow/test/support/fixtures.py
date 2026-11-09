from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cashflow.connectors.conformance import fixture_cases, fixture_input
from cashflow.connectors.registry import load_registry
from cashflow.utils.config import get_settings

CONNECTORS_DIR = get_settings().connectors_dir
REGISTRY = load_registry(CONNECTORS_DIR)

# (connector id, fixture case directory) for every golden fixture
CASES: list[tuple[str, Path]] = [
    (connector_id, case)
    for connector_id in REGISTRY.definitions
    for case in fixture_cases(CONNECTORS_DIR, connector_id)
]


def case_id(value: Any) -> str:
    return value.name if isinstance(value, Path) else str(value)


def read_case(case: Path) -> tuple[bytes, dict[str, Any]]:
    """Input bytes and golden output of one fixture case."""
    expected = json.loads((case / "expected.json").read_text(encoding="utf-8"))
    return fixture_input(case).read_bytes(), expected
