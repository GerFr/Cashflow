"""Builds synthetic Trade Republic statements with the layout of the real PDF (positions in points, A4).

Used by the tests to build variants (e.g. a broken balance) and to write the golden fixture:

    uv run python test/support/traderepublic.py
    # rewrites connectors/fixtures/de.traderepublic.pdf-statement/basic/input.pdf
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

import pymupdf

# TextWriter with Font objects embeds Unicode, so "€" extracts as "€" (insert_text would give "·").
FONT, BOLD = pymupdf.Font("helv"), pymupdf.Font("hebo")
BODY, SMALL, LABEL, HEADING = 7.0, 5.5, 5.0, 11.0  # LABEL: column headers (52 pt wide, like the original)
LINE = 7.6  # line pitch inside a row
ROW_PAD = 16.0  # vertical space between rows
COL = {"DATUM": 74.4, "TYP": 100.6, "BESCHREIBUNG": 160.8, "ZAHLUNGSEINGANG": 372.9, "ZAHLUNGSAUSGANG": 427.1}
SALDO_RIGHT = 519.3
FOOTER_TOP = 758.0


@dataclass(frozen=True)
class Entry:
    date: list[str]  # date lines, e.g. ["02 Aug.", "2026"] or ["15", "Sept.", "2026"]
    typ: str
    description: list[str]  # description lines as printed
    incoming: str = ""
    outgoing: str = ""
    balance: str | None = None  # computed from the previous balance when None


ENTRIES = [
    Entry(["01 Aug.", "2026"], "Überweisung", ["Incoming transfer from Max Mustermann"], incoming="1.500,00"),
    Entry(["02 Aug.", "2026"], "Kartentransaktion", ["Kornblume Backstube"], outgoing="3,20"),
    Entry(["02 Aug.", "2026"], "Kartentransaktion", ["Kornblume Backstube"], outgoing="3,20"),
    Entry(
        ["04", "Aug.", "2026"],
        "Handel",
        ["Ausführung Handel Direktkauf Kauf IE00B4L5Y983 MUSTER-", "CORE MSCI WORLD 1234567890 KW"],
        outgoing="500,00",
    ),
    Entry(["03 Aug.", "2026"], "Zinsen", ["Your interest payment"], incoming="1,23"),
    Entry(
        ["01", "Sept.", "2026"],
        "SEPA-Lastschrift",
        ["Sepa Direct Debit transfer to Musterstrom GmbH"],
        outgoing="45,00",
    ),
    Entry(["15", "Sept.", "2026"], "Überweisung", ["Outgoing transfer for Erika Musterfrau"], outgoing="120,00"),
    Entry(["01 Okt.", "2026"], "Ertrag", ["Cash Dividend for ISIN IE00B4L5Y983"], incoming="2,10"),
    Entry(["01 Nov.", "2026"], "Zinsen", ["Your interest payment"], incoming="0,85"),
    Entry(
        ["05 Nov.", "2026"],
        "Überweisung",
        ["Einzahlung akzeptiert: DE89370400440532013000 auf", "DE02100100100006820101"],
        incoming="50,00",
    ),
]
ROWS_ON_FIRST_PAGE = 7
IBAN = "DE02100100100006820101"


def amount(text: str) -> Decimal:
    return Decimal(text.replace(".", "").replace(",", ".")) if text else Decimal(0)


def euro(value: Decimal) -> str:
    whole, cents = f"{value:.2f}".split(".")
    return f"{int(whole):,}".replace(",", ".") + f",{cents}"


def text(page: pymupdf.Page, x: float, top: float, value: str, size: float = BODY, font: pymupdf.Font = FONT) -> None:
    writer = pymupdf.TextWriter(page.rect)
    writer.append((x, top + size), value, font=font, fontsize=size)
    writer.write_text(page)


def right(page: pymupdf.Page, x1: float, top: float, value: str, size: float = BODY) -> None:
    text(page, x1 - FONT.text_length(value, fontsize=size), top, value, size)


def footer(page: pymupdf.Page, number: int, count: int) -> None:
    for i, line in enumerate(["Trade Republic Bank GmbH", "Brunnenstraße 19-21", "10119 Berlin"]):
        text(page, 73.0, FOOTER_TOP + i * 6.7, line, SMALL)
    text(page, 187.3, FOOTER_TOP, "www.traderepublic.com", SMALL)
    text(page, 74.5, 808.0, "Erstellt am 2026-11-09 08:00:00 Europe/Berlin (UTC+01:00)", SMALL)
    text(page, 475.7, 808.0, f"Seite {number} von {count}", SMALL)


def table_header(page: pymupdf.Page, top: float) -> float:
    for label, x in COL.items():
        text(page, x, top, label, LABEL, BOLD)
    text(page, 501.3, top, "SALDO", LABEL, BOLD)
    return top + 20.0


def entry_rows(page: pymupdf.Page, top: float, entries: list[tuple[Entry, str]]) -> float:
    for entry, balance in entries:
        lines = max(len(entry.date), len(entry.description))
        middle = top + (lines - 1) * LINE / 2
        for i, line in enumerate(entry.date):
            text(page, COL["DATUM"], top + i * LINE, line)
        text(page, COL["TYP"], middle, entry.typ)
        for i, line in enumerate(entry.description):
            text(page, COL["BESCHREIBUNG"], top + i * LINE, line)
        if entry.incoming:
            text(page, COL["ZAHLUNGSEINGANG"], middle, f"{entry.incoming} €")
        if entry.outgoing:
            text(page, COL["ZAHLUNGSAUSGANG"], middle, f"{entry.outgoing} €")
        right(page, SALDO_RIGHT, middle, f"{balance} €")
        top += lines * LINE + ROW_PAD
    return top


def statement_pdf(
    entries: list[Entry] = ENTRIES, opening: str = "0,00", overview: dict[str, str] | None = None
) -> bytes:
    """A two-page statement; the overview totals are computed from the entries unless given."""
    balances, current = [], amount(opening)
    for entry in entries:
        current += amount(entry.incoming) - amount(entry.outgoing)
        balances.append(entry.balance or euro(current))
    totals = {
        "incoming": euro(sum((amount(e.incoming) for e in entries), Decimal(0))),
        "outgoing": euro(sum((amount(e.outgoing) for e in entries), Decimal(0))),
        "closing": euro(current),
        **(overview or {}),
    }
    rows = list(zip(entries, balances, strict=True))

    doc = pymupdf.open()
    first = doc.new_page(width=595.28, height=841.89)
    text(first, 73.8, 80.0, "TRADE REPUBLIC", 9.0, BOLD)
    text(first, 73.8, 104.0, "TRADE REPUBLIC BANK GMBH BRUNNENSTRASSE 19-21 10119 BERLIN", SMALL, BOLD)
    for i, line in enumerate(["MAX MUSTERMANN", "Musterweg 1", "12345 Musterstadt"]):
        text(first, 73.8, 139.1 + i * 9.1, line, SMALL)
    for i, (label, value) in enumerate(
        [("DATUM", "01 Aug. 2026 - 08 Nov. 2026"), ("IBAN", IBAN), ("BIC", "TRBKDEBBXXX")]
    ):
        text(first, 388.7, 139.1 + i * 9.1, label, SMALL, BOLD)
        right(first, SALDO_RIGHT, 139.1 + i * 9.1, value, SMALL)
    text(first, 73.7, 202.1, "KONTOÜBERSICHT", HEADING, BOLD)
    for label, x in [
        ("PRODUKT", 74.4),
        ("ANFANGSSALDO", 148.2),
        ("ZAHLUNGSEINGANG", 238.7),
        ("ZAHLUNGSAUSGANG", 347.2),
    ]:
        text(first, x, 240.6, label, SMALL, BOLD)
    text(first, 492.1, 240.6, "ENDSALDO", SMALL, BOLD)
    text(first, 74.4, 255.4, "Cashkonto")
    for x, value in [(148.2, opening), (238.7, totals["incoming"]), (347.2, totals["outgoing"])]:
        text(first, x, 255.4, f"{value} €")
    right(first, 520.8, 255.4, f"{totals['closing']} €")
    text(first, 73.7, 311.9, "UMSATZÜBERSICHT", HEADING, BOLD)
    entry_rows(first, table_header(first, 342.1), rows[:ROWS_ON_FIRST_PAGE])
    footer(first, 1, 2)

    second = doc.new_page(width=595.28, height=841.89)
    text(second, 73.8, 104.0, "TRADE REPUBLIC BANK GMBH BRUNNENSTRASSE 19-21 10119 BERLIN", SMALL, BOLD)
    top = entry_rows(second, table_header(second, 152.7), rows[ROWS_ON_FIRST_PAGE:])
    # Later sections must be ignored: a money-market fund table with dated rows and amounts.
    text(second, 73.7, top + 20, "BARMITTELÜBERSICHT", HEADING, BOLD)
    text(second, 73.7, top + 60, "TRANSAKTIONSÜBERSICHT", HEADING, BOLD)
    text(second, 74.4, top + 90, "DATUM", SMALL, BOLD)
    text(second, 497.8, top + 90, "BETRAG", SMALL, BOLD)
    text(second, 74.4, top + 105, "02 Nov. 2026")
    text(second, 139.0, top + 105, "Kauf")
    right(second, SALDO_RIGHT, top + 105, "880,00 €")
    footer(second, 2, 2)

    doc.set_metadata({})
    data = doc.tobytes(garbage=4, deflate=True, no_new_id=True)
    doc.close()
    return data


if __name__ == "__main__":
    repo = Path(__file__).resolve().parents[3]
    target = repo / "connectors" / "fixtures" / "de.traderepublic.pdf-statement" / "basic" / "input.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(statement_pdf())
    print(f"written {target.relative_to(repo)}")
