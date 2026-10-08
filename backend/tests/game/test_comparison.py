"""Every tile rule: green, yellow, gray and the edges. No database needed."""

from dataclasses import replace

import pytest

from apps.game.comparison import (
    TILE_ORDER,
    Color,
    Direction,
    SongFacts,
    Tile,
    TileKey,
    artist_tile,
    compare,
    country_tile,
    genre_tile,
    language_tile,
    style_tile,
    theme_tile,
    vocal_tile,
    year_tile,
)

ROCK, METAL, POP = 1, 2, 3
GRUNGE, HARD_ROCK, HEAVY_METAL, SYNTH_POP = 11, 12, 13, 14
LOVE, BREAKUP, PARTY = 21, 22, 23  # LOVE and BREAKUP are both in group 100
UK, SWEDEN, USA = 31, 32, 33
EUROPE, NORTH_AMERICA = 41, 42

ANSWER = SongFacts(
    id=1,
    primary_artist_id=100,
    primary_artist_name="Queen",
    artist_ids=frozenset({100}),
    person_ids=frozenset({1000, 1001}),
    year=1975,
    genre_id=ROCK,
    genre_name="Rock",
    related_genre_ids=frozenset({METAL}),
    style_ids=frozenset({HARD_ROCK}),
    style_genre_ids=frozenset({ROCK}),
    style_names=("Hard Rock",),
    vocal="male",
    vocal_label="Male",
    theme_ids=frozenset({LOVE}),
    theme_group_ids=frozenset({100}),
    primary_theme_name="Falling in Love",
    country_id=UK,
    country_name="United Kingdom",
    region_id=EUROPE,
    language_id=1,
    language_name="English",
)

# A guess that differs from the answer in every attribute.
STRANGER = SongFacts(
    id=2,
    primary_artist_id=200,
    primary_artist_name="ABBA",
    artist_ids=frozenset({200}),
    person_ids=frozenset({2000}),
    year=1999,
    genre_id=POP,
    genre_name="Pop",
    related_genre_ids=frozenset(),
    style_ids=frozenset({SYNTH_POP}),
    style_genre_ids=frozenset({POP}),
    style_names=("Synth-Pop", "Disco"),
    vocal="female",
    vocal_label="Female",
    theme_ids=frozenset({PARTY}),
    theme_group_ids=frozenset({200}),
    primary_theme_name="Party / Dancing",
    country_id=USA,
    country_name="United States",
    region_id=NORTH_AMERICA,
    language_id=2,
    language_name="Spanish",
)


def guess(**changes) -> SongFacts:
    return replace(STRANGER, **changes)


class TestArtist:
    def test_green_same_primary_artist(self) -> None:
        tile = artist_tile(guess(primary_artist_id=100, artist_ids=frozenset({100})), ANSWER)
        assert tile.color is Color.GREEN

    def test_green_even_if_featured_artists_differ(self) -> None:
        answer = replace(ANSWER, artist_ids=frozenset({100, 300}))
        tile = artist_tile(guess(primary_artist_id=100, artist_ids=frozenset({100, 400})), answer)
        assert tile.color is Color.GREEN

    def test_yellow_shared_band_member(self) -> None:
        # Freddie Mercury solo vs Queen
        tile = artist_tile(guess(person_ids=frozenset({1000})), ANSWER)
        assert tile.color is Color.YELLOW

    def test_yellow_primary_of_one_is_featured_on_the_other(self) -> None:
        tile = artist_tile(guess(artist_ids=frozenset({200, 100})), ANSWER)
        assert tile.color is Color.YELLOW

    def test_yellow_shared_featured_artist(self) -> None:
        answer = replace(ANSWER, artist_ids=frozenset({100, 500}))
        tile = artist_tile(guess(artist_ids=frozenset({200, 500})), answer)
        assert tile.color is Color.YELLOW

    def test_gray(self) -> None:
        assert artist_tile(STRANGER, ANSWER) == Tile(TileKey.ARTIST, "ABBA", Color.GRAY)


class TestYear:
    def test_green_has_no_direction(self) -> None:
        assert year_tile(guess(year=1975), ANSWER, 5) == Tile(TileKey.YEAR, "1975", Color.GREEN)

    @pytest.mark.parametrize(
        ("year", "color", "direction"),
        [
            (1970, Color.YELLOW, Direction.UP),  # exactly 5 earlier
            (1980, Color.YELLOW, Direction.DOWN),  # exactly 5 later
            (1974, Color.YELLOW, Direction.UP),
            (1976, Color.YELLOW, Direction.DOWN),
            (1969, Color.GRAY, Direction.UP),  # 6 years: just outside
            (1981, Color.GRAY, Direction.DOWN),
        ],
    )
    def test_range_and_direction(self, year: int, color: Color, direction: Direction) -> None:
        tile = year_tile(guess(year=year), ANSWER, 5)
        assert (tile.color, tile.direction) == (color, direction)

    def test_range_comes_from_the_argument(self) -> None:
        assert year_tile(guess(year=1972), ANSWER, 2).color is Color.GRAY
        assert year_tile(guess(year=1972), ANSWER, 3).color is Color.YELLOW


class TestGenre:
    def test_green(self) -> None:
        assert genre_tile(guess(genre_id=ROCK, genre_name="Rock"), ANSWER).color is Color.GREEN

    def test_yellow_related_genre(self) -> None:
        tile = genre_tile(guess(genre_id=METAL, genre_name="Metal"), ANSWER)
        assert tile == Tile(TileKey.GENRE, "Metal", Color.YELLOW)

    def test_gray(self) -> None:
        assert genre_tile(STRANGER, ANSWER).color is Color.GRAY


class TestStyle:
    def test_green_any_shared_style(self) -> None:
        tile = style_tile(guess(style_ids=frozenset({SYNTH_POP, HARD_ROCK})), ANSWER)
        assert tile.color is Color.GREEN

    def test_yellow_style_from_the_same_genre(self) -> None:
        tile = style_tile(
            guess(style_ids=frozenset({GRUNGE}), style_genre_ids=frozenset({ROCK})), ANSWER
        )
        assert tile.color is Color.YELLOW

    def test_gray_with_all_styles_listed(self) -> None:
        assert style_tile(STRANGER, ANSWER) == Tile(TileKey.STYLE, "Synth-Pop, Disco", Color.GRAY)

    def test_related_genre_style_is_not_yellow(self) -> None:
        tile = style_tile(
            guess(style_ids=frozenset({HEAVY_METAL}), style_genre_ids=frozenset({METAL})), ANSWER
        )
        assert tile.color is Color.GRAY


class TestVocal:
    def test_green(self) -> None:
        assert vocal_tile(guess(vocal="male"), ANSWER).color is Color.GREEN

    def test_gray_never_yellow(self) -> None:
        assert vocal_tile(guess(vocal="mixed"), ANSWER).color is Color.GRAY

    def test_value_is_the_label(self) -> None:
        assert vocal_tile(STRANGER, ANSWER).value == "Female"


class TestTheme:
    def test_green_any_shared_theme(self) -> None:
        tile = theme_tile(guess(theme_ids=frozenset({PARTY, LOVE})), ANSWER)
        assert tile.color is Color.GREEN

    def test_yellow_same_theme_group(self) -> None:
        tile = theme_tile(
            guess(theme_ids=frozenset({BREAKUP}), theme_group_ids=frozenset({100})), ANSWER
        )
        assert tile.color is Color.YELLOW

    def test_gray_shows_primary_theme(self) -> None:
        assert theme_tile(STRANGER, ANSWER) == Tile(TileKey.THEME, "Party / Dancing", Color.GRAY)


class TestCountry:
    def test_green(self) -> None:
        assert country_tile(guess(country_id=UK, region_id=EUROPE), ANSWER).color is Color.GREEN

    def test_yellow_same_region(self) -> None:
        tile = country_tile(
            guess(country_id=SWEDEN, country_name="Sweden", region_id=EUROPE), ANSWER
        )
        assert tile == Tile(TileKey.COUNTRY, "Sweden", Color.YELLOW)

    def test_gray(self) -> None:
        assert country_tile(STRANGER, ANSWER).color is Color.GRAY


class TestLanguage:
    def test_green(self) -> None:
        assert language_tile(guess(language_id=1), ANSWER).color is Color.GREEN

    def test_gray_never_yellow(self) -> None:
        assert language_tile(STRANGER, ANSWER) == Tile(TileKey.LANGUAGE, "Spanish", Color.GRAY)


class TestCompare:
    def test_answer_against_itself_is_all_green(self) -> None:
        tiles = compare(ANSWER, ANSWER, year_yellow_range=5)
        assert [t.key for t in tiles] == list(TILE_ORDER)
        assert {t.color for t in tiles} == {Color.GREEN}
        assert all(t.direction is None for t in tiles)

    def test_stranger_is_all_gray(self) -> None:
        tiles = compare(STRANGER, ANSWER, year_yellow_range=5)
        assert {t.color for t in tiles} == {Color.GRAY}
        assert tiles[1].direction is Direction.DOWN

    def test_values_describe_the_guess(self) -> None:
        tiles = compare(STRANGER, ANSWER, year_yellow_range=5)
        assert [t.value for t in tiles] == [
            "ABBA",
            "1999",
            "Pop",
            "Synth-Pop, Disco",
            "Female",
            "Party / Dancing",
            "United States",
            "Spanish",
        ]
