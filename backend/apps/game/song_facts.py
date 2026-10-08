"""Build comparison DTOs from the database (the only DB-aware part of comparing)."""

from collections.abc import Iterable

from django.db.models import Prefetch, QuerySet

from apps.catalog.models import Song, SongTheme, Vocal
from apps.game.comparison import SongFacts


def facts_queryset() -> QuerySet[Song]:
    """Songs with everything ``to_facts`` reads, in a fixed number of queries."""
    return Song.objects.select_related(
        "primary_artist__country__region", "genre", "language"
    ).prefetch_related(
        "genre__related",
        "styles",
        Prefetch("song_themes", queryset=SongTheme.objects.select_related("theme")),
        "song_artists__artist__memberships",
    )


def to_facts(song: Song) -> SongFacts:
    credits = list(song.song_artists.all())
    themes = list(song.song_themes.all())
    primary_theme = next((t for t in themes if t.is_primary), themes[0] if themes else None)
    styles = sorted(song.styles.all(), key=lambda s: s.name)
    country = song.primary_artist.country
    return SongFacts(
        id=song.pk,
        primary_artist_id=song.primary_artist_id,
        primary_artist_name=song.primary_artist.name,
        artist_ids=frozenset(c.artist_id for c in credits),
        person_ids=frozenset(m.person_id for c in credits for m in c.artist.memberships.all()),
        year=song.year,
        genre_id=song.genre_id,
        genre_name=song.genre.name,
        related_genre_ids=frozenset(g.pk for g in song.genre.related.all()),
        style_ids=frozenset(s.pk for s in styles),
        style_genre_ids=frozenset(s.genre_id for s in styles),
        style_names=tuple(s.name for s in styles),
        vocal=song.vocal,
        vocal_label=str(Vocal(song.vocal).label),
        theme_ids=frozenset(t.theme_id for t in themes),
        theme_group_ids=frozenset(t.theme.group_id for t in themes),
        primary_theme_name=primary_theme.theme.name if primary_theme else "",
        country_id=country.pk,
        country_name=country.name,
        region_id=country.region_id,
        language_id=song.language_id,
        language_name=song.language.name,
    )


def facts_for(song_ids: Iterable[int]) -> dict[int, SongFacts]:
    return {song.pk: to_facts(song) for song in facts_queryset().filter(pk__in=list(song_ids))}
