"""Compare a guessed song with the answer, tile by tile.

Pure functions over immutable DTOs: no database access happens here, so the
rules are easy to test exhaustively. ``apps.game.song_facts`` builds the DTOs.
"""

from dataclasses import dataclass
from enum import StrEnum


class Color(StrEnum):
    GREEN = "green"
    YELLOW = "yellow"
    GRAY = "gray"


class Direction(StrEnum):
    UP = "up"  # the answer is later
    DOWN = "down"  # the answer is earlier


class TileKey(StrEnum):
    ARTIST = "artist"
    YEAR = "year"
    GENRE = "genre"
    STYLE = "style"
    VOCAL = "vocal"
    THEME = "theme"
    COUNTRY = "country"
    LANGUAGE = "language"


TILE_ORDER: tuple[TileKey, ...] = tuple(TileKey)


@dataclass(frozen=True, slots=True)
class SongFacts:
    """Everything the tiles need about one song, with display values."""

    id: int
    primary_artist_id: int
    primary_artist_name: str
    artist_ids: frozenset[int]  # primary + featured
    person_ids: frozenset[int]  # members of every artist on the song
    year: int
    genre_id: int
    genre_name: str
    related_genre_ids: frozenset[int]
    style_ids: frozenset[int]
    style_genre_ids: frozenset[int]
    style_names: tuple[str, ...]
    vocal: str
    vocal_label: str
    theme_ids: frozenset[int]
    theme_group_ids: frozenset[int]
    primary_theme_name: str
    country_id: int
    country_name: str
    region_id: int
    language_id: int
    language_name: str


@dataclass(frozen=True, slots=True)
class Tile:
    key: TileKey
    value: str
    color: Color
    direction: Direction | None = None


def _color(green: bool, yellow: bool = False) -> Color:
    if green:
        return Color.GREEN
    return Color.YELLOW if yellow else Color.GRAY


def artist_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    # Yellow: a shared person (Freddie Mercury ↔ Queen) or any shared artist
    # credit, i.e. primary↔featured or featured↔featured.
    return Tile(
        TileKey.ARTIST,
        guess.primary_artist_name,
        _color(
            guess.primary_artist_id == answer.primary_artist_id,
            bool(guess.artist_ids & answer.artist_ids or guess.person_ids & answer.person_ids),
        ),
    )


def year_tile(guess: SongFacts, answer: SongFacts, yellow_range: int) -> Tile:
    if guess.year == answer.year:
        return Tile(TileKey.YEAR, str(guess.year), Color.GREEN)
    return Tile(
        TileKey.YEAR,
        str(guess.year),
        _color(False, abs(guess.year - answer.year) <= yellow_range),
        Direction.UP if answer.year > guess.year else Direction.DOWN,
    )


def genre_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    return Tile(
        TileKey.GENRE,
        guess.genre_name,
        _color(guess.genre_id == answer.genre_id, guess.genre_id in answer.related_genre_ids),
    )


def style_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    return Tile(
        TileKey.STYLE,
        ", ".join(guess.style_names),
        _color(
            bool(guess.style_ids & answer.style_ids),
            bool(guess.style_genre_ids & answer.style_genre_ids),
        ),
    )


def vocal_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    return Tile(TileKey.VOCAL, guess.vocal_label, _color(guess.vocal == answer.vocal))


def theme_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    return Tile(
        TileKey.THEME,
        guess.primary_theme_name,
        _color(
            bool(guess.theme_ids & answer.theme_ids),
            bool(guess.theme_group_ids & answer.theme_group_ids),
        ),
    )


def country_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    return Tile(
        TileKey.COUNTRY,
        guess.country_name,
        _color(guess.country_id == answer.country_id, guess.region_id == answer.region_id),
    )


def language_tile(guess: SongFacts, answer: SongFacts) -> Tile:
    return Tile(
        TileKey.LANGUAGE, guess.language_name, _color(guess.language_id == answer.language_id)
    )


def compare(guess: SongFacts, answer: SongFacts, *, year_yellow_range: int) -> list[Tile]:
    """The 8 tiles for ``guess`` against ``answer``, in display order."""
    return [
        artist_tile(guess, answer),
        year_tile(guess, answer, year_yellow_range),
        genre_tile(guess, answer),
        style_tile(guess, answer),
        vocal_tile(guess, answer),
        theme_tile(guess, answer),
        country_tile(guess, answer),
        language_tile(guess, answer),
    ]
