"""Database-level guarantees: these must hold even if Python validation is bypassed."""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from apps.catalog.models import ArtistRole, Song, SongAlias, SongArtist, SongStatus, SongTheme
from tests.factories import (
    ArtistFactory,
    FactFactory,
    SongFactory,
    ThemeFactory,
    complete_song,
)

pytestmark = pytest.mark.django_db


def assert_db_rejects(fn) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        fn()


class TestSongUniqueness:
    def test_same_title_and_primary_artist_ignoring_case_is_rejected(self) -> None:
        song = SongFactory(title="Bohemian Rhapsody")

        assert_db_rejects(
            lambda: SongFactory(title="BOHEMIAN rhapsody", primary_artist=song.primary_artist)
        )

    def test_same_title_by_another_artist_is_allowed(self) -> None:
        SongFactory(title="Hello")
        SongFactory(title="Hello")

        assert Song.objects.filter(title="Hello").count() == 2

    def test_duplicate_is_reported_by_model_validation(self) -> None:
        song = SongFactory(title="Hello")
        duplicate = Song(title="hello", primary_artist=song.primary_artist)

        with pytest.raises(ValidationError, match="already has a song with this title"):
            duplicate.full_clean()

    def test_musicbrainz_id_is_unique(self) -> None:
        mbid = "b1a9c0e9-d987-4042-ae91-78d6a3267d69"
        SongFactory(musicbrainz_id=mbid)

        assert_db_rejects(lambda: SongFactory(musicbrainz_id=mbid))

    def test_several_songs_without_musicbrainz_id_are_allowed(self) -> None:
        SongFactory(musicbrainz_id=None)
        SongFactory(musicbrainz_id=None)


class TestSongYear:
    @pytest.mark.parametrize("year", [1900, timezone.now().year])
    def test_bounds_are_accepted(self, year: int) -> None:
        SongFactory(year=year)

    @pytest.mark.parametrize("year", [1899, timezone.now().year + 1])
    def test_out_of_range_is_rejected_by_database(self, year: int) -> None:
        assert_db_rejects(lambda: SongFactory(year=year))

    def test_future_year_is_rejected_by_model_validation(self) -> None:
        song = SongFactory.build(year=timezone.now().year + 1, primary_artist=ArtistFactory())

        with pytest.raises(ValidationError) as exc:
            song.full_clean()

        assert "year" in exc.value.message_dict


class TestSongFields:
    def test_blank_title_is_rejected(self) -> None:
        assert_db_rejects(lambda: SongFactory(title="   "))

    @pytest.mark.parametrize("video_id", ["short", "dQw4w9WgXc!", "dQw4w9 gXcQ"])
    def test_malformed_youtube_id_is_rejected(self, video_id: str) -> None:
        assert_db_rejects(lambda: SongFactory(youtube_video_id=video_id))

    def test_empty_youtube_id_is_stored_as_null(self) -> None:
        song = SongFactory.build(youtube_video_id="", primary_artist=ArtistFactory())

        song.full_clean()

        assert song.youtube_video_id is None

    def test_invalid_vocal_is_rejected(self) -> None:
        assert_db_rejects(lambda: SongFactory(vocal="choir"))

    def test_sources_must_be_urls(self) -> None:
        song = SongFactory.build(sources=["not a url"], primary_artist=ArtistFactory())

        with pytest.raises(ValidationError) as exc:
            song.full_clean()

        assert "sources" in exc.value.message_dict

    @pytest.mark.parametrize("missing", ["year", "genre", "language", "vocal"])
    def test_verified_song_needs_tile_fields(self, missing: str) -> None:
        song = complete_song()
        setattr(song, missing, "" if missing == "vocal" else None)

        assert_db_rejects(song.save)

    def test_draft_song_may_be_incomplete(self) -> None:
        song = SongFactory(status=SongStatus.DRAFT)

        assert song.year is None and song.genre is None


class TestPrimaryArtistSync:
    def test_creating_a_song_creates_the_primary_credit(self) -> None:
        song = SongFactory()

        assert list(song.song_artists.values_list("artist_id", "role")) == [
            (song.primary_artist_id, ArtistRole.PRIMARY)
        ]

    def test_changing_primary_artist_replaces_the_credit(self) -> None:
        song = SongFactory()
        new_artist = ArtistFactory()

        song.primary_artist = new_artist
        song.save()

        assert list(song.song_artists.values_list("artist_id", "role")) == [
            (new_artist.pk, ArtistRole.PRIMARY)
        ]

    def test_promoting_a_featured_artist(self) -> None:
        song = SongFactory()
        guest = ArtistFactory()
        SongArtist.objects.create(song=song, artist=guest, role=ArtistRole.FEATURED)

        old_primary = song.primary_artist_id
        song.primary_artist = guest
        song.save()

        assert set(song.song_artists.values_list("artist_id", "role")) == {
            (guest.pk, ArtistRole.PRIMARY)
        }
        assert old_primary != guest.pk

    def test_second_primary_credit_is_rejected(self) -> None:
        song = SongFactory()

        assert_db_rejects(
            lambda: SongArtist.objects.create(
                song=song, artist=ArtistFactory(), role=ArtistRole.PRIMARY
            )
        )

    def test_same_artist_twice_is_rejected(self) -> None:
        song = SongFactory()

        assert_db_rejects(
            lambda: SongArtist.objects.create(
                song=song, artist=song.primary_artist, role=ArtistRole.FEATURED
            )
        )

    def test_primary_artist_cannot_also_be_featured(self) -> None:
        song = SongFactory()
        credit = SongArtist(song=song, artist=song.primary_artist, role=ArtistRole.FEATURED)

        with pytest.raises(ValidationError, match="already the primary artist"):
            credit.clean()


class TestThemesAndAliases:
    def test_only_one_primary_theme(self) -> None:
        song = SongFactory()
        SongTheme.objects.create(song=song, theme=ThemeFactory(), is_primary=True)

        assert_db_rejects(
            lambda: SongTheme.objects.create(song=song, theme=ThemeFactory(), is_primary=True)
        )

    def test_secondary_themes_are_allowed(self) -> None:
        song = SongFactory()
        SongTheme.objects.create(song=song, theme=ThemeFactory(), is_primary=True)
        SongTheme.objects.create(song=song, theme=ThemeFactory(), is_primary=False)

        assert song.song_themes.count() == 2

    def test_alias_is_unique_per_song_ignoring_case(self) -> None:
        song = SongFactory()
        SongAlias.objects.create(song=song, alias="Despasito")

        assert_db_rejects(lambda: SongAlias.objects.create(song=song, alias="DESPASITO"))


class TestFacts:
    def test_source_url_is_required(self) -> None:
        assert_db_rejects(lambda: FactFactory(source_url=""))

    def test_blank_text_is_rejected(self) -> None:
        assert_db_rejects(lambda: FactFactory(text="  "))
