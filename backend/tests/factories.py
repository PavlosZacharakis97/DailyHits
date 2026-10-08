from datetime import date, timedelta

import factory
from factory.django import DjangoModelFactory

from apps.catalog import models as m
from apps.game.models import DailyPuzzle


class RegionFactory(DjangoModelFactory):
    class Meta:
        model = m.Region
        django_get_or_create = ["code"]

    code = factory.Sequence(lambda n: f"region-{n}")
    name = factory.Sequence(lambda n: f"Region {n}")


class CountryFactory(DjangoModelFactory):
    class Meta:
        model = m.Country

    name = factory.Sequence(lambda n: f"Country {n}")
    iso_code = factory.Sequence(lambda n: f"{chr(65 + n // 26 % 26)}{chr(65 + n % 26)}")
    region = factory.SubFactory(RegionFactory)


class LanguageFactory(DjangoModelFactory):
    class Meta:
        model = m.Language
        django_get_or_create = ["iso_code"]

    name = factory.Sequence(lambda n: f"Language {n}")
    iso_code = factory.Sequence(lambda n: f"{chr(97 + n // 26 % 26)}{chr(97 + n % 26)}")


class GenreFactory(DjangoModelFactory):
    class Meta:
        model = m.Genre

    name = factory.Sequence(lambda n: f"Genre {n}")


class StyleFactory(DjangoModelFactory):
    class Meta:
        model = m.Style

    name = factory.Sequence(lambda n: f"Style {n}")
    genre = factory.SubFactory(GenreFactory)


class ThemeGroupFactory(DjangoModelFactory):
    class Meta:
        model = m.ThemeGroup

    name = factory.Sequence(lambda n: f"Theme group {n}")


class ThemeFactory(DjangoModelFactory):
    class Meta:
        model = m.Theme

    name = factory.Sequence(lambda n: f"Theme {n}")
    group = factory.SubFactory(ThemeGroupFactory)


class EditionFactory(DjangoModelFactory):
    class Meta:
        model = m.Edition
        django_get_or_create = ["code"]

    code = "world"
    name = "World Hits"


class PersonFactory(DjangoModelFactory):
    class Meta:
        model = m.Person

    name = factory.Sequence(lambda n: f"Person {n}")


class ArtistFactory(DjangoModelFactory):
    class Meta:
        model = m.Artist

    name = factory.Sequence(lambda n: f"Artist {n}")
    type = m.ArtistType.GROUP
    country = factory.SubFactory(CountryFactory)


class SongFactory(DjangoModelFactory):
    """A draft song with only the required fields."""

    class Meta:
        model = m.Song

    title = factory.Sequence(lambda n: f"Song {n}")
    primary_artist = factory.SubFactory(ArtistFactory)


class FactFactory(DjangoModelFactory):
    class Meta:
        model = m.Fact

    song = factory.SubFactory(SongFactory)
    text = factory.Sequence(lambda n: f"An interesting detail number {n}.")
    strength = m.FactStrength.EASY
    order = factory.Sequence(lambda n: n)
    source_url = "https://en.wikipedia.org/wiki/Example"


def complete_song(**kwargs) -> m.Song:
    """A song that passes verification, saved as verified unless told otherwise."""
    kwargs.setdefault("status", m.SongStatus.VERIFIED)
    genre = kwargs.pop("genre", None) or GenreFactory()
    song = SongFactory(
        year=kwargs.pop("year", 1985),
        genre=genre,
        vocal=kwargs.pop("vocal", m.Vocal.MALE),
        language=kwargs.pop("language", None) or LanguageFactory(iso_code="en", name="English"),
        youtube_video_id="dQw4w9WgXcQ",
        sources=["https://en.wikipedia.org/wiki/Example"],
        **kwargs,
    )
    song.styles.add(StyleFactory(genre=genre))
    m.SongTheme.objects.create(song=song, theme=ThemeFactory(), is_primary=True)
    song.editions.add(EditionFactory())
    for order in range(3):
        FactFactory(song=song, order=order)
    return song


class DailyPuzzleFactory(DjangoModelFactory):
    class Meta:
        model = DailyPuzzle

    edition = factory.SubFactory(EditionFactory)
    song = factory.LazyFunction(complete_song)
    date = factory.Sequence(lambda n: date(2030, 1, 1) + timedelta(days=n))
