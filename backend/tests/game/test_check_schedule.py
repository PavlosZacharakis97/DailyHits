from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.catalog.models import Difficulty, SongStatus
from apps.game.dates import edition_today
from apps.game.management.commands.check_schedule import _ranges
from tests.factories import DailyPuzzleFactory, EditionFactory, complete_song

pytestmark = pytest.mark.django_db


def schedule(days: int, **song_kwargs):
    edition = EditionFactory()
    today = edition_today(edition)
    return [
        DailyPuzzleFactory(
            edition=edition, date=today + timedelta(days=i), song=complete_song(**song_kwargs)
        )
        for i in range(days)
    ]


def output(*args) -> str:
    out = StringIO()
    call_command("check_schedule", *args, stdout=out)
    return out.getvalue()


def test_complete_schedule() -> None:
    schedule(3)
    assert "Schedule is complete and valid." in output("--days", "3")


def test_gaps_are_grouped_into_ranges() -> None:
    schedule(2)
    text = output("--days", "6")
    assert "4 days without a puzzle" in text
    assert "(4 days)" in text


def test_song_that_lost_its_status_is_an_error() -> None:
    puzzles = schedule(2)
    song = puzzles[1].song
    song.status = SongStatus.REVIEW
    song.save()

    assert "Only verified songs can be scheduled." in output("--days", "2")


def test_balance_warning_is_reported_once() -> None:
    schedule(3, difficulty=Difficulty.HARD)
    text = output("--days", "3")
    assert text.count("hard songs in a row") == 1


def test_strict_mode_fails() -> None:
    EditionFactory()
    with pytest.raises(CommandError, match="problems found"):
        call_command("check_schedule", "--days", "2", "--strict", stdout=StringIO())


def test_unknown_edition() -> None:
    with pytest.raises(CommandError, match="No active edition"):
        call_command("check_schedule", "--edition", "mars", stdout=StringIO())


def test_ranges() -> None:
    from datetime import date

    days = [date(2030, 1, 1), date(2030, 1, 2), date(2030, 1, 5)]
    assert _ranges(days) == ["2030-01-01 – 2030-01-02 (2 days)", "2030-01-05"]
