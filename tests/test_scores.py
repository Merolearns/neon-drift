"""Tests for ScoreDB.qualifies: a scoreless run is never a high score."""

import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scores import ScoreDB


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("NEON_DRIFT_DB", str(tmp_path / "scores.db"))
    return ScoreDB()


def test_zero_does_not_qualify_on_empty_table(db):
    # a run that scores nothing used to prompt for a name and store a 0
    assert db.qualifies(0) is False


def test_any_positive_score_qualifies_on_empty_table(db):
    assert db.qualifies(1) is True


def test_full_table(db):
    for i in range(10):
        db.add_score(f"P{i}", (i + 1) * 10, 1)
    assert db.qualifies(0) is False
    assert db.qualifies(10) is False  # tie with the lowest score: no bump
    assert db.qualifies(11) is True
