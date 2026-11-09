from __future__ import annotations

import shutil

import pytest
from support.fixtures import CASES, CONNECTORS_DIR, REGISTRY, case_id, read_case

from cashflow.connectors.registry import DefinitionError, load_registry


@pytest.mark.parametrize(("connector_id", "case"), CASES, ids=case_id)
def test_detects_the_fixture_format(connector_id, case):
    content, _ = read_case(case)
    assert REGISTRY.detect(content, "export.csv")["id"] == connector_id


@pytest.mark.parametrize(
    "content",
    [b"", b"\xff\xfe\x00garbage", b"Datum;Betrag\n01.01.2026;1,00\n", b'"unterminated'],
    ids=["empty", "binary", "unknown-header", "broken-quote"],
)
def test_unknown_files_are_not_detected(content):
    assert REGISTRY.detect(content, "export.csv") is None


def test_filename_patterns_break_ties():
    definition = REGISTRY.get("de.dkb.csv-2023")
    twin = {**definition, "id": "zz.twin", "detect": {**definition["detect"], "filename_patterns": ["twin-*.csv"]}}
    registry = type(REGISTRY)({**REGISTRY.definitions, "zz.twin": twin})
    content, _ = read_case(next(case for cid, case in CASES if cid == "de.dkb.csv-2023"))

    assert registry.detect(content, "twin-2026.csv")["id"] == "zz.twin"
    assert registry.detect(content, "other.csv")["id"] == "de.dkb.csv-2023"


def test_invalid_definition_is_rejected(tmp_path):
    shutil.copytree(CONNECTORS_DIR / "schema", tmp_path / "schema")
    (tmp_path / "definitions").mkdir()
    source = (CONNECTORS_DIR / "definitions" / "de.dkb.csv-2023.yaml").read_text(encoding="utf-8")
    (tmp_path / "definitions" / "wrong-name.yaml").write_text(source, encoding="utf-8")

    with pytest.raises(DefinitionError, match="file name must equal id"):
        load_registry(tmp_path)
