import pytest

from apps.catalog.models import ArtistMember, SongAlias, SongArtist, SongTheme
from apps.catalog.validation import (
    SONG_ISSUE_PREFETCH,
    Level,
    mentions,
    song_issues,
    verification_errors,
)
from tests.factories import (
    ArtistFactory,
    FactFactory,
    PersonFactory,
    SongFactory,
    StyleFactory,
    ThemeFactory,
    complete_song,
)

pytestmark = pytest.mark.django_db


def codes(song, level: Level | None = None) -> set[str]:
    song = type(song).objects.prefetch_related(*SONG_ISSUE_PREFETCH).get(pk=song.pk)
    return {i.code for i in song_issues(song) if level is None or i.level is level}


def test_complete_song_has_no_issues() -> None:
    assert codes(complete_song()) == set()


def test_empty_draft_lists_every_missing_part() -> None:
    assert codes(SongFactory(), Level.ERROR) == {
        "missing_year",
        "missing_genre",
        "missing_language",
        "missing_vocal",
        "no_styles",
        "no_themes",
        "no_editions",
        "no_facts",
    }


def test_missing_youtube_and_sources_are_warnings_only() -> None:
    song = SongFactory()

    assert {"no_youtube", "no_sources"} <= codes(song, Level.WARNING)


def test_more_than_two_styles() -> None:
    song = complete_song()
    song.styles.add(StyleFactory(), StyleFactory())

    assert "too_many_styles" in codes(song)


def test_more_than_two_themes() -> None:
    song = complete_song()
    SongTheme.objects.create(song=song, theme=ThemeFactory())
    SongTheme.objects.create(song=song, theme=ThemeFactory())

    assert "too_many_themes" in codes(song)


def test_themes_without_a_primary() -> None:
    song = complete_song()
    song.song_themes.update(is_primary=False)

    assert "primary_theme" in codes(song)


def test_fewer_than_three_facts() -> None:
    song = complete_song()
    song.facts.first().delete()

    assert "few_facts" in codes(song)


class TestFactsMustNotRevealTheAnswer:
    def test_title(self) -> None:
        song = complete_song(title="Bohemian Rhapsody")
        FactFactory(song=song, text="Bohemian Rhapsody took three weeks to record.")

        assert "fact_mentions_answer" in codes(song)

    def test_primary_artist_ignoring_case_and_accents(self) -> None:
        song = complete_song(primary_artist=ArtistFactory(name="Beyoncé"))
        FactFactory(song=song, text="BEYONCE wrote it on tour.")

        assert "fact_mentions_answer" in codes(song)

    def test_featured_artist(self) -> None:
        song = complete_song()
        SongArtist.objects.create(song=song, artist=ArtistFactory(name="Daddy Yankee"))
        FactFactory(song=song, text="Daddy Yankee joined for the remix.")

        assert "fact_mentions_answer" in codes(song)

    def test_band_member(self) -> None:
        queen = ArtistFactory(name="Queen")
        ArtistMember.objects.create(artist=queen, person=PersonFactory(name="Freddie Mercury"))
        song = complete_song(primary_artist=queen)
        FactFactory(song=song, text="Freddie Mercury played the piano part.")

        assert "fact_mentions_answer" in codes(song)

    def test_alias(self) -> None:
        song = complete_song()
        SongAlias.objects.create(song=song, alias="Despasito")
        FactFactory(song=song, text="Fans often search for despasito.")

        assert "fact_mentions_answer" in codes(song)

    def test_only_whole_words_count(self) -> None:
        song = complete_song(title="One")
        FactFactory(song=song, text="It was done in someone's garage.")

        assert "fact_mentions_answer" not in codes(song)


@pytest.mark.parametrize(
    ("text", "name", "expected"),
    [
        ("Sung by Beyoncé", "beyonce", True),
        ("ABBA's biggest hit", "ABBA", True),
        ("Abbatoir", "ABBA", False),
        ("AC/DC on stage", "AC/DC", True),
        ("anything", "  ", False),
    ],
)
def test_mentions(text: str, name: str, expected: bool) -> None:
    assert mentions(text, name) is expected


def test_verification_errors_exclude_warnings() -> None:
    song = complete_song()
    song.youtube_video_id = None
    song.save()

    assert verification_errors(song) == []
