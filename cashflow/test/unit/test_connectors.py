"""Connector conformance suite: definitions are valid and reproduce their golden fixtures."""

from __future__ import annotations

import pytest
import yaml
from support.fixtures import CASES, CONNECTORS_DIR, case_id, read_case

from cashflow.connectors.conformance import actual_output, fixture_cases
from cashflow.connectors.registry import definition_errors, definition_files, schema_validator

DEFINITION_FILES = definition_files(CONNECTORS_DIR)


def test_there_are_definitions():
    assert DEFINITION_FILES


@pytest.mark.parametrize("path", DEFINITION_FILES, ids=lambda p: p.stem)
def test_definition_is_valid_and_has_fixtures(path):
    definition = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert definition_errors(schema_validator(CONNECTORS_DIR), path, definition) == []
    assert fixture_cases(CONNECTORS_DIR, definition["id"]), f"no fixtures in connectors/fixtures/{definition['id']}/"


@pytest.mark.parametrize(("connector_id", "case"), CASES, ids=case_id)
def test_fixture_reproduces_expected_json(connector_id, case):
    definition = yaml.safe_load((CONNECTORS_DIR / "definitions" / f"{connector_id}.yaml").read_text(encoding="utf-8"))
    _, expected = read_case(case)
    assert actual_output(definition, case) == expected, "output differs; run `uv run update-golden` and review"
