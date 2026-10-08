"""REST API of the game: /api/v1/puzzles/… and /api/v1/songs/search."""

from urllib.parse import quote_plus, urlparse
from uuid import UUID, uuid4

from django.conf import settings
from django.http import HttpRequest
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.catalog.models import ArtistRole, Song
from apps.game import errors, services
from apps.game.conf import game_config
from apps.game.models import DailyPuzzle, GameSession
from apps.game.search import search_songs
from apps.game.serializers import (
    ErrorSerializer,
    GuessRequestSerializer,
    GuessResponseSerializer,
    HintsSerializer,
    PuzzleStateSerializer,
    RevealSerializer,
    SongBriefSerializer,
)

EDITION_PARAM = OpenApiParameter(
    "edition", OpenApiTypes.STR, default="world", description="Edition code."
)
DAY_PARAM = OpenApiParameter(
    "day",
    OpenApiTypes.STR,
    OpenApiParameter.PATH,
    description="`today` or an archive date `YYYY-MM-DD` (up to 50 days back).",
)
ERRORS = {
    400: OpenApiResponse(ErrorSerializer),
    403: OpenApiResponse(ErrorSerializer),
    404: OpenApiResponse(ErrorSerializer),
    409: OpenApiResponse(ErrorSerializer),
    429: OpenApiResponse(ErrorSerializer),
}


# --- Shared request handling ------------------------------------------------


def origin_allowed(request: HttpRequest) -> bool:
    origin = request.headers.get("Origin")
    if not origin:
        return False
    if origin in settings.CSRF_TRUSTED_ORIGINS:
        return True
    return urlparse(origin).netloc == request.get_host()


class GameView(APIView):
    """Puzzle endpoints: need cookie consent, own the anonymous player cookie."""

    throttle_scope: str | None = None

    def initial(self, request: Request, *args, **kwargs) -> None:
        super().initial(request, *args, **kwargs)
        if request.COOKIES.get(settings.CONSENT_COOKIE_NAME) != settings.CONSENT_COOKIE_VERSION:
            raise errors.ConsentRequired
        # CSRF: no session auth here, so check the Origin of state-changing requests.
        if request.method not in ("GET", "HEAD", "OPTIONS") and not origin_allowed(request):
            raise errors.BadOrigin
        self.player_token, self.new_player = self._player_token(request)

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        if getattr(self, "new_player", False):
            response.set_cookie(
                settings.PLAYER_COOKIE_NAME,
                str(self.player_token),
                max_age=settings.PLAYER_COOKIE_AGE,
                httponly=True,
                secure=settings.PLAYER_COOKIE_SECURE,
                samesite="Lax",
            )
        # Per-player state: never cache it anywhere.
        response["Cache-Control"] = "no-store"
        return response

    @staticmethod
    def _player_token(request: Request) -> tuple[UUID, bool]:
        try:
            return UUID(request.COOKIES[settings.PLAYER_COOKIE_NAME]), False
        except (KeyError, ValueError):
            return uuid4(), True

    def session_for(self, request: Request, day: str) -> GameSession:
        edition = services.get_edition(request.query_params.get("edition", "world"))
        puzzle = services.get_puzzle(edition, services.resolve_day(edition, day))
        return services.get_or_create_session(puzzle, self.player_token)


def song_brief(song: Song) -> dict:
    return {"id": song.pk, "title": song.title, "artist": song.primary_artist.name}


def tiles_data(tiles) -> list[dict]:
    return [
        {"key": t.key, "value": t.value, "color": t.color, "direction": t.direction} for t in tiles
    ]


def hints_data(session: GameSession, attempts_used: int) -> list[dict]:
    return [
        {"number": i, "text": fact.text}
        for i, fact in enumerate(services.unlocked_hints(session, attempts_used), start=1)
    ]


def state_data(session: GameSession) -> dict:
    config = game_config()
    puzzle: DailyPuzzle = session.puzzle
    results = services.session_guesses(session)
    used = len(results)
    return {
        "edition": puzzle.edition.code,
        "date": puzzle.date,
        "number": puzzle.number,
        "max_attempts": config.max_attempts,
        "hint_attempts": list(config.hint_attempts),
        "year_yellow_range": config.year_yellow_range,
        "status": session.status,
        "attempts_used": used,
        "attempts_left": config.max_attempts - used,
        "guesses": [
            {
                "attempt": r.guess.attempt_number,
                "song": song_brief(r.guess.song),
                "tiles": tiles_data(r.tiles),
            }
            for r in results
        ],
        "hints": hints_data(session, used),
    }


# --- Endpoints --------------------------------------------------------------


class PuzzleView(GameView):
    @extend_schema(
        summary="Puzzle state for the player (creates the session on first visit)",
        parameters=[DAY_PARAM, EDITION_PARAM],
        responses={200: PuzzleStateSerializer, **ERRORS},
    )
    def get(self, request: Request, day: str) -> Response:
        session = self.session_for(request, day)
        return Response(PuzzleStateSerializer(state_data(session)).data)


class GuessView(GameView):
    throttle_scope = "guess"

    @extend_schema(
        summary="Make a guess",
        parameters=[DAY_PARAM, EDITION_PARAM],
        request=GuessRequestSerializer,
        responses={200: GuessResponseSerializer, **ERRORS},
    )
    def post(self, request: Request, day: str) -> Response:
        body = GuessRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        session = self.session_for(request, day)
        result = services.make_guess(session, body.validated_data["song_id"])
        session.refresh_from_db()
        used = result.guess.attempt_number
        return Response(
            GuessResponseSerializer(
                {
                    "guess": {
                        "attempt": used,
                        "song": song_brief(result.guess.song),
                        "tiles": tiles_data(result.tiles),
                    },
                    "status": session.status,
                    "attempts_used": used,
                    "attempts_left": game_config().max_attempts - used,
                    "hints": hints_data(session, used),
                }
            ).data
        )


class HintsView(GameView):
    @extend_schema(
        summary="Unlocked fact hints (after guesses 5 and 8; all once the game ends)",
        parameters=[DAY_PARAM, EDITION_PARAM],
        responses={200: HintsSerializer, **ERRORS},
    )
    def get(self, request: Request, day: str) -> Response:
        session = self.session_for(request, day)
        return Response({"hints": hints_data(session, session.guesses.count())})


class GiveUpView(GameView):
    @extend_schema(
        summary="Give up and end the game",
        parameters=[DAY_PARAM, EDITION_PARAM],
        request=None,
        responses={200: PuzzleStateSerializer, **ERRORS},
    )
    def post(self, request: Request, day: str) -> Response:
        session = services.give_up(self.session_for(request, day))
        return Response(PuzzleStateSerializer(state_data(session)).data)


class RevealView(GameView):
    @extend_schema(
        summary="The answer, its facts and a YouTube link (finished games only)",
        parameters=[DAY_PARAM, EDITION_PARAM],
        responses={200: RevealSerializer, **ERRORS},
    )
    def get(self, request: Request, day: str) -> Response:
        song = services.reveal(self.session_for(request, day))
        featured = [c.artist.name for c in song.song_artists.all() if c.role == ArtistRole.FEATURED]
        if song.youtube_video_id:
            youtube = f"https://www.youtube.com/watch?v={song.youtube_video_id}"
        else:
            query = quote_plus(f"{song.primary_artist.name} {song.title}")
            youtube = f"https://www.youtube.com/results?search_query={query}"
        return Response(
            RevealSerializer(
                {
                    "id": song.pk,
                    "title": song.title,
                    "artist": song.primary_artist.name,
                    "featured": featured,
                    "year": song.year,
                    "youtube_url": youtube,
                    "facts": [
                        {"text": f.text, "strength": f.strength, "source_url": f.source_url}
                        for f in services.revealed_facts(song)
                    ],
                }
            ).data
        )


class SongSearchView(APIView):
    """Autocomplete. Needs no cookies, so its answers can be cached."""

    throttle_scope = "search"

    @extend_schema(
        summary="Autocomplete over verified songs (title, alias or artist)",
        parameters=[
            OpenApiParameter(
                "q", OpenApiTypes.STR, required=True, description="At least 2 characters."
            ),
            EDITION_PARAM,
        ],
        responses={200: SongBriefSerializer(many=True), **ERRORS},
    )
    def get(self, request: Request) -> Response:
        edition = services.get_edition(request.query_params.get("edition", "world"))
        query = request.query_params.get("q", "").strip()
        songs = search_songs(edition, query) if len(query) >= 2 else []
        response = Response([song_brief(s) for s in songs])
        response["Cache-Control"] = "public, max-age=300"
        return response
