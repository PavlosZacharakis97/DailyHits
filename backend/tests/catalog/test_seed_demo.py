import pytest
from django.core.management import call_command

from apps.catalog.models import ArtistRole, Fact, Song, SongStatus
from apps.catalog.validation import SONG_ISSUE_PREFETCH, song_issues

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def _reference() -> None:
    call_command("seed_reference")


def test_demo_songs_pass_validation_without_issues() -> None:
    call_command("seed_demo", status=SongStatus.VERIFIED)

    songs = Song.objects.prefetch_related(*SONG_ISSUE_PREFETCH)
    assert songs.count() == 20
    assert {s.title: song_issues(s) for s in songs} == {s.title: [] for s in songs}
    assert set(songs.values_list("status", flat=True)) == {SongStatus.VERIFIED}


def test_demo_is_idempotent() -> None:
    call_command("seed_demo")
    call_command("seed_demo")

    assert Song.objects.count() == 20
    assert Fact.objects.count() == 60
    assert set(Song.objects.values_list("status", flat=True)) == {SongStatus.REVIEW}


def test_featured_artist_and_members() -> None:
    call_command("seed_demo")

    despacito = Song.objects.get(title="Despacito")
    assert despacito.song_artists.get(role=ArtistRole.FEATURED).artist.name == "Daddy Yankee"
    queen = Song.objects.get(title="Bohemian Rhapsody").primary_artist
    assert "Freddie Mercury" in queen.members.values_list("name", flat=True)
