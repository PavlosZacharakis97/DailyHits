"""Game API: rules, errors, cookies, and above all that the answer never leaks."""

import json
from datetime import timedelta

import pytest
from django.core.cache import cache
from django.test import Client
from rest_framework.throttling import ScopedRateThrottle

from apps.catalog.models import ArtistRole, SongAlias, SongArtist, SongStatus
from apps.game.dates import edition_today
from apps.game.models import GameSession, SessionStatus
from tests.factories import (
    ArtistFactory,
    DailyPuzzleFactory,
    EditionFactory,
    FactFactory,
    complete_song,
)

pytestmark = pytest.mark.django_db

ORIGIN = "http://localhost:5173"
API = "/api/v1"


@pytest.fixture(autouse=True)
def _clean_cache() -> None:
    cache.clear()  # throttling counters


@pytest.fixture
def edition():
    return EditionFactory()


@pytest.fixture
def answer(edition):
    song = complete_song(title="Bohemian Rhapsody", primary_artist=ArtistFactory(name="Queen"))
    song.facts.all().delete()
    for order, strength in enumerate(["strong", "easy", "medium"]):
        FactFactory(song=song, order=order, strength=strength, text=f"{strength} fact")
    return song


@pytest.fixture
def puzzle(edition, answer):
    return DailyPuzzleFactory(edition=edition, song=answer, date=edition_today(edition), number=7)


@pytest.fixture
def others(edition):
    return [complete_song(title=f"Other song {i}") for i in range(12)]


@pytest.fixture
def player() -> Client:
    client = Client()
    client.cookies["dh_consent"] = "1"
    return client


def guess(client: Client, song_id: int, day: str = "today"):
    return client.post(
        f"{API}/puzzles/{day}/guess",
        data=json.dumps({"song_id": song_id}),
        content_type="application/json",
        HTTP_ORIGIN=ORIGIN,
    )


def error_code(response) -> str:
    return response.json()["error"]["code"]


class TestConsentAndCookies:
    def test_game_needs_consent(self, puzzle) -> None:
        response = Client().get(f"{API}/puzzles/today")

        assert response.status_code == 403
        assert error_code(response) == "consent_required"
        assert "dh_player" not in response.cookies

    def test_first_visit_sets_an_anonymous_http_only_cookie(self, player, puzzle) -> None:
        response = player.get(f"{API}/puzzles/today")

        cookie = response.cookies["dh_player"]
        assert response.status_code == 200
        assert cookie["httponly"] and cookie["samesite"] == "Lax"
        assert GameSession.objects.get().player_token.hex == cookie.value.replace("-", "")

    def test_the_cookie_keeps_the_same_session(self, player, puzzle) -> None:
        player.get(f"{API}/puzzles/today")
        response = player.get(f"{API}/puzzles/today")

        assert "dh_player" not in response.cookies
        assert GameSession.objects.count() == 1

    def test_invalid_cookie_is_replaced(self, player, puzzle) -> None:
        player.cookies["dh_player"] = "not-a-uuid"

        assert "dh_player" in player.get(f"{API}/puzzles/today").cookies

    def test_state_is_never_cached(self, player, puzzle) -> None:
        assert player.get(f"{API}/puzzles/today")["Cache-Control"] == "no-store"


class TestOrigin:
    def test_post_without_origin_is_rejected(self, player, puzzle, others) -> None:
        response = player.post(
            f"{API}/puzzles/today/guess",
            data=json.dumps({"song_id": others[0].pk}),
            content_type="application/json",
        )
        assert error_code(response) == "bad_origin"

    def test_post_from_another_site_is_rejected(self, player, puzzle, others) -> None:
        response = player.post(f"{API}/puzzles/today/give-up", HTTP_ORIGIN="https://evil.example")
        assert response.status_code == 403
        assert error_code(response) == "bad_origin"

    def test_same_host_origin_is_accepted(self, player, puzzle) -> None:
        response = player.post(f"{API}/puzzles/today/give-up", HTTP_ORIGIN="http://testserver")
        assert response.status_code == 200


class TestPuzzleState:
    def test_new_game(self, player, puzzle) -> None:
        data = player.get(f"{API}/puzzles/today").json()

        assert data == {
            "edition": "world",
            "date": puzzle.date.isoformat(),
            "number": 7,
            "max_attempts": 10,
            "hint_attempts": [5, 8],
            "year_yellow_range": 5,
            "status": "in_progress",
            "attempts_used": 0,
            "attempts_left": 10,
            "guesses": [],
            "hints": [],
        }

    def test_guesses_are_replayed_with_tiles(self, player, puzzle, others) -> None:
        guess(player, others[0].pk)
        guess(player, others[1].pk)

        data = player.get(f"{API}/puzzles/today").json()

        assert [g["attempt"] for g in data["guesses"]] == [1, 2]
        assert data["guesses"][0]["song"]["title"] == "Other song 0"
        assert [t["key"] for t in data["guesses"][0]["tiles"]] == [
            "artist",
            "year",
            "genre",
            "style",
            "vocal",
            "theme",
            "country",
            "language",
        ]

    def test_no_puzzle_today(self, player, edition) -> None:
        assert error_code(player.get(f"{API}/puzzles/today")) == "puzzle_not_found"

    def test_unknown_edition(self, player, puzzle) -> None:
        response = player.get(f"{API}/puzzles/today", {"edition": "mars"})
        assert error_code(response) == "edition_not_found"

    def test_unverified_puzzle_song_is_hidden(self, player, puzzle, answer) -> None:
        answer.status = SongStatus.REVIEW
        answer.save()
        assert player.get(f"{API}/puzzles/today").status_code == 404


class TestGuessing:
    def test_wrong_guess(self, player, puzzle, others) -> None:
        data = guess(player, others[0].pk).json()

        assert data["status"] == "in_progress"
        assert data["attempts_used"] == 1 and data["attempts_left"] == 9
        assert len(data["guess"]["tiles"]) == 8

    def test_right_guess_wins(self, player, puzzle, answer) -> None:
        data = guess(player, answer.pk).json()

        assert data["status"] == "won"
        assert {t["color"] for t in data["guess"]["tiles"]} == {"green"}
        assert len(data["hints"]) == 2  # all hints once the game is over

    def test_ten_wrong_guesses_lose(self, player, puzzle, others) -> None:
        for song in others[:10]:
            response = guess(player, song.pk)

        assert response.json()["status"] == "lost"
        assert error_code(guess(player, others[10].pk)) == "game_over"
        assert GameSession.objects.get().finished_at is not None

    def test_same_song_twice(self, player, puzzle, others) -> None:
        guess(player, others[0].pk)
        response = guess(player, others[0].pk)

        assert response.status_code == 409
        assert error_code(response) == "already_guessed"

    @pytest.mark.parametrize("problem", ["missing", "unverified", "other_edition"])
    def test_unknown_song(self, player, puzzle, others, problem) -> None:
        song_id = 999_999
        if problem == "unverified":
            others[0].status = SongStatus.REVIEW
            others[0].save()
            song_id = others[0].pk
        elif problem == "other_edition":
            others[0].editions.set([EditionFactory(code="ru", name="RU")])
            song_id = others[0].pk

        response = guess(player, song_id)

        assert response.status_code == 400
        assert error_code(response) == "unknown_song"

    def test_invalid_body(self, player, puzzle) -> None:
        response = player.post(
            f"{API}/puzzles/today/guess",
            data=json.dumps({"song_id": "abc"}),
            content_type="application/json",
            HTTP_ORIGIN=ORIGIN,
        )
        body = response.json()["error"]
        assert response.status_code == 400
        assert body["code"] == "invalid" and "song_id" in body["details"]

    def test_give_up_then_no_more_guesses(self, player, puzzle, others) -> None:
        data = player.post(f"{API}/puzzles/today/give-up", HTTP_ORIGIN=ORIGIN).json()

        assert data["status"] == "gave_up"
        assert error_code(guess(player, others[0].pk)) == "game_over"
        assert (
            error_code(player.post(f"{API}/puzzles/today/give-up", HTTP_ORIGIN=ORIGIN))
            == "game_over"
        )

    def test_players_are_independent(self, player, puzzle, answer) -> None:
        guess(player, answer.pk)
        other = Client()
        other.cookies["dh_consent"] = "1"

        assert other.get(f"{API}/puzzles/today").json()["status"] == "in_progress"

    def test_tiles_are_english_for_any_browser(self, player, puzzle, others) -> None:
        response = player.post(
            f"{API}/puzzles/today/guess",
            data=json.dumps({"song_id": others[0].pk}),
            content_type="application/json",
            HTTP_ORIGIN=ORIGIN,
            HTTP_ACCEPT_LANGUAGE="ru",
        )
        vocal = next(t for t in response.json()["guess"]["tiles"] if t["key"] == "vocal")
        assert vocal["value"] == "Male"


class TestHints:
    def hints(self, client) -> list[str]:
        return [h["text"] for h in client.get(f"{API}/puzzles/today/hints").json()["hints"]]

    def test_unlock_after_guesses_5_and_8(self, player, puzzle, others) -> None:
        unlocked = []
        for song in others[:8]:
            guess(player, song.pk)
            unlocked.append(len(self.hints(player)))

        assert unlocked == [0, 0, 0, 0, 1, 1, 1, 2]

    def test_subtlest_first_then_most_revealing(self, player, puzzle, others) -> None:
        for song in others[:8]:
            guess(player, song.pk)

        assert self.hints(player) == ["easy fact", "strong fact"]

    def test_guess_response_includes_new_hint(self, player, puzzle, others) -> None:
        for song in others[:4]:
            guess(player, song.pk)
        assert guess(player, others[4].pk).json()["hints"] == [{"number": 1, "text": "easy fact"}]


class TestReveal:
    def test_forbidden_while_playing(self, player, puzzle) -> None:
        response = player.get(f"{API}/puzzles/today/reveal")
        assert response.status_code == 403
        assert error_code(response) == "game_in_progress"

    def test_after_the_game(self, player, puzzle, answer) -> None:
        SongArtist.objects.create(
            song=answer, artist=ArtistFactory(name="Guest"), role=ArtistRole.FEATURED
        )
        guess(player, answer.pk)

        data = player.get(f"{API}/puzzles/today/reveal").json()

        assert data["title"] == "Bohemian Rhapsody"
        assert (data["artist"], data["featured"], data["year"]) == ("Queen", ["Guest"], 1985)
        assert data["youtube_url"] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        assert [f["text"] for f in data["facts"]] == ["easy fact", "strong fact", "medium fact"]

    def test_youtube_search_link_without_video(self, player, puzzle, answer) -> None:
        answer.youtube_video_id = None
        answer.save()
        player.post(f"{API}/puzzles/today/give-up", HTTP_ORIGIN=ORIGIN)

        url = player.get(f"{API}/puzzles/today/reveal").json()["youtube_url"]
        assert url == "https://www.youtube.com/results?search_query=Queen+Bohemian+Rhapsody"


class TestArchive:
    def test_past_puzzle_has_its_own_session(self, player, edition, puzzle, others) -> None:
        day = puzzle.date - timedelta(days=3)
        DailyPuzzleFactory(edition=edition, song=others[0], date=day)

        data = player.get(f"{API}/puzzles/{day.isoformat()}").json()

        assert data["date"] == day.isoformat()
        assert guess(player, others[0].pk, day.isoformat()).json()["status"] == "won"
        assert player.get(f"{API}/puzzles/today").json()["status"] == "in_progress"

    @pytest.mark.parametrize("days_ago", [-1, 51])
    def test_future_and_too_old_dates_look_missing(
        self, player, edition, puzzle, others, days_ago
    ) -> None:
        day = puzzle.date - timedelta(days=days_ago)
        DailyPuzzleFactory(edition=edition, song=others[0], date=day)

        response = player.get(f"{API}/puzzles/{day.isoformat()}")
        assert response.status_code == 404
        assert error_code(response) == "puzzle_not_found"

    def test_fifty_days_back_is_allowed(self, player, edition, puzzle, others) -> None:
        day = puzzle.date - timedelta(days=50)
        DailyPuzzleFactory(edition=edition, song=others[0], date=day)
        assert player.get(f"{API}/puzzles/{day.isoformat()}").status_code == 200

    def test_impossible_date(self, player, puzzle) -> None:
        assert error_code(player.get(f"{API}/puzzles/2026-02-31")) == "puzzle_not_found"


class TestSearch:
    def search(self, q: str, **params) -> list[str]:
        response = Client().get(f"{API}/songs/search", {"q": q, **params})
        assert response.status_code == 200
        return [s["title"] for s in response.json()]

    def test_needs_two_characters(self, others) -> None:
        assert self.search("o") == []

    def test_returns_only_id_title_artist(self, others) -> None:
        song = Client().get(f"{API}/songs/search", {"q": "Other song 1"}).json()[0]
        assert set(song) == {"id", "title", "artist"}

    def test_at_most_ten_results(self, others) -> None:
        assert len(self.search("other")) == 10

    def test_title_prefix_ranks_first(self, edition) -> None:
        complete_song(title="Dreams")
        complete_song(title="Sweet Dreams")
        assert self.search("dreams") == ["Dreams", "Sweet Dreams"]

    def test_case_and_accents_are_ignored(self, edition) -> None:
        complete_song(title="Alors on danse", primary_artist=ArtistFactory(name="Stromaé"))
        assert self.search("STROMAE") == ["Alors on danse"]

    def test_typo_is_tolerated(self, edition) -> None:
        complete_song(title="Bohemian Rhapsody")
        assert self.search("bohemain") == ["Bohemian Rhapsody"]

    def test_alias(self, edition) -> None:
        song = complete_song(title="Despacito")
        SongAlias.objects.create(song=song, alias="Деспасито")
        assert self.search("деспа") == ["Despacito"]

    def test_featured_artist(self, edition) -> None:
        song = complete_song(title="Despacito")
        SongArtist.objects.create(song=song, artist=ArtistFactory(name="Daddy Yankee"))
        assert self.search("yankee") == ["Despacito"]

    def test_only_verified_songs_of_the_edition(self, edition) -> None:
        complete_song(title="Hidden draft", status=SongStatus.DRAFT)
        other = complete_song(title="Hidden elsewhere")
        other.editions.set([EditionFactory(code="ru", name="RU")])
        assert self.search("hidden") == []

    def test_results_are_cacheable(self, others) -> None:
        response = Client().get(f"{API}/songs/search", {"q": "other"})
        assert response["Cache-Control"] == "public, max-age=300"


class TestErrorsAndLimits:
    def test_unknown_endpoint_is_json(self) -> None:
        response = Client().get(f"{API}/nope")
        assert response.status_code == 404
        assert error_code(response) == "not_found"

    def test_search_is_throttled(self, others, monkeypatch) -> None:
        monkeypatch.setattr(
            ScopedRateThrottle, "THROTTLE_RATES", {"search": "2/min", "guess": "2/min"}
        )
        client = Client()
        codes = [client.get(f"{API}/songs/search", {"q": "other"}).status_code for _ in range(3)]

        assert codes == [200, 200, 429]
        body = client.get(f"{API}/songs/search", {"q": "other"}).json()["error"]
        assert body["code"] == "throttled" and body["details"]["retry_after"] > 0

    def test_guess_is_throttled(self, player, puzzle, others, monkeypatch) -> None:
        monkeypatch.setattr(
            ScopedRateThrottle, "THROTTLE_RATES", {"search": "2/min", "guess": "2/min"}
        )
        codes = [guess(player, s.pk).status_code for s in others[:3]]
        assert codes == [200, 200, 429]

    def test_openapi_schema_is_served(self) -> None:
        response = Client().get(f"{API}/schema/", HTTP_ACCEPT="application/json")
        paths = json.loads(response.content)["paths"]
        assert {"/api/v1/puzzles/{day}/guess", "/api/v1/songs/search"} <= set(paths)


class TestTheAnswerNeverLeaks:
    """Spec §8 (docs/spec.md): no in-progress response may contain the answer id or title."""

    @staticmethod
    def ids_in(payload) -> set:
        found = set()
        if isinstance(payload, dict):
            for key, value in payload.items():
                if key == "id":
                    found.add(value)
                found |= TestTheAnswerNeverLeaks.ids_in(value)
        elif isinstance(payload, list):
            for item in payload:
                found |= TestTheAnswerNeverLeaks.ids_in(item)
        return found

    def assert_clean(self, response, answer) -> None:
        text = response.content.decode()
        assert answer.title.lower() not in text.lower()
        if response.headers.get("Content-Type", "").startswith("application/json"):
            assert answer.pk not in self.ids_in(response.json())

    def test_every_in_progress_response(self, player, puzzle, answer, others) -> None:
        responses = [player.get(f"{API}/puzzles/today")]
        for song in others[:9]:  # up to the last attempt, all hints unlocked
            responses.append(guess(player, song.pk))
            responses.append(player.get(f"{API}/puzzles/today/hints"))
        responses.append(player.get(f"{API}/puzzles/today"))
        responses.append(player.get(f"{API}/puzzles/today/reveal"))
        responses.append(guess(player, others[0].pk))  # error path

        assert GameSession.objects.get().status == SessionStatus.IN_PROGRESS
        for response in responses:
            self.assert_clean(response, answer)

    def test_search_cannot_be_used_to_find_the_answer(self, player, puzzle, answer, others) -> None:
        # Searching is allowed to list the answer like any song, but carries no marker.
        results = Client().get(f"{API}/songs/search", {"q": "bohemian"}).json()
        assert results == [{"id": answer.pk, "title": answer.title, "artist": "Queen"}]
