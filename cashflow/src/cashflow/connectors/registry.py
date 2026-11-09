"""Loads the connector definitions and picks the one that matches a file."""

from __future__ import annotations

import json
from dataclasses import dataclass
from fnmatch import fnmatch
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

from cashflow.connectors.engine import Interpreter


class DefinitionError(Exception):
    """A connector definition is invalid."""


def schema_validator(connectors_dir: Path) -> Draft202012Validator:
    schema = json.loads((connectors_dir / "schema" / "connector.schema.json").read_text(encoding="utf-8"))
    return Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)


def definition_files(connectors_dir: Path) -> list[Path]:
    return sorted((connectors_dir / "definitions").glob("*.yaml"))


def definition_errors(validator: Draft202012Validator, path: Path, definition: Any) -> list[str]:
    errors = [
        f"{'/'.join(map(str, e.path)) or '<root>'}: {e.message}"
        for e in sorted(validator.iter_errors(definition), key=lambda e: list(e.path))
    ]
    if not errors and path.stem != definition["id"]:
        errors.append(f"file name must equal id {definition['id']!r}")
    return errors


@dataclass(frozen=True)
class Registry:
    definitions: dict[str, dict[str, Any]]

    def __len__(self) -> int:
        return len(self.definitions)

    def get(self, connector_id: str) -> dict[str, Any] | None:
        return self.definitions.get(connector_id)

    def detect(self, data: bytes, filename: str) -> dict[str, Any] | None:
        """The definition whose detection columns are in the file's header; file name patterns break ties."""
        candidates = [d for d in self.definitions.values() if Interpreter(d).matches(data)]
        if len(candidates) > 1:
            named = [
                d for d in candidates if any(fnmatch(filename, p) for p in d["detect"].get("filename_patterns", []))
            ]
            candidates = named or candidates
        return candidates[0] if candidates else None


def load_registry(connectors_dir: Path) -> Registry:
    validator = schema_validator(connectors_dir)
    definitions: dict[str, dict[str, Any]] = {}
    for path in definition_files(connectors_dir):
        definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = definition_errors(validator, path, definition)
        if errors:
            raise DefinitionError(f"{path.name}: {'; '.join(errors)}")
        definitions[definition["id"]] = definition
    return Registry(definitions)
