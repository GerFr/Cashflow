"""Loads the connectors and picks the one that matches a file.

Two kinds share one interface: declarative connectors (YAML definitions in ``connectors/definitions``,
run by the interpreter in ``engine.py``) and code connectors (Python modules in this package) for formats
the DSL can't describe, such as PDF statements.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Protocol

import yaml
from jsonschema import Draft202012Validator

from cashflow.connectors.engine import Interpreter, ParseResult


class DefinitionError(Exception):
    """A connector definition is invalid."""


class Connector(Protocol):
    id: str
    name: str
    version: str
    status: str
    institution: str
    filename_patterns: tuple[str, ...]

    def matches(self, data: bytes) -> bool: ...

    def parse(self, data: bytes) -> ParseResult: ...


@dataclass(frozen=True)
class DeclarativeConnector:
    definition: dict[str, Any]

    @property
    def id(self) -> str:
        return self.definition["id"]

    @property
    def name(self) -> str:
        return self.definition["name"]

    @property
    def version(self) -> str:
        return self.definition["version"]

    @property
    def status(self) -> str:
        return self.definition["status"]

    @property
    def institution(self) -> str:
        return self.definition["institution"]["name"]

    @property
    def filename_patterns(self) -> tuple[str, ...]:
        return tuple(self.definition["detect"].get("filename_patterns", []))

    def matches(self, data: bytes) -> bool:
        return Interpreter(self.definition).matches(data)

    def parse(self, data: bytes) -> ParseResult:
        return Interpreter(self.definition).parse(data)


def code_connectors() -> list[Connector]:
    from cashflow.connectors.traderepublic import TradeRepublicStatement

    return [TradeRepublicStatement()]


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
    connectors: dict[str, Connector] = field(default_factory=dict)

    def __len__(self) -> int:
        return len(self.connectors)

    def get(self, connector_id: str) -> Connector | None:
        return self.connectors.get(connector_id)

    def detect(self, data: bytes, filename: str) -> Connector | None:
        """The connector that recognises the file's content; file name patterns break ties."""
        candidates = [c for c in self.connectors.values() if c.matches(data)]
        if len(candidates) > 1:
            named = [c for c in candidates if any(fnmatch(filename, p) for p in c.filename_patterns)]
            candidates = named or candidates
        return candidates[0] if candidates else None


def load_registry(connectors_dir: Path) -> Registry:
    validator = schema_validator(connectors_dir)
    connectors: dict[str, Connector] = {}
    for path in definition_files(connectors_dir):
        definition = yaml.safe_load(path.read_text(encoding="utf-8"))
        errors = definition_errors(validator, path, definition)
        if errors:
            raise DefinitionError(f"{path.name}: {'; '.join(errors)}")
        connectors[definition["id"]] = DeclarativeConnector(definition)
    for connector in code_connectors():
        if connector.id in connectors:
            raise DefinitionError(f"code connector {connector.id!r} clashes with a definition")
        connectors[connector.id] = connector
    return Registry(connectors)
