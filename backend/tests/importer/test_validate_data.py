from io import StringIO

import pytest
from django.core.management import CommandError, call_command

from apps.catalog.models import SongStatus
from apps.importer.quality import probable_duplicates, song_findings
from tests.factories import ArtistFactory, FactFactory, SongFactory, complete_song

pytestmark = pytest.mark.django_db


def test_clean_catalogue() -> None:
    complete_song()
    assert song_findings() == []


def test_reports_missing_fields_and_old_years() -> None:
    complete_song(year=1932)
    SongFactory(title="Unfinished")

    messages = {f.message for f in song_findings()}
    assert "No genre." in messages
    assert "Year 1932 is unusually early: check it." in messages


def test_reports_facts_that_reveal_the_answer() -> None:
    song = complete_song(title="Hello")
    FactFactory(song=song, text="Hello was recorded in one take.")

    assert any("mentions “Hello”" in f.message for f in song_findings())


def test_status_filter() -> None:
    SongFactory(title="Draft one")
    assert song_findings([SongStatus.VERIFIED]) == []


def test_probable_duplicates() -> None:
    queen = ArtistFactory(name="Queen")
    SongFactory(title="Bohemian Rhapsody", primary_artist=queen)
    SongFactory(title="Bohemian Rapsody", primary_artist=queen)
    SongFactory(title="Dancing Queen", primary_artist=ArtistFactory(name="ABBA"))

    pairs = probable_duplicates()
    assert len(pairs) == 1
    assert {pairs[0][0], pairs[0][1]} == {"Bohemian Rhapsody — Queen", "Bohemian Rapsody — Queen"}


def test_command_report_and_ci_exit_code() -> None:
    bad = complete_song(title="Hello")
    FactFactory(song=bad, text="Hello was recorded in one take.")

    out = StringIO()
    call_command("validate_data", stdout=out)
    assert "1 errors" in out.getvalue()

    with pytest.raises(CommandError, match="blocking problems in verified songs"):
        call_command("validate_data", "--fail-on-error", stdout=StringIO())
