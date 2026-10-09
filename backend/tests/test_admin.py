"""Smoke and behaviour tests for the admin, the main data-entry tool."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.catalog.models import Song, SongStatus
from apps.game.models import DailyPuzzle
from tests.factories import (
    ArtistFactory,
    DailyPuzzleFactory,
    EditionFactory,
    GenreFactory,
    LanguageFactory,
    SongFactory,
    StyleFactory,
    ThemeFactory,
    complete_song,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def admin_client(client: Client) -> Client:
    user = get_user_model().objects.create_superuser("admin", "admin@example.com", "pw")
    client.force_login(user)
    return client


@pytest.mark.parametrize(
    "model",
    [
        "catalog.region",
        "catalog.country",
        "catalog.language",
        "catalog.genre",
        "catalog.style",
        "catalog.themegroup",
        "catalog.theme",
        "catalog.edition",
        "catalog.person",
        "catalog.artist",
        "catalog.song",
        "game.dailypuzzle",
        "game.gamesession",
        "importer.importbatch",
    ],
)
def test_changelist_and_add_pages_open(admin_client: Client, model: str) -> None:
    app, name = model.split(".")
    complete_song()

    assert admin_client.get(reverse(f"admin:{app}_{name}_changelist")).status_code == 200
    if model not in ("game.gamesession", "importer.importbatch"):
        assert admin_client.get(reverse(f"admin:{app}_{name}_add")).status_code == 200


def test_song_list_shows_problems(admin_client: Client) -> None:
    SongFactory(title="Half-done")

    response = admin_client.get(reverse("admin:catalog_song_changelist"))

    assert "No facts." in response.content.decode()


def test_song_list_filters_by_decade(admin_client: Client) -> None:
    complete_song(title="Eighties", year=1985)
    complete_song(title="Nineties", year=1995)

    response = admin_client.get(reverse("admin:catalog_song_changelist"), {"decade": "1980"})

    assert [s.title for s in response.context["cl"].result_list] == ["Eighties"]


def _inline_management(prefix: str, total: int = 0) -> dict[str, str]:
    return {
        f"{prefix}-TOTAL_FORMS": str(total),
        f"{prefix}-INITIAL_FORMS": "0",
        f"{prefix}-MIN_NUM_FORMS": "0",
        f"{prefix}-MAX_NUM_FORMS": "1000",
    }


def song_post_data(**overrides) -> dict[str, str]:
    genre = GenreFactory()
    data = {
        "title": "Brand New Song",
        "primary_artist": str(ArtistFactory().pk),
        "status": SongStatus.DRAFT,
        "difficulty": "medium",
        "editions": [str(EditionFactory().pk)],
        "year": "1999",
        "genre": str(genre.pk),
        "styles": [str(StyleFactory(genre=genre).pk)],
        "vocal": "female",
        "language": str(LanguageFactory().pk),
        "youtube_video_id": "",
        "musicbrainz_id": "",
        "sources": "[]",
        "notes": "",
        **_inline_management("song_artists"),
        **_inline_management("song_themes", 1),
        "song_themes-0-theme": str(ThemeFactory().pk),
        "song_themes-0-is_primary": "on",
        **_inline_management("aliases"),
        **_inline_management("facts", 3),
    }
    for i in range(3):
        data |= {
            f"facts-{i}-strength": "easy",
            f"facts-{i}-order": str(i),
            f"facts-{i}-text": f"A neutral detail number {i}.",
            f"facts-{i}-source_url": "https://en.wikipedia.org/wiki/Example",
        }
    data.update(overrides)
    return data


def test_complete_song_can_be_created_as_verified(admin_client: Client) -> None:
    response = admin_client.post(
        reverse("admin:catalog_song_add"), song_post_data(status=SongStatus.VERIFIED)
    )

    assert response.status_code == 302, response.context and response.context["errors"]
    song = Song.objects.get(title="Brand New Song")
    assert song.status == SongStatus.VERIFIED
    assert song.facts.count() == 3
    assert song.song_artists.get().artist_id == song.primary_artist_id


def test_incomplete_song_falls_back_to_review(admin_client: Client) -> None:
    data = song_post_data(status=SongStatus.VERIFIED, **_inline_management("facts", 1))

    admin_client.post(reverse("admin:catalog_song_add"), data)

    assert Song.objects.get(title="Brand New Song").status == SongStatus.REVIEW


def test_duplicate_song_is_rejected_by_the_form(admin_client: Client) -> None:
    existing = SongFactory(title="Hello")
    data = song_post_data(title="HELLO", primary_artist=str(existing.primary_artist_id))

    response = admin_client.post(reverse("admin:catalog_song_add"), data)

    assert response.status_code == 200
    assert "already has a song with this title" in response.content.decode()
    assert Song.objects.filter(title__iexact="hello").count() == 1


def test_future_year_is_rejected_by_the_form(admin_client: Client) -> None:
    response = admin_client.post(reverse("admin:catalog_song_add"), song_post_data(year="2999"))

    assert response.status_code == 200
    assert not Song.objects.filter(title="Brand New Song").exists()


def test_featured_artist_equal_to_primary_is_rejected(admin_client: Client) -> None:
    data = song_post_data()
    data |= _inline_management("song_artists", 1) | {
        "song_artists-0-artist": data["primary_artist"]
    }

    response = admin_client.post(reverse("admin:catalog_song_add"), data)

    assert response.status_code == 200
    assert "already the primary artist" in response.content.decode()


def test_bulk_verify_only_verifies_valid_songs(admin_client: Client) -> None:
    good = complete_song(status=SongStatus.REVIEW)
    bad = SongFactory(status=SongStatus.REVIEW)

    admin_client.post(
        reverse("admin:catalog_song_changelist"),
        {"action": "mark_verified", "_selected_action": [good.pk, bad.pk]},
    )

    good.refresh_from_db()
    bad.refresh_from_db()
    assert (good.status, bad.status) == (SongStatus.VERIFIED, SongStatus.REVIEW)


def test_bulk_review(admin_client: Client) -> None:
    song = SongFactory()

    admin_client.post(
        reverse("admin:catalog_song_changelist"),
        {"action": "mark_review", "_selected_action": [song.pk]},
    )

    song.refresh_from_db()
    assert song.status == SongStatus.REVIEW


def test_puzzle_list_warns_about_schedule_gaps(admin_client: Client) -> None:
    EditionFactory()

    response = admin_client.get(reverse("admin:game_dailypuzzle_changelist"))

    assert "no puzzle in the next 14 days" in response.content.decode()


def test_puzzle_with_unverified_song_is_rejected(admin_client: Client) -> None:
    song = complete_song(status=SongStatus.REVIEW)

    response = admin_client.post(
        reverse("admin:game_dailypuzzle_add"),
        {"edition": EditionFactory().pk, "date": "2030-01-01", "song": song.pk, "number": ""},
    )

    assert response.status_code == 200
    assert not DailyPuzzle.objects.exists()


def test_puzzle_is_created_with_next_number(admin_client: Client) -> None:
    DailyPuzzleFactory(number=7)

    admin_client.post(
        reverse("admin:game_dailypuzzle_add"),
        {"edition": EditionFactory().pk, "date": "2031-01-01", "song": complete_song().pk},
    )

    assert DailyPuzzle.objects.get(date="2031-01-01").number == 8


def test_admin_switches_to_russian(admin_client: Client) -> None:
    admin_client.post(reverse("set_language"), {"language": "ru", "next": "/admin/"})

    response = admin_client.get(reverse("admin:index"))

    page = response.content.decode()
    assert "Выйти" in page
    # Our own translations, not only Django's built-in ones.
    assert "Администрирование DailyHit" in page
    assert "Песни дня" in page


def test_import_report_page_opens(admin_client: Client) -> None:
    from apps.importer.models import ImportBatch, ImportRow

    batch = ImportBatch.objects.create(file_name="songs.csv", summary={"error": 1})
    ImportRow.objects.create(
        batch=batch, row_number=2, raw={"title": "X"}, status="error", messages=["unknown genre"]
    )

    response = admin_client.get(reverse("admin:importer_importbatch_change", args=[batch.pk]))

    assert response.status_code == 200
    assert "unknown genre" in response.content.decode()
