#!/usr/bin/env python3
"""Check every connector definition against its golden fixtures.

For each file in connectors/definitions/:
  * it validates against connectors/schema/connector.schema.json,
  * its file name equals its id,
  * it has at least one fixture, and the reference interpreter
    (tools/connector_ref.py) reproduces each fixture's expected.json.

Usage:
  python tools/validate.py                 # run the checks
  python tools/validate.py --update-golden # rewrite expected.json files (review the diff!)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

sys.path.insert(0, str(Path(__file__).resolve().parent))
import connector_ref

CONNECTORS = Path(__file__).resolve().parents[1] / "connectors"

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)
        print(f"  FAIL {message}")
    return condition


def validate_connectors(update_golden: bool) -> None:
    schema = json.loads((CONNECTORS / "schema" / "connector.schema.json").read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    for path in sorted((CONNECTORS / "definitions").glob("*.yaml")):
        definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = sorted(validator.iter_errors(definition), key=lambda e: list(e.path))
        if not check(not errors, f"{path.name}: schema errors: {[f'{list(e.path)}: {e.message}' for e in errors]}"):
            continue
        check(path.stem == definition["id"], f"{path.name}: file name must equal id {definition['id']!r}")

        fixtures = sorted(p for p in (CONNECTORS / "fixtures" / definition["id"]).glob("*/") if p.is_dir())
        check(bool(fixtures), f"{definition['id']}: no fixtures in connectors/fixtures/{definition['id']}/")
        for fixture in fixtures:
            inputs = sorted(fixture.glob("input.*"))
            if not check(len(inputs) == 1, f"{fixture}: expected exactly one input.* file"):
                continue
            name = f"{definition['id']}/{fixture.name}"
            try:
                result = connector_ref.run(definition, inputs[0])
            except connector_ref.ConnectorError as exc:
                check(False, f"{name}: {exc}")
                continue
            actual = result.to_json()
            golden = fixture / "expected.json"
            if update_golden:
                golden.write_text(json.dumps(actual, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
                print(f"  {name}: golden file written")
            elif check(golden.exists(), f"{name}: expected.json missing (run with --update-golden)"):
                expected = json.loads(golden.read_text(encoding="utf-8"))
                if check(actual == expected, f"{name}: output differs from expected.json"):
                    print(f"  {name}: {len(result.transactions)} transactions ok")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update-golden", action="store_true", help="rewrite connector expected.json files")
    args = parser.parse_args()

    validate_connectors(args.update_golden)

    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
