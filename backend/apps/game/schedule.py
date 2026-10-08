"""Schedule rules for DailyPuzzle, shared by model validation, admin and check_schedule."""

from datetime import date, timedelta

from django.utils.translation import gettext as _

from apps.catalog.models import Difficulty, Edition, SongStatus
from apps.game.conf import game_config
from apps.game.models import DailyPuzzle

CONSECUTIVE_WARNING_DAYS = 3


def puzzle_errors(puzzle: DailyPuzzle) -> dict[str, list[str]]:
    """Blocking problems: the puzzle must not be saved while any are present."""
    errors: dict[str, list[str]] = {}
    song = puzzle.song

    if song.status != SongStatus.VERIFIED:
        errors.setdefault("song", []).append(_("Only verified songs can be scheduled."))
    if not song.editions.filter(pk=puzzle.edition_id).exists():
        errors.setdefault("song", []).append(
            _("The song is not part of the “%(edition)s” edition.") % {"edition": puzzle.edition}
        )

    others = DailyPuzzle.objects.filter(edition_id=puzzle.edition_id).exclude(pk=puzzle.pk)

    repeat_days = game_config().song_repeat_days
    window = timedelta(days=repeat_days - 1)
    repeat = (
        others.filter(song_id=song.pk, date__range=(puzzle.date - window, puzzle.date + window))
        .order_by("date")
        .first()
    )
    if repeat is not None:
        errors.setdefault("song", []).append(
            _("Already scheduled on %(date)s; a song may repeat once in %(days)s days.")
            % {"date": repeat.date, "days": repeat_days}
        )

    neighbour = (
        others.filter(
            date__in=[puzzle.date - timedelta(days=1), puzzle.date + timedelta(days=1)],
            song__primary_artist_id=song.primary_artist_id,
        )
        .order_by("date")
        .first()
    )
    if neighbour is not None:
        errors.setdefault("song", []).append(
            _("%(artist)s is also on %(date)s; an artist cannot play two days in a row.")
            % {"artist": song.primary_artist, "date": neighbour.date}
        )
    return errors


def puzzle_warnings(puzzle: DailyPuzzle) -> list[str]:
    """Non-blocking balance hints: a 3-day run of one genre or of hard songs."""
    span = timedelta(days=CONSECUTIVE_WARNING_DAYS - 1)
    nearby = {
        p.date: p
        for p in DailyPuzzle.objects.filter(
            edition_id=puzzle.edition_id, date__range=(puzzle.date - span, puzzle.date + span)
        )
        .exclude(pk=puzzle.pk)
        .select_related("song")
    }
    nearby[puzzle.date] = puzzle

    warnings: list[str] = []
    for offset in range(CONSECUTIVE_WARNING_DAYS):
        start = puzzle.date - timedelta(days=CONSECUTIVE_WARNING_DAYS - 1 - offset)
        run = [nearby.get(start + timedelta(days=i)) for i in range(CONSECUTIVE_WARNING_DAYS)]
        if any(p is None for p in run):
            continue
        songs = [p.song for p in run]
        if songs[0].genre_id is not None and len({s.genre_id for s in songs}) == 1:
            warnings.append(
                _("%(days)s days in a row from %(date)s are all %(genre)s.")
                % {"days": CONSECUTIVE_WARNING_DAYS, "date": start, "genre": songs[0].genre}
            )
        if all(s.difficulty == Difficulty.HARD for s in songs):
            warnings.append(
                _("%(days)s hard songs in a row from %(date)s.")
                % {"days": CONSECUTIVE_WARNING_DAYS, "date": start}
            )
    return list(dict.fromkeys(warnings))


def missing_dates(edition: Edition, start: date, days: int) -> list[date]:
    """Dates in [start, start + days) that have no puzzle."""
    end = start + timedelta(days=days - 1)
    taken = set(
        DailyPuzzle.objects.filter(edition=edition, date__range=(start, end)).values_list(
            "date", flat=True
        )
    )
    return [
        start + timedelta(days=i) for i in range(days) if start + timedelta(days=i) not in taken
    ]


__all__ = ["missing_dates", "puzzle_errors", "puzzle_warnings"]
