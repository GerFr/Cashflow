"""Trade Republic account statement (PDF "Kontoauszug", section UMSATZÜBERSICHT).

Trade Republic offers no CSV export, so this is a code connector. It reads the words of the PDF with
their positions, groups them into table rows by vertical gaps and assigns them to columns by the
header positions (DATUM, TYP, BESCHREIBUNG, ZAHLUNGSEINGANG, ZAHLUNGSAUSGANG, SALDO). Every row must
continue the running balance, and the totals must match the KONTOÜBERSICHT, so a layout change fails
loudly instead of producing wrong numbers. Later sections (BARMITTELÜBERSICHT, money-market fund
TRANSAKTIONSÜBERSICHT, HINWEISE) are not account bookings and are ignored.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import date
from decimal import Decimal

import pymupdf

from cashflow.connectors.engine import ConnectorError, ParseResult, add_record, format_decimal, parse_decimal

LOCALE = {"decimal_separator": ",", "thousands_separator": "."}
MONTHS = {
    "jan": 1, "feb": 2, "mär": 3, "mar": 3, "apr": 4, "mai": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "okt": 10, "nov": 11, "dez": 12,
}  # fmt: skip
AMOUNT = re.compile(r"^\d{1,3}(?:\.\d{3})*,\d{2}$")
DAY = re.compile(r"^\d{1,2}$")
IBAN = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")
COLUMNS = ("DATUM", "TYP", "BESCHREIBUNG", "ZAHLUNGSEINGANG", "ZAHLUNGSAUSGANG", "SALDO")
SAME_LINE = 2.0  # points: words whose tops differ less are on one line
ROW_GAP = 4.0  # points: a larger vertical gap between words starts a new table row
HEADING_HEIGHT = 10.0  # points: section headings are taller than table text
COUNTERPARTY_PREFIXES = ("Outgoing transfer for ", "Incoming transfer from ")


@dataclass(frozen=True)
class Word:
    x0: float
    top: float
    x1: float
    bottom: float
    text: str


@dataclass(frozen=True)
class Row:
    date: date
    typ: str
    description: str
    amount: Decimal
    direction: str
    balance: Decimal
    raw: str


def read_pages(data: bytes, limit: int | None = None) -> list[list[Word]]:
    try:
        with pymupdf.open(stream=data, filetype="pdf") as doc:
            return [[Word(*w[:5]) for w in page.get_text("words")] for page in list(doc)[:limit]]
    except (pymupdf.FileDataError, RuntimeError, ValueError) as exc:
        raise ConnectorError(f"not a readable PDF: {exc}") from None


def same_line(words: list[Word], anchor: Word) -> list[Word]:
    return sorted((w for w in words if abs(w.top - anchor.top) < SAME_LINE), key=lambda w: w.x0)


def money(text: str) -> Decimal:
    return parse_decimal(text, LOCALE)


def parse_day(tokens: list[str]) -> date:
    """'02', 'Aug.', '2023' → 2023-08-02."""
    if len(tokens) != 3 or not DAY.match(tokens[0]):
        raise ConnectorError(f"date not understood: {' '.join(tokens)!r}")
    month = MONTHS.get(tokens[1].lower().rstrip(".")[:3])
    if month is None or not tokens[2].isdigit():
        raise ConnectorError(f"date not understood: {' '.join(tokens)!r}")
    return date(int(tokens[2]), month, int(tokens[0]))


def lines(words: list[Word]) -> list[list[Word]]:
    """Words grouped into lines (tops within SAME_LINE), each line ordered left to right."""
    result: list[list[Word]] = []
    for word in sorted(words, key=lambda w: w.top):
        if result and word.top - result[-1][0].top < SAME_LINE:
            result[-1].append(word)
        else:
            result.append([word])
    return [sorted(line, key=lambda w: w.x0) for line in result]


def join_lines(words: list[Word]) -> str:
    """Text in reading order; a word broken at a line end ('MUSTER-' / 'CORE') is joined without a space."""
    text = ""
    for line in lines(words):
        for i, word in enumerate(line):
            hyphenated = i == 0 and text.endswith("-") and not text.endswith(" -") and word.text[0].isalnum()
            text = word.text if not text else text + ("" if hyphenated else " ") + word.text
    return text


def group_rows(words: list[Word]) -> list[list[Word]]:
    """Split table words into rows wherever the vertical gap between them exceeds ROW_GAP."""
    rows: list[list[Word]] = []
    bottom = None
    for word in sorted(words, key=lambda w: w.top):
        if bottom is None or word.top - bottom > ROW_GAP:
            rows.append([])
            bottom = word.bottom
        rows[-1].append(word)
        bottom = max(bottom, word.bottom)
    return rows


class TradeRepublicStatement:
    id = "de.traderepublic.pdf-statement"
    name = "Trade Republic - Kontoauszug (PDF)"
    version = "0.1.0"
    status = "community"
    institution = "Trade Republic Bank GmbH"
    filename_patterns: tuple[str, ...] = ()

    def matches(self, data: bytes) -> bool:
        if not data.startswith(b"%PDF"):
            return False
        try:
            first_page = read_pages(data, limit=1)[0]
        except (ConnectorError, IndexError):
            return False
        texts = {w.text for w in first_page}
        return {"TRADE", "REPUBLIC", "UMSATZÜBERSICHT", "KONTOÜBERSICHT"} <= texts

    def parse(self, data: bytes) -> ParseResult:
        pages = read_pages(data)
        if not pages:
            raise ConnectorError("empty PDF")
        iban, period_end = self.read_header(pages[0])
        opening, total_in, total_out, closing = self.read_overview(pages[0])

        result = ParseResult(self.id, self.version, hashlib.sha256(data).hexdigest())
        occurrences: dict[str, int] = {}
        balance = opening
        sums = {"credit": Decimal(0), "debit": Decimal(0)}
        for number, row in enumerate((r for page in pages for r in self.read_rows(page)), start=1):
            signed = row.amount if row.direction == "credit" else -row.amount
            if balance + signed != row.balance:
                raise ConnectorError(
                    f"balance {row.balance} does not follow from {balance} and {signed} ({row.raw})", number
                )
            balance = row.balance
            sums[row.direction] += row.amount
            add_record(result, self.record(number, iban, row), occurrences, row.raw)

        expected = {"incoming": total_in, "outgoing": total_out, "closing balance": closing}
        actual = {"incoming": sums["credit"], "outgoing": sums["debit"], "closing balance": balance}
        for name in expected:
            if expected[name] != actual[name]:
                raise ConnectorError(
                    f"{name} {actual[name]} differs from the KONTOÜBERSICHT ({expected[name]}); are all pages there?"
                )

        result.balances.append(
            {"account": iban, "date": period_end.isoformat(), "balance": format_decimal(closing, money=True)}
        )
        return result

    @staticmethod
    def read_header(words: list[Word]) -> tuple[str, date]:
        """IBAN and end of the statement period from the block in the top right corner of page 1."""
        labels = {}
        for label in ("IBAN", "DATUM"):  # the topmost one; the table header has another DATUM
            found = [w for w in words if w.text == label]
            if not found:
                raise ConnectorError("statement header (DATUM, IBAN) not found")
            labels[label] = min(found, key=lambda w: w.top)
        iban = next((w.text for w in same_line(words, labels["IBAN"]) if IBAN.match(w.text)), None)
        period = [w.text for w in same_line(words, labels["DATUM"]) if w is not labels["DATUM"]]
        if iban is None or "-" not in period:
            raise ConnectorError("statement header (DATUM, IBAN) not understood")
        return iban, parse_day(period[period.index("-") + 1 :])

    @staticmethod
    def read_overview(words: list[Word]) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Opening balance, incoming, outgoing and closing balance of the 'Cashkonto' row."""
        anchor = next((w for w in words if w.text == "Cashkonto"), None)
        amounts = [money(w.text) for w in same_line(words, anchor) if AMOUNT.match(w.text)] if anchor else []
        if len(amounts) != 4:
            raise ConnectorError("KONTOÜBERSICHT: row 'Cashkonto' with four amounts not found")
        opening, total_in, total_out, closing = amounts
        return opening, total_in, total_out, closing

    def read_rows(self, words: list[Word]) -> list[Row]:
        """The transaction rows of one page: between the table header and the next heading or the footer."""
        header = next((w for w in words if w.text == "BESCHREIBUNG"), None)
        if header is None:
            return []
        columns = {w.text: w for w in same_line(words, header) if w.text in COLUMNS}
        if set(columns) != set(COLUMNS):
            raise ConnectorError(f"table header incomplete: {sorted(columns)}")
        footer = [w.top for w in words if w.text == "www.traderepublic.com"]
        headings = [w.top for w in words if w.top > header.bottom and w.bottom - w.top > HEADING_HEIGHT]
        end = min([*footer, *headings], default=float("inf"))
        table = [w for w in words if header.bottom < w.top < end and w.x0 >= columns["DATUM"].x0 - 2]
        return [self.read_row(row, columns) for row in group_rows(table)]

    @staticmethod
    def read_row(words: list[Word], columns: dict[str, Word]) -> Row:
        typ_x, text_x = columns["TYP"].x0 - 2, columns["BESCHREIBUNG"].x0 - 2
        amount_x, out_x = columns["ZAHLUNGSEINGANG"].x0 - 3, columns["ZAHLUNGSAUSGANG"].x0 - 3
        amounts = [w for w in words if w.x0 >= amount_x and AMOUNT.match(w.text)]
        raw = join_lines(words)
        balances = [w for w in amounts if w.x1 > columns["SALDO"].x0]
        moves = [w for w in amounts if w not in balances]
        if len(balances) != 1 or len(moves) != 1:
            raise ConnectorError(f"expected one amount and one balance in row: {raw!r}")
        description = [
            w for w in words if w.x0 >= text_x and w not in amounts and not (w.x0 >= amount_x and w.text == "€")
        ]
        return Row(
            date=parse_day([w.text for line in lines(words) for w in line if w.x0 < typ_x]),
            typ=join_lines([w for w in words if typ_x <= w.x0 < text_x]),
            description=join_lines(description),
            amount=money(moves[0].text),
            direction="credit" if moves[0].x0 < out_x else "debit",
            balance=money(balances[0].text),
            raw=raw,
        )

    @staticmethod
    def record(number: int, iban: str, row: Row) -> dict[str, str | int]:
        rec: dict[str, str | int] = {
            "row_number": number,
            "account_iban": iban,
            "booking_date": row.date.isoformat(),
            "direction": row.direction,
            "amount": format_decimal(row.amount, money=True),
            "currency": "EUR",
            "status": "booked",
            "remittance_information": row.description,
            "booking_text": row.typ,
        }
        if row.typ == "Kartentransaktion":
            rec["counterparty_name"] = row.description
        for prefix in COUNTERPARTY_PREFIXES:
            if row.description.startswith(prefix):
                rec["counterparty_name"] = row.description.removeprefix(prefix)
        return rec
