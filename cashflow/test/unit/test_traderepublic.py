from __future__ import annotations

import dataclasses
from datetime import date

import pymupdf
import pytest
from support.traderepublic import ENTRIES, statement_pdf

from cashflow.connectors.engine import ConnectorError
from cashflow.connectors.traderepublic import TradeRepublicStatement, Word, join_lines, parse_day

CONNECTOR = TradeRepublicStatement()


def blank_pdf() -> bytes:
    doc = pymupdf.open()
    doc.new_page().insert_text((72, 72), "Some other bank statement")
    return doc.tobytes()


@pytest.mark.parametrize(
    "content",
    [b"Buchungstag;Betrag\n", b"%PDF-1.7 truncated", blank_pdf()],
    ids=["csv", "broken-pdf", "other-pdf"],
)
def test_other_files_do_not_match(content):
    assert not CONNECTOR.matches(content)


def test_broken_pdf_is_a_connector_error():
    with pytest.raises(ConnectorError, match="not a readable PDF"):
        CONNECTOR.parse(b"%PDF-1.7 truncated")


def test_other_pdf_is_a_connector_error():
    with pytest.raises(ConnectorError, match="statement header"):
        CONNECTOR.parse(blank_pdf())


def test_row_breaking_the_running_balance_is_rejected():
    entries = list(ENTRIES)
    entries[3] = dataclasses.replace(entries[3], balance="999,99")
    with pytest.raises(ConnectorError, match=r"row 4: balance 999\.99 does not follow"):
        CONNECTOR.parse(statement_pdf(entries))


def test_totals_must_match_the_overview():
    with pytest.raises(ConnectorError, match=r"outgoing 671\.40 differs from the KONTOÜBERSICHT"):
        CONNECTOR.parse(statement_pdf(overview={"outgoing": "671,41"}))


def test_opening_balance_starts_the_chain():
    result = CONNECTOR.parse(statement_pdf(opening="100,00", overview=None))
    assert result.balances[0]["balance"] == "982.78"


@pytest.mark.parametrize(
    ("tokens", "expected"),
    [
        (["02", "Aug.", "2023"], date(2023, 8, 2)),
        (["11", "Juli", "2023"], date(2023, 7, 11)),
        (["3", "März", "2024"], date(2024, 3, 3)),
        (["15", "Sept.", "2026"], date(2026, 9, 15)),
        (["31", "Dez.", "2025"], date(2025, 12, 31)),
    ],
)
def test_parse_day(tokens, expected):
    assert parse_day(tokens) == expected


@pytest.mark.parametrize("tokens", [["02", "Aug."], ["xx", "Aug.", "2023"], ["02", "Foo", "2023"]])
def test_parse_day_rejects_other_text(tokens):
    with pytest.raises(ConnectorError, match="date not understood"):
        parse_day(tokens)


def test_join_lines_joins_words_broken_at_a_line_end():
    assert join_lines([Word(0, 0, 10, 7, "X(IE)-"), Word(0, 8.1, 10, 15, "MSCI")]) == "X(IE)-MSCI"


def test_join_lines_keeps_spaces_within_a_line():
    words = [
        Word(0, 0.4, 10, 7, "Kauf"),
        Word(12, 0, 14, 7, "-"),
        Word(16, 0.3, 30, 7, "Amundi"),
        Word(0, 8, 9, 15, "MSCI"),
    ]
    assert join_lines(words) == "Kauf - Amundi MSCI"


def test_join_lines_keeps_a_standalone_dash_at_a_line_end():
    assert (
        join_lines([Word(0, 0, 10, 7, "Kauf"), Word(12, 0, 14, 7, "-"), Word(0, 8, 9, 15, "Amundi")]) == "Kauf - Amundi"
    )
