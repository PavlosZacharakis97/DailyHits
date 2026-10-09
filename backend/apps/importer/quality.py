"""Data quality report shared by the validate_data command."""

from dataclasses import dataclass

from django.db import connection

from apps.catalog.models import Song
from apps.catalog.validation import SONG_ISSUE_PREFETCH, Level, song_issues

OLDEST_PLAUSIBLE_YEAR = 1950
DUPLICATE_SIMILARITY = 0.6


@dataclass(frozen=True, slots=True)
class Finding:
    level: str  # "error" | "warning"
    song: str
    message: str


def song_findings(statuses: list[str] | None = None) -> list[Finding]:
    songs = Song.objects.select_related("primary_artist").prefetch_related(*SONG_ISSUE_PREFETCH)
    if statuses:
        songs = songs.filter(status__in=statuses)
    findings = []
    for song in songs.order_by("title"):
        label = f"{song.title} — {song.primary_artist} [{song.status}]"
        for issue in song_issues(song):
            findings.append(Finding(issue.level.value, label, str(issue.message)))
        if song.year is not None and song.year < OLDEST_PLAUSIBLE_YEAR:
            findings.append(
                Finding(
                    Level.WARNING.value, label, f"Year {song.year} is unusually early: check it."
                )
            )
    return findings


def probable_duplicates(threshold: float = DUPLICATE_SIMILARITY) -> list[tuple[str, str, float]]:
    """Pairs of songs whose “title artist” look alike (pg_trgm similarity)."""
    sql = """
        WITH s AS (
            SELECT song.id, song.title, artist.name AS artist,
                   unaccent(lower(song.title || ' ' || artist.name)) AS key
            FROM catalog_song song
            JOIN catalog_artist artist ON artist.id = song.primary_artist_id
        )
        SELECT a.title, a.artist, b.title, b.artist, similarity(a.key, b.key) AS sim
        FROM s a JOIN s b ON a.id < b.id
        WHERE similarity(a.key, b.key) >= %s
        ORDER BY sim DESC, a.title
    """
    with connection.cursor() as cursor:
        cursor.execute(sql, [threshold])
        return [
            (f"{t1} — {a1}", f"{t2} — {a2}", round(sim, 2))
            for t1, a1, t2, a2, sim in cursor.fetchall()
        ]
