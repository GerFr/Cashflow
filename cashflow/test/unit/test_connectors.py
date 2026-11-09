"""Connector conformance suite: definitions are valid and every connector reproduces its golden fixtures."""

from __future__ import annotations

import pytest
import yaml
from support.fixtures import CASES, CONNECTORS_DIR, REGISTRY, case_id, read_case

from cashflow.connectors.conformance import actual_output, fixture_cases
from cashflow.connectors.registry import definition_errors, definition_files, schema_validator

DEFINITION_FILES = definition_files(CONNECTORS_DIR)


def test_there_are_definitions():
    assert DEFINITION_FILES


@pytest.mark.parametrize("path", DEFINITION_FILES, ids=lambda p: p.stem)
def test_definition_is_valid(path):
    definition = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert definition_errors(schema_validator(CONNECTORS_DIR), path, definition) == []


@pytest.mark.parametrize("connector_id", sorted(REGISTRY.connectors))
def test_every_connector_has_fixtures(connector_id):
    assert fixture_cases(CONNECTORS_DIR, connector_id), f"no fixtures in connectors/fixtures/{connector_id}/"


@pytest.mark.parametrize(("connector_id", "case"), CASES, ids=case_id)
def test_fixture_reproduces_expected_json(connector_id, case):
    _, expected = read_case(case)
    actual = actual_output(REGISTRY.get(connector_id), case)
    assert actual == expected, "output differs; run `uv run update-golden` and review"
