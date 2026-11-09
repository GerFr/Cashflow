from __future__ import annotations

from datetime import date

from cashflow.balances import Anchor, compute

D = date.fromisoformat


def test_no_anchor_no_balances():
    assert compute([], {D("2026-01-02"): -500}) == ({}, [])


def test_backwards_and_forwards_from_the_anchor():
    net = {D("2026-01-01"): 1000, D("2026-01-03"): -200, D("2026-01-05"): 50}
    days, checks = compute([Anchor(D("2026-01-03"), 1300, "export")], net)
    assert days == {
        D("2026-01-01"): 1500,
        D("2026-01-02"): 1500,
        D("2026-01-03"): 1300,
        D("2026-01-04"): 1300,
        D("2026-01-05"): 1350,
    }
    assert checks == []


def test_later_anchor_is_checked_and_resets_the_balance():
    net = {D("2026-01-02"): -100, D("2026-01-04"): -100}
    anchors = [Anchor(D("2026-01-01"), 1000, "opening"), Anchor(D("2026-01-03"), 850, "export")]
    days, checks = compute(anchors, net)
    assert [(c.anchor.date, c.computed, c.difference) for c in checks] == [(D("2026-01-03"), 900, -50)]
    assert days[D("2026-01-03")] == 850  # the bank's figure wins
    assert days[D("2026-01-04")] == 750


def test_matching_anchors_have_no_difference():
    net = {D("2026-01-02"): -100}
    anchors = [Anchor(D("2026-01-01"), 1000, "opening"), Anchor(D("2026-01-02"), 900, "export")]
    _, checks = compute(anchors, net)
    assert [c.difference for c in checks] == [0]


def test_export_wins_a_tie_with_the_opening_balance():
    anchors = [Anchor(D("2026-01-01"), 5, "opening"), Anchor(D("2026-01-01"), 7, "export")]
    days, checks = compute(anchors, {})
    assert days == {D("2026-01-01"): 7}
    assert [(c.anchor.source, c.difference) for c in checks] == [("opening", -2)]
