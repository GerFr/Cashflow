#!/usr/bin/env python3
"""Validate the ontology, the SHACL shapes and all connector definitions.

Checks (all must pass in CI):
  1. Every Turtle file parses; every cf: term used anywhere is declared in
     ontology/cashflow.ttl; every declared term has English and German labels
     and an English definition.
  2. The default category scheme and the example data conform to the shapes
     (no violations, no warnings).
  3. Every ex:bad-* resource in ontology/examples/invalid/ is reported.
  4. The SPARQL queries in ontology/queries/ run and return the expected
     results on the example data (regression test of the metric semantics).
  5. Every connector definition validates against the JSON Schema, has at
     least one fixture, reproduces its golden output (expected.json) and emits
     RDF that conforms to the shapes.
  6. Lastenheft features and Pflichtenheft requirements are mapped to the same
     milestones in docs/ROADMAP.md, and the traceability matrix links every
     feature to requirements that deliver it (and vice versa).

Usage:
  python tools/validate.py                 # run all checks
  python tools/validate.py --update-golden # rewrite connector expected.json files
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from decimal import Decimal
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator
from pyshacl import validate as shacl_validate
from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS

sys.path.insert(0, str(Path(__file__).resolve().parent))
import connector_ref

ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = ROOT / "ontology"
CONNECTORS = ROOT / "connectors"
CF = Namespace("https://gerfr.github.io/Cashflow/ontology/cashflow#")
SH = Namespace("http://www.w3.org/ns/shacl#")
EX = "https://example.org/cashflow-demo/"

DECLARATION_TYPES = {OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty, OWL.AnnotationProperty, OWL.NamedIndividual}

failures: list[str] = []


def check(condition: bool, message: str) -> bool:
    if not condition:
        failures.append(message)
        print(f"  FAIL {message}")
    return condition


def load(*paths: Path) -> Graph:
    g = Graph()
    for p in paths:
        g.parse(p, format="turtle")
    return g


def shacl(data: Graph, shapes: Graph, ontology: Graph) -> Graph:
    _, results, _ = shacl_validate(
        data,
        shacl_graph=shapes,
        ont_graph=ontology,
        inference="rdfs",
        abort_on_first=False,
        allow_warnings=True,
        meta_shacl=False,
    )
    return results


def report(results: Graph) -> list[tuple[str, str, str]]:
    rows = []
    for r in results.subjects(RDF.type, SH.ValidationResult):
        rows.append(
            (
                str(results.value(r, SH.resultSeverity)).rsplit("#", 1)[-1],
                str(results.value(r, SH.focusNode)),
                str(results.value(r, SH.resultMessage)),
            )
        )
    return sorted(rows)


# --- 1. Ontology lint -----------------------------------------------------------------


def lint_ontology(ontology: Graph) -> None:
    print("[1] ontology lint")
    declared = {
        s for s, o in ontology.subject_objects(RDF.type) if o in DECLARATION_TYPES and str(s).startswith(str(CF))
    }
    check(len(declared) > 50, f"expected more than 50 cf: declarations, found {len(declared)}")
    for term in sorted(declared):
        langs = {lit.language for lit in ontology.objects(term, RDFS.label)}
        check({"en", "de"} <= langs, f"{term} lacks an English or German rdfs:label")
        defs = {lit.language for lit in ontology.objects(term, SKOS.definition)}
        check("en" in defs, f"{term} lacks an English skos:definition")

    used: dict[str, set[str]] = {}
    files = [*ONTOLOGY.rglob("*.ttl"), *ONTOLOGY.rglob("*.rq")]
    pattern = re.compile(r"\bcf:([A-Za-z][A-Za-z0-9]*)")
    for f in files:
        for name in pattern.findall(f.read_text(encoding="utf-8")):
            used.setdefault(name, set()).add(f.relative_to(ROOT).as_posix())
    for f in [CONNECTORS / "schema" / "connector.schema.json"]:
        for kind in json.loads(f.read_text(encoding="utf-8"))["properties"]["account_kind"]["enum"]:
            used.setdefault(kind, set()).add(f.relative_to(ROOT).as_posix())
    for name, where in sorted(used.items()):
        check(CF[name] in declared, f"cf:{name} is used in {sorted(where)} but not declared in cashflow.ttl")
    print(f"  {len(declared)} declared terms, {len(used)} distinct terms used")


# --- 2./3. SHACL ----------------------------------------------------------------------


def validate_examples(ontology: Graph, shapes: Graph, categories: Graph) -> None:
    print("[2] SHACL: categories and example data")
    for label, data in [
        ("categories.ttl", categories),
        ("examples/example-data.ttl", categories + load(ONTOLOGY / "examples" / "example-data.ttl")),
    ]:
        rows = report(shacl(data, shapes, ontology))
        check(not rows, f"{label} does not conform: {rows}")
        print(f"  {label}: {'ok' if not rows else f'{len(rows)} results'}")

    print("[3] SHACL: negative tests")
    for path in sorted((ONTOLOGY / "examples" / "invalid").glob("*.ttl")):
        data = categories + load(path)
        flagged = {focus for _, focus, _ in report(shacl(data, shapes, ontology))}
        bad = {str(s) for s in data.subjects() if isinstance(s, URIRef) and str(s).startswith(EX + "bad-")}
        missed = sorted(bad - flagged)
        check(not missed, f"{path.name}: deliberate errors not detected for {missed}")
        print(f"  {path.name}: {len(bad) - len(missed)}/{len(bad)} deliberate errors detected")


# --- 4. Queries -------------------------------------------------------------------------

EXPECTED_QUERY_RESULTS = {
    # Period bubble input for October 2026 (see example-data.ttl).
    "spend-by-top-category.rq": {
        "Housing": Decimal("955.99"),  # rent + household split from the REWE receipt
        "Health": Decimal("23.80"),
        "Subscriptions & communication": Decimal("19.99"),
        "Food & drink": Decimal("15.61"),  # groceries split only
        "Shopping": Decimal("4.49"),  # drugstore split
    },
    "tax-year-report.rq": {
        "Medical expenses": Decimal("23.80"),
    },
}


def run_queries(ontology: Graph, categories: Graph) -> None:
    print("[4] SPARQL queries on example data")
    data = ontology + categories + load(ONTOLOGY / "examples" / "example-data.ttl")
    for path in sorted((ONTOLOGY / "queries").glob("*.rq")):
        rows = list(data.query(path.read_text(encoding="utf-8")))
        check(len(rows) > 0, f"{path.name} returned no rows")
        expected = EXPECTED_QUERY_RESULTS.get(path.name)
        if expected is not None:
            got = {str(r[1]): Decimal(str(r[2])) for r in rows}
            check(got == expected, f"{path.name}: expected {expected}, got {got}")
        print(f"  {path.name}: {len(rows)} rows")


# --- 5. Connectors ----------------------------------------------------------------------


def validate_connectors(ontology: Graph, shapes: Graph, update_golden: bool) -> None:
    print("[5] connectors")
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
                check(actual == expected, f"{name}: output differs from expected.json")

            rows = report(shacl(connector_ref.to_rdf(result, definition, inputs[0].name), shapes, ontology))
            check(not rows, f"{name}: emitted RDF does not conform: {rows}")
            print(f"  {name}: {len(result.transactions)} transactions, RDF {'ok' if not rows else 'INVALID'}")


# --- 6. Lastenheft <-> Pflichtenheft <-> roadmap ----------------------------------------

DOCS = ROOT / "docs"
REQ_ID = re.compile(r"\b(?:[A-Z]{3}-\d{2}|D-\d{2})\b")
FEATURE_ID = re.compile(r"\bLF-[A-Z]{3}-\d{2}\b")
MILESTONE_KEY = re.compile(r"M\d|post|won't")


def cells(line: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip())[1:-1]]


def table_rows(text: str, width: int) -> list[list[str]]:
    return [row for row in (cells(line) for line in text.splitlines() if line.startswith("|")) if len(row) == width]


def milestones(value: str) -> set[str]:
    m = re.fullmatch(r"M(\d)\s*[\u2013-]\s*M(\d)", value)
    if m:
        return {f"M{i}" for i in range(int(m.group(1)), int(m.group(2)) + 1)}
    return {value}


def milestone_index(text: str, ids: re.Pattern[str]) -> dict[str, set[str]]:
    index: dict[str, set[str]] = {}
    for key, listed in table_rows(text, 2):
        if MILESTONE_KEY.fullmatch(key):
            for i in ids.findall(listed):
                index.setdefault(i, set()).add(key)
    return index


def section_lists(roadmap: str, label: str, ids: re.Pattern[str]) -> dict[str, set[str]]:
    """IDs listed per roadmap milestone section after a bold label such as '**Delivers:**'."""
    out: dict[str, set[str]] = {}
    for section in re.split(r"\n## ", roadmap):
        m = re.match(r"(M\d) — |After 1\.0", section)
        line = re.search(rf"^\*\*{re.escape(label)}\*\*(.*)$", section, re.MULTILINE)
        if m and line:
            out[m.group(1) or "post"] = set(ids.findall(line.group(1)))
    return out


def compare_index(planned: dict[str, set[str]], index: dict[str, set[str]], source: str) -> None:
    for i, ms in sorted(planned.items()):
        got = index.get(i, set())
        check(
            bool(got) and got <= ms and (len(ms) > 1 or got == ms),
            f"{i}: {source} says {sorted(ms)}, roadmap index says {sorted(got)}",
        )
    for i in sorted(set(index) - set(planned)):
        check(False, f"{i} is in the roadmap index but not defined in the {source}")


def compare_sections(sections: dict[str, set[str]], index: dict[str, set[str]], label: str) -> None:
    for ms, listed in sections.items():
        expected = {i for i, s in index.items() if ms in s}
        check(listed == expected, f"ROADMAP {ms} '{label}': {sorted(listed ^ expected)} differ from the index")


def check_docs() -> None:
    print("[6] Lastenheft <-> Pflichtenheft <-> roadmap")
    lastenheft = (DOCS / "LASTENHEFT.md").read_text(encoding="utf-8")
    spec = (DOCS / "SPECIFICATION.md").read_text(encoding="utf-8")
    roadmap = (DOCS / "ROADMAP.md").read_text(encoding="utf-8")

    features: dict[str, set[str]] = {}
    for row in table_rows(lastenheft, 6):
        if FEATURE_ID.fullmatch(row[0]):
            check(row[0] not in features, f"feature {row[0]} defined twice in LASTENHEFT.md")
            features[row[0]] = {row[4]}
    requirements: dict[str, set[str]] = {}
    for row in table_rows(spec, 4):
        if REQ_ID.fullmatch(row[0]) and row[2] in {"M", "S", "C", "W"}:
            check(row[0] not in requirements, f"requirement {row[0]} defined twice in SPECIFICATION.md")
            requirements[row[0]] = {"won't"} if row[2] == "W" else milestones(row[3])

    # Roadmap: feature index, requirement index and the per-milestone lists must agree.
    feature_part, requirement_part = roadmap.split("## Feature → milestone index", 1)[1].split(
        "## Requirement → milestone index", 1
    )
    feature_index = milestone_index(feature_part, FEATURE_ID)
    requirement_index = milestone_index(requirement_part, REQ_ID)
    compare_index(features, feature_index, "Lastenheft")
    compare_index(requirements, requirement_index, "Pflichtenheft")
    compare_sections(section_lists(roadmap, "Delivers:", FEATURE_ID), feature_index, "Delivers")
    compare_sections(section_lists(roadmap, "Requirements (Pflichtenheft):", REQ_ID), requirement_index, "Requirements")

    # Lastenheft section 7 summarises features per milestone with ranges such as "IMP-01…07".
    summary = lastenheft.split("## 7. Milestones", 1)[1].split("## 8.", 1)[0]
    for row in table_rows(summary, 4):
        ms = row[0].strip("*")
        if MILESTONE_KEY.fullmatch(ms):
            listed = {
                f"LF-{area}-{n:02d}"
                for area, first, last in re.findall(r"([A-Z]{3})-(\d{2})(?:…(\d{2}))?", row[2])
                for n in range(int(first), int(last or first) + 1)
            }
            expected = {f for f, s in features.items() if ms in s}
            check(listed == expected, f"LASTENHEFT section 7, {ms}: {sorted(listed ^ expected)} differ")

    # Traceability matrix (Pflichtenheft section 17): complete in both directions.
    trace = {
        f: set(REQ_ID.findall(reqs))
        for f, reqs in table_rows(spec.split("## 17. Traceability", 1)[1], 2)
        if FEATURE_ID.fullmatch(f)
    }
    for f, ms in sorted(features.items()):
        reqs = trace.get(f, set())
        known = reqs & set(requirements)
        check(bool(reqs), f"{f} has no requirements in the traceability matrix")
        check(known == reqs, f"{f}: unknown requirements {sorted(reqs - known)}")
        delivered = set().union(*(requirements[r] for r in known)) if known else set()
        check(ms <= delivered, f"{f} ({min(ms)}) is not delivered by any of its requirements {sorted(delivered)}")
    for f in sorted(set(trace) - set(features)):
        check(False, f"traceability matrix lists unknown feature {f}")
    traced = set().union(*trace.values()) if trace else set()
    untraced = sorted(r for r, ms in requirements.items() if ms != {"won't"} and r not in traced)
    check(not untraced, f"requirements not traced to any Lastenheft feature: {untraced}")
    print(f"  {len(features)} features and {len(requirements)} requirements traced and mapped to milestones")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--update-golden", action="store_true", help="rewrite connector expected.json files")
    args = parser.parse_args()

    ontology = load(ONTOLOGY / "cashflow.ttl")
    shapes = load(ONTOLOGY / "shapes.ttl")
    categories = load(ONTOLOGY / "categories.ttl")

    lint_ontology(ontology)
    validate_examples(ontology, shapes, categories)
    run_queries(ontology, categories)
    validate_connectors(ontology, shapes, args.update_golden)
    check_docs()

    if failures:
        print(f"\n{len(failures)} check(s) failed")
        return 1
    print("\nall checks passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
