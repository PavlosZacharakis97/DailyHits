from datetime import timedelta
from itertools import pairwise

import pytest
from django.core.management import CommandError, call_command

from apps.catalog.models import ArtistRole, Fact, Song, SongStatus
from apps.catalog.validation import SONG_ISSUE_PREFETCH, song_issues
from apps.game.dates import edition_today
from apps.game.models import DailyPuzzle

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _reference() -> None:
    call_command("seed_reference")


def test_demo_songs_pass_validation_without_issues() -> None:
    call_command("seed_demo", status=SongStatus.VERIFIED)

    songs = Song.objects.prefetch_related(*SONG_ISSUE_PREFETCH)
    assert songs.count() == 40
    assert {s.title: song_issues(s) for s in songs} == {s.title: [] for s in songs}
    assert set(songs.values_list("status", flat=True)) == {SongStatus.VERIFIED}


def test_demo_is_idempotent() -> None:
    call_command("seed_demo")
    call_command("seed_demo")

    assert Song.objects.count() == 40
    assert Fact.objects.count() == 120
    assert set(Song.objects.values_list("status", flat=True)) == {SongStatus.REVIEW}


def test_featured_artist_and_members() -> None:
    call_command("seed_demo")

    despacito = Song.objects.get(title="Despacito")
    assert despacito.song_artists.get(role=ArtistRole.FEATURED).artist.name == "Daddy Yankee"
    queen = Song.objects.get(title="Bohemian Rhapsody").primary_artist
    assert "Freddie Mercury" in queen.members.values_list("name", flat=True)


def test_schedule_follows_the_rules() -> None:
    call_command("seed_demo", status=SongStatus.VERIFIED, schedule=25, past=3)

    puzzles = list(DailyPuzzle.objects.select_related("song__primary_artist").order_by("date"))
    first = edition_today(puzzles[0].edition) - timedelta(days=3)
    assert len(puzzles) == 25
    assert puzzles[0].date == first
    assert [p.number for p in puzzles] == list(range(1, 26))
    artists = [p.song.primary_artist_id for p in puzzles]
    assert all(a != b for a, b in pairwise(artists))


def test_schedule_is_idempotent() -> None:
    call_command("seed_demo", status=SongStatus.VERIFIED, schedule=5)
    call_command("seed_demo", status=SongStatus.VERIFIED, schedule=5)

    assert DailyPuzzle.objects.count() == 5


def test_schedule_needs_verified_songs() -> None:
    with pytest.raises(CommandError, match="--status verified"):
        call_command("seed_demo", schedule=5)
