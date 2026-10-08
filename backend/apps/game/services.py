"""Game rules on the server: puzzles, sessions, guesses, hints and the reveal.

The browser never decides anything: it only receives tiles for its own guesses,
unlocked hints, and the answer once the session is over.
"""

from dataclasses import dataclass
from datetime import date, timedelta
from uuid import UUID

from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

from apps.catalog.models import Edition, Fact, FactStrength, Song, SongStatus
from apps.game import errors
from apps.game.comparison import Tile, compare
from apps.game.conf import game_config
from apps.game.dates import edition_today
from apps.game.models import DailyPuzzle, GameSession, Guess, SessionStatus
from apps.game.song_facts import facts_for

STRENGTH_RANK = {FactStrength.EASY: 0, FactStrength.MEDIUM: 1, FactStrength.STRONG: 2}


@dataclass(frozen=True, slots=True)
class GuessResult:
    guess: Guess
    tiles: list[Tile]


# --- Puzzles ----------------------------------------------------------------


def get_edition(code: str) -> Edition:
    try:
        return Edition.objects.get(code=code, is_active=True)
    except Edition.DoesNotExist:
        raise errors.EditionNotFound from None


def resolve_day(edition: Edition, day: str) -> date:
    """“today” or an ISO date within the archive window; anything else is a 404.

    Future and too-old dates give the same 404 as a missing puzzle, so the API
    never reveals whether a puzzle exists.
    """
    today = edition_today(edition)
    if day == "today":
        return today
    try:
        requested = date.fromisoformat(day)
    except ValueError:
        raise errors.PuzzleNotFound from None
    if not today - timedelta(days=game_config().archive_days) <= requested <= today:
        raise errors.PuzzleNotFound
    return requested


def get_puzzle(edition: Edition, day: date) -> DailyPuzzle:
    puzzle = (
        DailyPuzzle.objects.select_related("edition", "song")
        .filter(edition=edition, date=day, song__status=SongStatus.VERIFIED)
        .first()
    )
    if puzzle is None:
        raise errors.PuzzleNotFound
    return puzzle


# --- Sessions ---------------------------------------------------------------


def get_or_create_session(puzzle: DailyPuzzle, player_token: UUID) -> GameSession:
    session = GameSession.objects.filter(puzzle=puzzle, player_token=player_token).first()
    if session is not None:
        return session
    try:
        with transaction.atomic():
            return GameSession.objects.create(puzzle=puzzle, player_token=player_token)
    except IntegrityError:
        # Two first requests raced; the other one created it.
        return GameSession.objects.get(puzzle=puzzle, player_token=player_token)


def session_guesses(session: GameSession) -> list[GuessResult]:
    """Past guesses with their tiles, recomputed from the catalogue."""
    guesses = list(
        session.guesses.select_related("song__primary_artist").order_by("attempt_number")
    )
    if not guesses:
        return []
    facts = facts_for([g.song_id for g in guesses] + [session.puzzle.song_id])
    answer = facts[session.puzzle.song_id]
    yellow = game_config().year_yellow_range
    return [
        GuessResult(g, compare(facts[g.song_id], answer, year_yellow_range=yellow)) for g in guesses
    ]


def make_guess(session: GameSession, song_id: int) -> GuessResult:
    config = game_config()
    with transaction.atomic():
        # Serialise guesses of one player so attempt numbers cannot collide.
        session = (
            GameSession.objects.select_for_update().select_related("puzzle").get(pk=session.pk)
        )
        if session.status != SessionStatus.IN_PROGRESS:
            raise errors.GameOver
        song = (
            Song.objects.select_related("primary_artist")
            .filter(
                pk=song_id,
                status=SongStatus.VERIFIED,
                editions=session.puzzle.edition_id,
            )
            .first()
        )
        if song is None:
            raise errors.UnknownSong
        if session.guesses.filter(song=song).exists():
            raise errors.AlreadyGuessed
        attempt = (session.guesses.aggregate(n=Max("attempt_number"))["n"] or 0) + 1
        if attempt > config.max_attempts:  # defensive: status should already be lost
            raise errors.NoAttemptsLeft

        guess = Guess.objects.create(session=session, song=song, attempt_number=attempt)
        if song.pk == session.puzzle.song_id:
            _finish(session, SessionStatus.WON)
        elif attempt >= config.max_attempts:
            _finish(session, SessionStatus.LOST)

    facts = facts_for({song.pk, session.puzzle.song_id})
    tiles = compare(
        facts[song.pk], facts[session.puzzle.song_id], year_yellow_range=config.year_yellow_range
    )
    return GuessResult(guess, tiles)


def give_up(session: GameSession) -> GameSession:
    with transaction.atomic():
        session = GameSession.objects.select_for_update().get(pk=session.pk)
        if session.status != SessionStatus.IN_PROGRESS:
            raise errors.GameOver
        _finish(session, SessionStatus.GAVE_UP)
    return session


def _finish(session: GameSession, status: str) -> None:
    session.status = status
    session.finished_at = timezone.now()
    session.save(update_fields=["status", "finished_at"])


# --- Hints and reveal -------------------------------------------------------


def hint_facts(song: Song) -> list[Fact]:
    """The two hint facts: the subtlest first, the most revealing second."""
    facts = sorted(
        song.facts.all(), key=lambda f: (STRENGTH_RANK.get(f.strength, 1), f.order, f.pk)
    )
    if len(facts) < 2:
        return facts
    return [facts[0], facts[-1]]


def revealed_facts(song: Song) -> list[Fact]:
    """All facts after the game: the two hints first, then the rest."""
    hints = hint_facts(song)
    return hints + [f for f in song.facts.all() if f not in hints]


def unlocked_hints(session: GameSession, attempts_used: int) -> list[Fact]:
    """Hints the player may see: by attempt count, or all once the game is over."""
    hints = hint_facts(session.puzzle.song)
    if session.status != SessionStatus.IN_PROGRESS:
        return hints
    thresholds = game_config().hint_attempts
    return [fact for fact, after in zip(hints, thresholds, strict=False) if attempts_used >= after]


def reveal(session: GameSession) -> Song:
    if session.status == SessionStatus.IN_PROGRESS:
        raise errors.GameInProgress
    return (
        Song.objects.select_related("primary_artist")
        .prefetch_related("song_artists__artist", "facts")
        .get(pk=session.puzzle.song_id)
    )
