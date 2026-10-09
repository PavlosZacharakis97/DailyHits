"""CSV import into draft songs.

Rules (see docs/import-format.md):
- New songs are created as drafts. Re-importing updates drafts in place
  (matched by MusicBrainz ID, else by title + primary artist), so no duplicates.
- Songs in review or verified are never overwritten; differences are reported.
- Unknown genres, styles, themes, countries, languages and editions are never
  created: the row is rejected with a message.
- A blank cell means “leave as is”, so data added in the admin survives re-imports.
- Each row is imported in its own savepoint: one bad row does not stop the rest.
"""

import csv
import re
import uuid
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction

from apps.catalog.models import (
    Artist,
    ArtistMember,
    ArtistRole,
    ArtistType,
    Country,
    Difficulty,
    Edition,
    Fact,
    FactStrength,
    Genre,
    Language,
    Person,
    Song,
    SongAlias,
    SongArtist,
    SongStatus,
    SongTheme,
    Style,
    Theme,
    Vocal,
)
from apps.catalog.validation import SONG_ISSUE_PREFETCH, verification_errors
from apps.importer.models import ImportBatch, ImportRow, RowStatus

LIST_SEPARATOR = "|"
MAX_FACTS = 5
YOUTUBE_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_url = URLValidator()


class RowRejected(Exception):
    def __init__(self, messages: list[str]) -> None:
        super().__init__("; ".join(messages))
        self.messages = messages


class _Rollback(Exception):
    """Raised to undo a dry run after the report is complete."""


@dataclass
class RowResult:
    row_number: int
    raw: dict[str, str]
    status: str
    song: Song | None = None
    messages: list[str] = field(default_factory=list)


@dataclass
class ImportReport:
    file_name: str
    dry_run: bool
    rows: list[RowResult]
    batch: ImportBatch | None = None

    @property
    def summary(self) -> dict[str, int]:
        counts = Counter(r.status for r in self.rows)
        return {status: counts.get(status, 0) for status in RowStatus.values}


# --- Reading ----------------------------------------------------------------


def read_rows(path: Path) -> list[dict[str, str]]:
    """Read a CSV saved by Excel, Numbers or Google Sheets (comma, semicolon or tab)."""
    text = path.read_text(encoding="utf-8-sig")
    try:
        dialect = csv.Sniffer().sniff(text.splitlines()[0] if text else ",", delimiters=",;\t")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(text.splitlines(), dialect=dialect)
    rows = []
    for row in reader:
        clean = {
            (key or "").strip().lower(): (value or "").strip()
            for key, value in row.items()
            if key is not None
        }
        if any(clean.values()):
            rows.append(clean)
    return rows


def split_list(value: str) -> list[str]:
    return [part.strip() for part in value.split(LIST_SEPARATOR) if part.strip()]


# --- Importer ---------------------------------------------------------------


@dataclass
class _Parsed:
    title: str
    artist: str
    artist_country: str
    artist_type: str
    scalars: dict[str, Any]
    styles: list[Style] | None
    themes: list[Theme] | None
    editions: list[Edition] | None
    featured: list[tuple[str, str]] | None
    members: list[str]
    aliases: list[str] | None
    sources: list[str] | None
    facts: list[dict[str, str]] | None
    warnings: list[str]


class SongImporter:
    def __init__(self, default_editions: Iterable[str] = ("world",)) -> None:
        self.genres = {g.name.lower(): g for g in Genre.objects.all()}
        self.styles = {s.name.lower(): s for s in Style.objects.all()}
        self.themes = {t.name.lower(): t for t in Theme.objects.all()}
        self.languages = {lang.iso_code: lang for lang in Language.objects.all()}
        self.languages |= {lang.name.lower(): lang for lang in self.languages.values()}
        self.countries = {c.iso_code: c for c in Country.objects.all()}
        self.editions = {e.code: e for e in Edition.objects.all()}
        self.default_editions = list(default_editions)

    # Public API ------------------------------------------------------------

    def run(self, path: Path, *, dry_run: bool = False) -> ImportReport:
        rows = read_rows(path)
        report = ImportReport(file_name=path.name, dry_run=dry_run, rows=[])
        try:
            with transaction.atomic():
                for number, raw in enumerate(rows, start=2):  # row 1 is the header
                    report.rows.append(self._import_row(number, raw))
                if dry_run:
                    raise _Rollback
                report.batch = self._save_report(report)
        except _Rollback:
            pass
        return report

    # Rows ------------------------------------------------------------------

    def _import_row(self, number: int, raw: dict[str, str]) -> RowResult:
        try:
            with transaction.atomic():
                parsed = self._parse(raw)
                status, song, messages = self._apply(parsed)
                return RowResult(number, raw, status, song, parsed.warnings + messages)
        except RowRejected as exc:
            return RowResult(number, raw, RowStatus.ERROR, messages=exc.messages)

    def _parse(self, raw: dict[str, str]) -> _Parsed:
        errors: list[str] = []
        warnings: list[str] = []
        get = lambda key: raw.get(key, "")  # noqa: E731

        title, artist = get("title"), get("artist")
        if not title:
            errors.append("title is required")
        if not artist:
            errors.append("artist is required")
        artist_type = get("artist_type").lower()
        if artist_type and artist_type not in ArtistType.values:
            errors.append(
                f"artist_type “{artist_type}” must be one of {', '.join(ArtistType.values)}"
            )

        scalars: dict[str, Any] = {}
        if year := get("year"):
            if year.isdigit():
                scalars["year"] = int(year)
            else:
                errors.append(f"year “{year}” is not a number")
        if genre := get("genre"):
            scalars["genre"] = self._lookup(self.genres, genre.lower(), "genre", genre, errors)
        if vocal := get("vocal").lower():
            if vocal in Vocal.values:
                scalars["vocal"] = vocal
            else:
                errors.append(f"vocal “{vocal}” must be one of {', '.join(Vocal.values)}")
        if language := get("language"):
            scalars["language"] = self._lookup(
                self.languages, language.lower(), "language", language, errors
            )
        if difficulty := get("difficulty").lower():
            if difficulty in Difficulty.values:
                scalars["difficulty"] = difficulty
            else:
                errors.append(
                    f"difficulty “{difficulty}” must be one of {', '.join(Difficulty.values)}"
                )
        if video := get("youtube_id"):
            if YOUTUBE_ID.match(video):
                scalars["youtube_video_id"] = video
            else:
                errors.append(
                    f"youtube_id “{video}” must be 11 characters (letters, digits, - or _)"
                )
        if mbid := get("musicbrainz_id"):
            try:
                scalars["musicbrainz_id"] = uuid.UUID(mbid)
            except ValueError:
                errors.append(f"musicbrainz_id “{mbid}” is not a valid ID")
        if notes := get("notes"):
            scalars["notes"] = notes

        styles = self._lookup_list(self.styles, get("styles"), "style", errors)
        themes = self._lookup_list(self.themes, get("themes"), "theme", errors)
        editions = [
            self._lookup(self.editions, code, "edition", code, errors)
            for code in (split_list(get("editions")) or self.default_editions)
        ]

        featured = None
        if get("featured"):
            featured = []
            for item in split_list(get("featured")):
                name, _, country = item.partition(":")
                featured.append((name.strip(), country.strip().upper()))

        sources = split_list(get("sources")) or None
        for url in sources or []:
            try:
                _url(url)
            except ValidationError:
                errors.append(f"source “{url}” is not a valid URL")

        facts = self._parse_facts(raw, errors)

        if errors:
            raise RowRejected(errors)
        return _Parsed(
            title=title,
            artist=artist,
            artist_country=get("artist_country").upper(),
            artist_type=artist_type,
            scalars=scalars,
            styles=styles,
            themes=themes,
            editions=editions,
            featured=featured,
            members=split_list(get("artist_members")),
            aliases=split_list(get("aliases")) or None,
            sources=sources,
            facts=facts,
            warnings=warnings,
        )

    def _parse_facts(self, raw: dict[str, str], errors: list[str]) -> list[dict[str, str]] | None:
        facts = []
        for n in range(1, MAX_FACTS + 1):
            text = raw.get(f"fact{n}", "")
            strength = raw.get(f"fact{n}_strength", "").lower()
            source = raw.get(f"fact{n}_source", "")
            if not (text or strength or source):
                continue
            if not text:
                errors.append(f"fact{n} has a strength or source but no text")
                continue
            if strength not in FactStrength.values:
                errors.append(f"fact{n}_strength must be one of {', '.join(FactStrength.values)}")
            if not source:
                errors.append(f"fact{n}_source is required")
            else:
                try:
                    _url(source)
                except ValidationError:
                    errors.append(f"fact{n}_source “{source}” is not a valid URL")
            facts.append({"text": text, "strength": strength, "source_url": source, "order": n})
        return facts or None

    @staticmethod
    def _lookup(table: dict, key: str, kind: str, shown: str, errors: list[str]):
        if key in table:
            return table[key]
        errors.append(f"unknown {kind} “{shown}” (it is not created automatically)")
        return None

    def _lookup_list(self, table: dict, value: str, kind: str, errors: list[str]) -> list | None:
        names = split_list(value)
        if not names:
            return None
        return [self._lookup(table, name.lower(), kind, name, errors) for name in names]

    # Writing ---------------------------------------------------------------

    def _artist(self, name: str, country_code: str, kind: str, label: str) -> Artist:
        matches = list(Artist.objects.filter(name__iexact=name)[:2])
        if len(matches) > 1:
            raise RowRejected([f"{label} “{name}” matches several artists; fix it in the admin"])
        if matches:
            return matches[0]
        if not country_code:
            raise RowRejected([f"{label} “{name}” is new: give its country (ISO code)"])
        country = self.countries.get(country_code.upper())
        if country is None:
            raise RowRejected([f"unknown country “{country_code}” for {label} “{name}”"])
        return Artist.objects.create(name=name, country=country, type=kind or ArtistType.SOLO)

    def _apply(self, p: _Parsed) -> tuple[str, Song, list[str]]:
        primary = self._artist(p.artist, p.artist_country, p.artist_type, "artist")
        for member in p.members:
            person = Person.objects.filter(name__iexact=member).first() or Person.objects.create(
                name=member
            )
            ArtistMember.objects.get_or_create(artist=primary, person=person)

        song = None
        if mbid := p.scalars.get("musicbrainz_id"):
            song = Song.objects.filter(musicbrainz_id=mbid).first()
        if song is None:
            song = Song.objects.filter(title__iexact=p.title, primary_artist=primary).first()

        if song is not None and song.status != SongStatus.DRAFT:
            differences = self._differences(song, p, primary)
            if not differences:
                return RowStatus.UNCHANGED, song, []
            return (
                RowStatus.CONFLICT,
                song,
                [f"song is in {song.get_status_display().lower()}, not overwritten", *differences],
            )

        created = song is None
        if not created and not self._differences(song, p, primary):
            return RowStatus.UNCHANGED, song, self._readiness(song)

        song = song or Song(primary_artist=primary)
        song.title = p.title
        song.primary_artist = primary
        for name, value in p.scalars.items():
            setattr(song, name, value)
        if p.sources is not None:
            song.sources = p.sources
        try:
            song.full_clean(exclude=["status"])
        except ValidationError as exc:
            raise RowRejected(
                [f"{k}: {' '.join(v)}" for k, v in exc.message_dict.items()]
            ) from None
        song.save()

        if p.styles is not None:
            song.styles.set(p.styles)
        if p.editions:
            song.editions.set(p.editions)
        if p.themes is not None:
            song.song_themes.all().delete()
            for i, theme in enumerate(dict.fromkeys(p.themes)):
                SongTheme.objects.create(song=song, theme=theme, is_primary=i == 0)
        if p.featured is not None:
            SongArtist.objects.filter(song=song, role=ArtistRole.FEATURED).delete()
            for name, country in p.featured:
                guest = self._artist(name, country, "", "featured artist")
                if guest.pk == primary.pk:
                    raise RowRejected([f"“{name}” is the primary artist, not featured"])
                SongArtist.objects.create(song=song, artist=guest, role=ArtistRole.FEATURED)
        if p.aliases is not None:
            song.aliases.all().delete()
            for alias in dict.fromkeys(a.lower() for a in p.aliases):
                original = next(a for a in p.aliases if a.lower() == alias)
                SongAlias.objects.create(song=song, alias=original)
        if p.facts is not None:
            song.facts.all().delete()
            for fact in p.facts:
                Fact.objects.create(song=song, **fact)

        return (RowStatus.CREATED if created else RowStatus.UPDATED), song, self._readiness(song)

    @staticmethod
    def _readiness(song: Song) -> list[str]:
        song = Song.objects.prefetch_related(*SONG_ISSUE_PREFETCH).get(pk=song.pk)
        errors = verification_errors(song)
        if not errors:
            return []
        return ["not ready to verify: " + " ".join(str(e.message) for e in errors)]

    @staticmethod
    def _differences(song: Song, p: _Parsed, primary: Artist) -> list[str]:
        diff = []

        def note(label: str, db: Any, csv_value: Any) -> None:
            if db != csv_value:
                diff.append(f"{label}: database “{db}” ≠ CSV “{csv_value}”")

        note("title", song.title, p.title)
        note("artist", song.primary_artist.name, primary.name)
        for name, value in p.scalars.items():
            note(name, getattr(song, name), value)
        if p.sources is not None:
            note("sources", song.sources, p.sources)
        if p.styles is not None:
            note(
                "styles",
                sorted(s.name for s in song.styles.all()),
                sorted(s.name for s in p.styles),
            )
        if p.editions:
            note(
                "editions",
                sorted(e.code for e in song.editions.all()),
                sorted(e.code for e in p.editions),
            )
        if p.themes is not None:
            db_themes = [
                t.theme.name for t in song.song_themes.order_by("-is_primary", "theme__name")
            ]
            note(
                "themes",
                [*db_themes[:1], *sorted(db_themes[1:])],
                [p.themes[0].name, *sorted(t.name for t in p.themes[1:])],
            )
        if p.featured is not None:
            note(
                "featured",
                sorted(
                    a.artist.name.lower()
                    for a in song.song_artists.filter(role=ArtistRole.FEATURED).select_related(
                        "artist"
                    )
                ),
                sorted(name.lower() for name, _ in p.featured),
            )
        if p.aliases is not None:
            note(
                "aliases",
                sorted(a.alias.lower() for a in song.aliases.all()),
                sorted({a.lower() for a in p.aliases}),
            )
        if p.facts is not None:
            note(
                "facts",
                [(f.text, f.strength, f.source_url) for f in song.facts.order_by("order", "pk")],
                [(f["text"], f["strength"], f["source_url"]) for f in p.facts],
            )
        return diff

    # Report ----------------------------------------------------------------

    @staticmethod
    def _save_report(report: ImportReport) -> ImportBatch:
        batch = ImportBatch.objects.create(
            file_name=report.file_name, dry_run=report.dry_run, summary=report.summary
        )
        ImportRow.objects.bulk_create(
            ImportRow(
                batch=batch,
                row_number=r.row_number,
                raw=r.raw,
                status=r.status,
                song=r.song if r.song is not None and r.song.pk else None,
                messages=r.messages,
            )
            for r in report.rows
        )
        return batch
