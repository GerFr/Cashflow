"""Reference interpreter for the declarative connector DSL (dsl_version 0.1).

This module is an *executable specification*: it defines precisely how a
connector definition (connectors/definitions/*.yaml) turns an export file into
canonical transaction records and RDF. CI runs it over every fixture.

The app's Kotlin connector engine must produce identical canonical JSON for
every fixture in ``connectors/fixtures`` (the connector conformance suite).
"""

from __future__ import annotations

import csv
import hashlib
import io
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import PROV, RDF, RDFS, XSD

CF = Namespace("https://gerfr.github.io/Cashflow/ontology/cashflow#")

ENCODINGS = {
    "utf-8": "utf-8",
    "utf-8-sig": "utf-8-sig",
    "windows-1252": "cp1252",
    "iso-8859-1": "latin-1",
    "iso-8859-15": "iso8859_15",
}

# Canonical record layout; the order is part of the conformance contract.
RECORD_FIELDS = [
    "id",
    "fingerprint",
    "row_number",
    "account_iban",
    "account_external_id",
    "booking_date",
    "value_date",
    "transaction_datetime",
    "direction",
    "amount",
    "currency",
    "original_amount",
    "original_currency",
    "exchange_rate",
    "fee_amount",
    "status",
    "counterparty_name",
    "counterparty_iban",
    "counterparty_bic",
    "remittance_information",
    "booking_text",
    "creditor_id",
    "mandate_reference",
    "end_to_end_id",
    "merchant_category_code",
    "external_id",
    "related_external_id",
    "category_hint",
]

DECIMAL_FIELDS = {"amount", "original_amount", "exchange_rate", "fee_amount"}
MONEY_FIELDS = {"amount", "original_amount", "fee_amount"}
UUID_NAMESPACE = "cashflow"
CURRENCY_SYMBOLS = "€$£¥₣"


class ConnectorError(Exception):
    """Raised for malformed input; carries the 1-based physical row number."""

    def __init__(self, message: str, row: int | None = None):
        super().__init__(f"row {row}: {message}" if row else message)
        self.row = row


@dataclass
class ParseResult:
    connector_id: str
    connector_version: str
    file_sha256: str
    accounts: list[str] = field(default_factory=list)
    balances: list[dict[str, str]] = field(default_factory=list)
    transactions: list[dict[str, Any]] = field(default_factory=list)
    skipped_rows: list[int] = field(default_factory=list)
    raw_rows: dict[int, str] = field(default_factory=dict)

    def to_json(self) -> dict[str, Any]:
        return {
            "connector": {"id": self.connector_id, "version": self.connector_version},
            "file_sha256": self.file_sha256,
            "accounts": self.accounts,
            "balances": self.balances,
            "skipped_rows": self.skipped_rows,
            "transactions": self.transactions,
        }


# --- Identifiers ----------------------------------------------------------------


def uuid8(name: str) -> uuid.UUID:
    """Name-based UUIDv8 using SHA-256 (RFC 9562, section 5.8 / appendix B.2)."""
    digest = bytearray(hashlib.sha256(f"{UUID_NAMESPACE}:{name}".encode()).digest()[:16])
    digest[6] = (digest[6] & 0x0F) | 0x80  # version 8
    digest[8] = (digest[8] & 0x3F) | 0x80  # RFC 9562 variant
    return uuid.UUID(bytes=bytes(digest))


def normalize_text(value: str | None) -> str:
    return " ".join((value or "").upper().split())


def fingerprint_base(rec: dict[str, Any]) -> str:
    parts = [
        rec.get("account_iban") or rec.get("account_external_id") or "",
        rec["booking_date"],
        rec.get("value_date") or "",
        rec["direction"],
        rec["amount"],
        rec["currency"],
        rec.get("counterparty_iban") or "",
        normalize_text(rec.get("counterparty_name")),
        normalize_text(rec.get("remittance_information")),
        rec.get("end_to_end_id") or "",
        rec.get("external_id") or "",
    ]
    return "\x1f".join(parts)


# --- Value parsing -----------------------------------------------------------------


def apply_transforms(value: str, transforms: list[str]) -> str:
    for t in transforms:
        if t == "trim":
            value = value.strip()
        elif t == "collapse_whitespace":
            value = " ".join(value.split())
        elif t == "remove_spaces":
            value = re.sub(r"\s+", "", value)
        elif t == "upper":
            value = value.upper()
        elif t == "lower":
            value = value.lower()
        elif t == "strip_currency_symbol":
            value = value.strip().strip(CURRENCY_SYMBOLS).strip()
        else:
            raise ConnectorError(f"unknown transform {t!r}")
    return value


def parse_decimal(raw: str, locale: dict[str, Any]) -> Decimal:
    s = raw.strip().replace("\u00a0", "").replace("\u2212", "-")
    thousands = locale.get("thousands_separator", "")
    if thousands:
        s = s.replace(thousands, "")
    s = s.replace(locale["decimal_separator"], ".")
    if s.endswith("-"):  # trailing minus, e.g. "12,50-"
        s = "-" + s[:-1]
    s = s.replace("+", "")
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise ConnectorError(f"not a decimal: {raw!r}") from exc


def parse_date(raw: str, locale: dict[str, Any]) -> date:
    for fmt in locale["date_formats"]:
        try:
            return datetime.strptime(raw.strip(), fmt).date()
        except ValueError:
            continue
    raise ConnectorError(f"date {raw!r} matches none of {locale['date_formats']}")


def parse_datetime(raw: str, locale: dict[str, Any]) -> datetime:
    try:
        return datetime.fromisoformat(raw.strip())
    except ValueError:
        pass
    for fmt in locale["date_formats"]:
        try:
            return datetime.strptime(raw.strip(), fmt)
        except ValueError:
            continue
    raise ConnectorError(f"date-time {raw!r} not understood")


def typed(value: str, type_: str, locale: dict[str, Any]) -> Any:
    if type_ == "string":
        return value
    if type_ == "date":
        return parse_date(value, locale)
    if type_ == "datetime":
        return parse_datetime(value, locale)
    if type_ == "decimal":
        return parse_decimal(value, locale)
    raise ConnectorError(f"unknown type {type_!r}")


def format_decimal(value: Decimal, money: bool) -> str:
    if money and value.as_tuple().exponent > -2:
        value = value.quantize(Decimal("0.01"))
    return format(value, "f")


# --- Interpreter -------------------------------------------------------------------


class Interpreter:
    def __init__(self, definition: dict[str, Any]):
        self.d = definition
        self.locale = definition["locale"]

    # conditions are evaluated on raw (untransformed) cell values
    def holds(self, cond: dict[str, Any], row: dict[str, str], line: int) -> bool:
        raw = self.cell(row, cond["column"], line)
        checks = []
        if "equals" in cond:
            checks.append(raw.strip() == cond["equals"])
        if "in" in cond:
            checks.append(raw.strip() in cond["in"])
        if "matches" in cond:
            checks.append(re.search(cond["matches"], raw) is not None)
        if "empty" in cond:
            checks.append((raw.strip() == "") == cond["empty"])
        if "negative" in cond:
            negative = raw.strip() != "" and parse_decimal(raw, self.locale) < 0
            checks.append(negative == cond["negative"])
        return all(checks)

    @staticmethod
    def cell(row: dict[str, str], column: str, line: int) -> str:
        if column not in row:
            raise ConnectorError(f"column {column!r} not found in header", line)
        return row[column]

    def value(self, spec: dict[str, Any], row: dict[str, str], preamble: dict[str, Any], line: int) -> Any:
        if "cases" in spec:
            for case in spec["cases"]:
                if "when" not in case or self.holds(case["when"], row, line):
                    return self.value(case, row, preamble, line)
            return None
        if "from_preamble" in spec:
            return preamble.get(spec["from_preamble"])
        raw = spec["const"] if "const" in spec else self.cell(row, spec["column"], line)
        raw = apply_transforms(raw, spec.get("transform", []))
        if raw.strip() == "" or raw in spec.get("null_values", []):
            return None
        if "regex" in spec:
            m = re.search(spec["regex"], raw)
            if not m:
                return None
            raw = m.group(1)
        if "map" in spec:
            if raw not in spec["map"]:
                raise ConnectorError(f"value {raw!r} not in map {sorted(spec['map'])}", line)
            raw = spec["map"][raw]
        try:
            return typed(raw, spec.get("type", "string"), self.locale)
        except ConnectorError as exc:
            raise ConnectorError(str(exc), line) from exc

    def read_preamble(self, rows: list[list[str]]) -> dict[str, Any]:
        out: dict[str, Any] = {}
        for name, spec in self.d["input"].get("preamble", {}).items():
            for cells in rows:
                if cells and re.search(spec["row_matches"], cells[0]):
                    if spec["cell"] >= len(cells):
                        raise ConnectorError(f"preamble field {name!r}: cell {spec['cell']} missing")
                    raw = apply_transforms(cells[spec["cell"]], spec.get("transform", []))
                    if "regex" in spec:
                        m = re.search(spec["regex"], raw)
                        if not m:
                            raise ConnectorError(f"preamble field {name!r}: regex did not match {raw!r}")
                        raw = m.group(1)
                    out[name] = typed(raw, spec.get("type", "string"), self.locale)
                    break
        return out

    def run(self, path: Path) -> ParseResult:
        data = path.read_bytes()
        result = ParseResult(self.d["id"], self.d["version"], hashlib.sha256(data).hexdigest())
        inp = self.d["input"]
        text = data.decode(ENCODINGS[inp["encoding"]])
        physical_lines = text.splitlines()

        reader = csv.reader(io.StringIO(text, newline=""), delimiter=inp["delimiter"], quotechar=inp.get("quote", '"'))
        records: list[tuple[int, int, list[str]]] = []  # (first line, last line, cells)
        last = 0
        for cells in reader:
            records.append((last + 1, reader.line_num, cells))
            last = reader.line_num

        header_idx = self.find_header(records)
        header = [h.strip() for h in records[header_idx][2]]
        missing = [c for c in self.d["detect"]["required_columns"] if c not in header]
        if missing:
            raise ConnectorError(f"detection columns missing from header: {missing}")
        preamble = self.read_preamble([cells for _, _, cells in records[:header_idx]])

        occurrences: dict[str, int] = {}
        for first, end, cells in records[header_idx + 1 :]:
            if inp.get("skip_empty_rows", True) and all(c.strip() == "" for c in cells):
                continue
            if len(cells) < len(header) or any(c.strip() for c in cells[len(header) :]):
                raise ConnectorError(f"expected {len(header)} cells, got {len(cells)}", first)
            row = dict(zip(header, cells, strict=False))  # surplus cells are empty (checked above)
            if any(self.holds(c, row, first) for c in self.d.get("filters", {}).get("exclude_if", [])):
                result.skipped_rows.append(first)
                continue
            rec = self.record(row, preamble, first)
            base = fingerprint_base(rec)
            n = occurrences.get(base, 0)
            occurrences[base] = n + 1
            rec["fingerprint"] = hashlib.sha256(f"{base}\x1f{n}".encode()).hexdigest()
            rec["id"] = str(uuid8(f"transaction:{rec['fingerprint']}"))
            result.transactions.append({k: rec[k] for k in RECORD_FIELDS if rec.get(k) is not None})
            result.raw_rows[first] = "\n".join(physical_lines[first - 1 : end])
            account = rec.get("account_iban") or rec.get("account_external_id")
            if account and account not in result.accounts:
                result.accounts.append(account)

        if "closing_balance" in preamble and "closing_balance_date" in preamble:
            account = preamble.get("account_iban") or (result.accounts[0] if result.accounts else None)
            result.balances.append(
                {
                    "account": account,
                    "date": preamble["closing_balance_date"].isoformat(),
                    "balance": format_decimal(preamble["closing_balance"], money=True),
                }
            )
        return result

    def find_header(self, records: list[tuple[int, int, list[str]]]) -> int:
        spec = self.d["input"]["header"]
        if "row" in spec:
            return spec["row"] - 1
        wanted = spec["find_row_containing"]
        for i, (_, _, cells) in enumerate(records):
            stripped = [c.strip() for c in cells]
            if all(w in stripped for w in wanted):
                return i
        raise ConnectorError(f"no header row containing {wanted}")

    def record(self, row: dict[str, str], preamble: dict[str, Any], line: int) -> dict[str, Any]:
        rec: dict[str, Any] = {"row_number": line}
        for name, spec in self.d["fields"].items():
            rec[name] = self.value(spec, row, preamble, line)
        if rec.get("booking_date") is None or rec.get("amount") is None or rec.get("currency") is None:
            raise ConnectorError("booking_date, amount and currency are required", line)

        direction = self.d["direction"]
        if direction["mode"] == "signed_amount":
            rec["direction"] = "debit" if rec["amount"] < 0 else "credit"
        else:
            flag = self.cell(row, direction["column"], line).strip()
            if flag in direction["debit_values"]:
                rec["direction"] = "debit"
            elif flag in direction["credit_values"]:
                rec["direction"] = "credit"
            else:
                raise ConnectorError(f"unknown debit/credit indicator {flag!r}", line)
        rec["status"] = rec.get("status") or "booked"
        if rec["status"] not in ("booked", "pending"):
            raise ConnectorError(f"status must map to booked|pending, got {rec['status']!r}", line)

        for k, v in list(rec.items()):
            if isinstance(v, Decimal):
                rec[k] = format_decimal(abs(v) if k in MONEY_FIELDS else v, money=k in MONEY_FIELDS)
            elif isinstance(v, date):  # also covers datetime
                rec[k] = v.isoformat()
        return rec


def run(definition: dict[str, Any], path: Path) -> ParseResult:
    return Interpreter(definition).run(path)


# --- RDF ---------------------------------------------------------------------------


def urn(name: str) -> URIRef:
    return URIRef(f"urn:uuid:{uuid8(name)}")


def money(g: Graph, value: str, currency: str) -> BNode:
    node = BNode()
    g.add((node, RDF.type, CF.MonetaryAmount))
    g.add((node, CF.value, Literal(value, datatype=XSD.decimal)))
    g.add((node, CF.currency, Literal(currency)))
    return node


def to_rdf(result: ParseResult, definition: dict[str, Any], file_name: str) -> Graph:
    """Emit the parse result as RDF conforming to ontology/cashflow.ttl + shapes.ttl."""
    g = Graph()
    g.bind("cf", CF)
    g.bind("prov", PROV)

    connector = urn(f"connector:{result.connector_id}@{result.connector_version}")
    g.add((connector, RDF.type, CF.Connector))
    g.add((connector, RDFS.label, Literal(definition["name"])))
    g.add((connector, CF.connectorId, Literal(result.connector_id)))
    g.add((connector, CF.connectorVersion, Literal(result.connector_version)))

    source = urn(f"file:{result.file_sha256}")
    g.add((source, RDF.type, CF.SourceFile))
    g.add((source, CF.sha256, Literal(result.file_sha256)))
    g.add((source, CF.fileName, Literal(file_name)))
    g.add((source, CF.mediaType, Literal("text/csv")))

    run_node = urn(f"import:{result.file_sha256}:{result.connector_id}@{result.connector_version}")
    g.add((run_node, RDF.type, CF.ImportRun))
    g.add((run_node, PROV.used, source))
    g.add((run_node, PROV.wasAssociatedWith, connector))

    accounts: dict[str, URIRef] = {}
    currencies: dict[str, str] = {}
    for tx in result.transactions:
        key = tx.get("account_iban") or tx.get("account_external_id")
        currencies.setdefault(key, tx["currency"])
    for key in result.accounts:
        node = urn(f"account:{key}")
        accounts[key] = node
        g.add((node, RDF.type, CF[definition["account_kind"]]))
        g.add((node, RDFS.label, Literal(f"{definition['institution']['name']} …{key[-4:]}")))
        g.add((node, CF.currency, Literal(currencies.get(key, "EUR"))))
        if re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", key):
            g.add((node, CF.iban, Literal(key)))
        else:
            g.add((node, CF.externalAccountId, Literal(key)))

    for tx in result.transactions:
        t = URIRef(f"urn:uuid:{tx['id']}")
        g.add((t, RDF.type, CF.Transaction))
        g.add((t, CF.account, accounts[tx.get("account_iban") or tx.get("account_external_id")]))
        g.add((t, CF.bookingDate, Literal(tx["booking_date"], datatype=XSD.date)))
        if "value_date" in tx:
            g.add((t, CF.valueDate, Literal(tx["value_date"], datatype=XSD.date)))
        if "transaction_datetime" in tx:
            g.add((t, CF.transactionDateTime, Literal(tx["transaction_datetime"], datatype=XSD.dateTime)))
        g.add((t, CF.amount, money(g, tx["amount"], tx["currency"])))
        if "original_amount" in tx:
            g.add((t, CF.originalAmount, money(g, tx["original_amount"], tx.get("original_currency", tx["currency"]))))
        if "exchange_rate" in tx:
            g.add((t, CF.exchangeRate, Literal(tx["exchange_rate"], datatype=XSD.decimal)))
        if "fee_amount" in tx:
            g.add((t, CF.fee, money(g, tx["fee_amount"], tx["currency"])))
        g.add((t, CF.direction, CF.Debit if tx["direction"] == "debit" else CF.Credit))
        g.add((t, CF.status, CF.Booked if tx["status"] == "booked" else CF.Pending))
        for key, prop in [
            ("counterparty_name", CF.counterpartyName),
            ("counterparty_iban", CF.counterpartyIban),
            ("counterparty_bic", CF.counterpartyBic),
            ("remittance_information", CF.remittanceInformation),
            ("booking_text", CF.bookingText),
            ("creditor_id", CF.creditorId),
            ("mandate_reference", CF.mandateReference),
            ("end_to_end_id", CF.endToEndId),
            ("merchant_category_code", CF.merchantCategoryCode),
            ("external_id", CF.externalId),
            ("related_external_id", CF.relatedExternalId),
        ]:
            if key in tx:
                g.add((t, prop, Literal(tx[key])))
        g.add((t, CF.fingerprint, Literal(tx["fingerprint"])))

        record = urn(f"record:{result.file_sha256}:{tx['row_number']}")
        g.add((record, RDF.type, CF.SourceRecord))
        g.add((record, CF.sourceFile, source))
        g.add((record, CF.rowNumber, Literal(tx["row_number"], datatype=XSD.positiveInteger)))
        g.add((record, CF.rawContent, Literal(result.raw_rows[tx["row_number"]])))
        g.add((t, PROV.wasDerivedFrom, record))
        g.add((t, PROV.wasGeneratedBy, run_node))

    # Balances stay in the JSON output only; the core ontology has no balance class yet.
    return g
