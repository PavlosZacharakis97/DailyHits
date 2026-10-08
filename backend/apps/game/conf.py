"""Game thresholds, read from settings.GAME so nothing is hard-coded."""

from dataclasses import dataclass

from django.conf import settings


@dataclass(frozen=True, slots=True)
class GameConfig:
    max_attempts: int
    year_yellow_range: int
    hint_attempts: tuple[int, ...]
    song_repeat_days: int
    archive_days: int
    schedule_lookahead_days: int


def game_config() -> GameConfig:
    raw = settings.GAME
    return GameConfig(
        max_attempts=raw["MAX_ATTEMPTS"],
        year_yellow_range=raw["YEAR_YELLOW_RANGE"],
        hint_attempts=tuple(raw["HINT_ATTEMPTS"]),
        song_repeat_days=raw["SONG_REPEAT_DAYS"],
        archive_days=raw["ARCHIVE_DAYS"],
        schedule_lookahead_days=raw["SCHEDULE_LOOKAHEAD_DAYS"],
    )
