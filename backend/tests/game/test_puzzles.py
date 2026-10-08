from datetime import date, datetime, timedelta
from uuid import uuid4
from zoneinfo import ZoneInfo

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog.models import Difficulty, SongStatus
from apps.game.dates import edition_today
from apps.game.models import DailyPuzzle, GameSession, Guess, SessionStatus
from apps.game.schedule import missing_dates, puzzle_errors, puzzle_warnings
from tests.factories import (
    DailyPuzzleFactory,
    EditionFactory,
    GenreFactory,
    SongFactory,
    complete_song,
)

pytestmark = pytest.mark.django_db

DAY = date(2030, 6, 15)


def build(song, day: date = DAY) -> DailyPuzzle:
    return DailyPuzzle(edition=EditionFactory(), song=song, date=day)


class TestNumbering:
    def test_numbers_are_assigned_in_order(self) -> None:
        first = DailyPuzzleFactory()
        second = DailyPuzzleFactory()

        assert (first.number, second.number) == (1, 2)

    def test_explicit_number_is_kept(self) -> None:
        assert DailyPuzzleFactory(number=40).number == 40

    def test_next_number_follows_the_highest(self) -> None:
        DailyPuzzleFactory(number=40)

        assert DailyPuzzleFactory().number == 41

    def test_numbers_are_per_edition(self) -> None:
        DailyPuzzleFactory()
        other = DailyPuzzleFactory(edition=EditionFactory(code="ru", name="Russian Hits"))

        assert other.number == 1

    def test_duplicate_number_is_rejected(self) -> None:
        DailyPuzzleFactory(number=1)

        with pytest.raises(IntegrityError), transaction.atomic():
            DailyPuzzleFactory(number=1)

    def test_one_puzzle_per_edition_and_date(self) -> None:
        DailyPuzzleFactory(date=DAY)

        with pytest.raises(IntegrityError), transaction.atomic():
            DailyPuzzleFactory(date=DAY)


class TestScheduleErrors:
    def test_valid_puzzle(self) -> None:
        build(complete_song()).full_clean()

    @pytest.mark.parametrize("status", [SongStatus.DRAFT, SongStatus.REVIEW])
    def test_song_must_be_verified(self, status: str) -> None:
        song = complete_song(status=status)

        with pytest.raises(ValidationError, match="Only verified songs"):
            build(song).full_clean()

    def test_song_must_be_in_the_edition(self) -> None:
        song = complete_song()
        song.editions.clear()

        with pytest.raises(ValidationError, match="not part of"):
            build(song).full_clean()

    @pytest.mark.parametrize("gap", [1, 364, -364])
    def test_song_cannot_repeat_within_a_year(self, gap: int) -> None:
        song = complete_song()
        DailyPuzzleFactory(song=song, date=DAY)

        assert "song" in puzzle_errors(build(song, DAY + timedelta(days=gap)))

    @pytest.mark.parametrize("gap", [365, -365])
    def test_song_may_repeat_after_a_year(self, gap: int) -> None:
        song = complete_song()
        DailyPuzzleFactory(song=song, date=DAY)

        assert puzzle_errors(build(song, DAY + timedelta(days=gap))) == {}

    @pytest.mark.parametrize("gap", [1, -1])
    def test_same_artist_not_two_days_in_a_row(self, gap: int) -> None:
        first = complete_song()
        DailyPuzzleFactory(song=first, date=DAY)
        second = complete_song(primary_artist=first.primary_artist)

        with pytest.raises(ValidationError, match="two days in a row"):
            build(second, DAY + timedelta(days=gap)).full_clean()

    def test_same_artist_with_a_day_in_between_is_fine(self) -> None:
        first = complete_song()
        DailyPuzzleFactory(song=first, date=DAY)
        second = complete_song(primary_artist=first.primary_artist)

        assert puzzle_errors(build(second, DAY + timedelta(days=2))) == {}

    def test_editing_a_puzzle_does_not_conflict_with_itself(self) -> None:
        puzzle = DailyPuzzleFactory()

        puzzle.full_clean()


class TestScheduleWarnings:
    def test_three_days_of_one_genre(self) -> None:
        genre = GenreFactory(name="Rock")
        for offset in (0, 1):
            DailyPuzzleFactory(song=complete_song(genre=genre), date=DAY + timedelta(days=offset))

        warnings = puzzle_warnings(build(complete_song(genre=genre), DAY + timedelta(days=2)))

        assert warnings == [f"3 days in a row from {DAY} are all Rock."]

    def test_three_hard_songs(self) -> None:
        for offset in (0, 2):
            DailyPuzzleFactory(
                song=complete_song(difficulty=Difficulty.HARD), date=DAY + timedelta(days=offset)
            )

        warnings = puzzle_warnings(
            build(complete_song(difficulty=Difficulty.HARD), DAY + timedelta(days=1))
        )

        assert warnings == [f"3 hard songs in a row from {DAY}."]

    def test_no_warning_with_a_gap(self) -> None:
        genre = GenreFactory()
        DailyPuzzleFactory(song=complete_song(genre=genre), date=DAY)

        assert puzzle_warnings(build(complete_song(genre=genre), DAY + timedelta(days=2))) == []


def test_missing_dates() -> None:
    edition = EditionFactory()
    DailyPuzzleFactory(edition=edition, date=DAY + timedelta(days=1))

    assert missing_dates(edition, DAY, 3) == [DAY, DAY + timedelta(days=2)]


class TestEditionToday:
    def test_uses_the_edition_time_zone(self) -> None:
        edition = EditionFactory(code="nz", name="NZ", timezone="Pacific/Auckland")
        moment = datetime(2030, 6, 15, 20, 0, tzinfo=ZoneInfo("UTC"))

        assert edition_today(edition, moment) == date(2030, 6, 16)

    def test_defaults_to_utc_now(self) -> None:
        assert edition_today(EditionFactory()) == timezone.now().date()


class TestSessions:
    def test_one_session_per_player_and_puzzle(self) -> None:
        puzzle = DailyPuzzleFactory()
        token = uuid4()
        GameSession.objects.create(player_token=token, puzzle=puzzle)

        with pytest.raises(IntegrityError), transaction.atomic():
            GameSession.objects.create(player_token=token, puzzle=puzzle)

    def test_finished_session_needs_finished_at(self) -> None:
        with pytest.raises(IntegrityError), transaction.atomic():
            GameSession.objects.create(
                player_token=uuid4(), puzzle=DailyPuzzleFactory(), status=SessionStatus.WON
            )

    def test_in_progress_session_cannot_have_finished_at(self) -> None:
        with pytest.raises(IntegrityError), transaction.atomic():
            GameSession.objects.create(
                player_token=uuid4(), puzzle=DailyPuzzleFactory(), finished_at=timezone.now()
            )

    def test_song_cannot_be_guessed_twice(self) -> None:
        session = GameSession.objects.create(player_token=uuid4(), puzzle=DailyPuzzleFactory())
        song = SongFactory()
        Guess.objects.create(session=session, song=song, attempt_number=1)

        with pytest.raises(IntegrityError), transaction.atomic():
            Guess.objects.create(session=session, song=song, attempt_number=2)

    def test_attempt_number_is_unique(self) -> None:
        session = GameSession.objects.create(player_token=uuid4(), puzzle=DailyPuzzleFactory())
        Guess.objects.create(session=session, song=SongFactory(), attempt_number=1)

        with pytest.raises(IntegrityError), transaction.atomic():
            Guess.objects.create(session=session, song=SongFactory(), attempt_number=1)
