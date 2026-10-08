from pathlib import Path
from typing import Any

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.catalog.models import (
    Artist,
    ArtistMember,
    ArtistRole,
    Country,
    Edition,
    Fact,
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
)
from apps.catalog.validation import SONG_ISSUE_PREFETCH, verification_errors

DEMO_FILE = Path(__file__).resolve().parents[2] / "seed" / "demo_songs.yaml"


class Command(BaseCommand):
    help = "Load demo songs for development. Requires seed_reference. Safe to re-run."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--file", type=Path, default=DEMO_FILE, help="YAML demo file.")
        parser.add_argument(
            "--status",
            choices=SongStatus.values,
            default=SongStatus.REVIEW,
            help="Status for songs that pass validation (default: review).",
        )
        parser.add_argument("--edition", default="world", help="Edition code for the songs.")

    def handle(self, *args: Any, file: Path, status: str, edition: str, **options: Any) -> None:
        try:
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CommandError(f"Cannot read {file}: {exc}") from exc
        try:
            edition_obj = Edition.objects.get(code=edition)
        except Edition.DoesNotExist as exc:
            raise CommandError(f"Edition {edition!r} not found; run seed_reference first.") from exc

        with transaction.atomic():
            people = {name: Person.objects.get_or_create(name=name)[0] for name in data["people"]}
            artists = {a["name"]: self._artist(a, people) for a in data["artists"]}
            for item in data["songs"]:
                song = self._song(item, artists, edition_obj)
                song = Song.objects.prefetch_related(*SONG_ISSUE_PREFETCH).get(pk=song.pk)
                errors = verification_errors(song)
                if errors and status == SongStatus.VERIFIED:
                    raise CommandError(f"{song}: " + " ".join(e.message for e in errors))
                Song.objects.filter(pk=song.pk).update(
                    status=SongStatus.DRAFT if errors else status
                )
                mark = " ".join(e.message for e in errors) if errors else "ok"
                self.stdout.write(f"  {song.title} — {song.primary_artist}: {mark}")

        self.stdout.write(self.style.SUCCESS(f"Loaded {len(data['songs'])} demo songs."))

    def _artist(self, data: dict, people: dict[str, Person]) -> Artist:
        artist, _ = Artist.objects.update_or_create(
            name=data["name"],
            defaults={
                "type": data["type"],
                "country": Country.objects.get(iso_code=data["country"]),
            },
        )
        for member in data["members"]:
            ArtistMember.objects.get_or_create(artist=artist, person=people[member])
        return artist

    def _song(self, data: dict, artists: dict[str, Artist], edition: Edition) -> Song:
        primary = artists[data["artist"]]
        song = Song.objects.filter(title__iexact=data["title"], primary_artist=primary).first()
        song = song or Song(primary_artist=primary)
        song.title = data["title"]
        song.year = data["year"]
        song.genre = Genre.objects.get(name=data["genre"])
        song.vocal = data["vocal"]
        song.language = Language.objects.get(iso_code=data["language"])
        song.difficulty = data["difficulty"]
        song.youtube_video_id = data["youtube"]
        song.sources = [data["source"]]
        song.full_clean(exclude=["status"])
        song.save()

        styles = list(Style.objects.filter(name__in=data["styles"]))
        if len(styles) != len(data["styles"]):
            raise CommandError(f"{song}: unknown style in {data['styles']}")
        song.styles.set(styles)
        song.editions.add(edition)

        SongArtist.objects.filter(song=song, role=ArtistRole.FEATURED).delete()
        for name in data.get("featured", []):
            SongArtist.objects.create(song=song, artist=artists[name], role=ArtistRole.FEATURED)

        song.song_themes.all().delete()
        for i, name in enumerate(data["themes"]):
            SongTheme.objects.create(
                song=song, theme=Theme.objects.get(name=name), is_primary=i == 0
            )

        song.aliases.all().delete()
        for alias in data.get("aliases", []):
            SongAlias.objects.create(song=song, alias=alias)

        song.facts.all().delete()
        for order, (strength, text) in enumerate(data["facts"], start=1):
            Fact.objects.create(
                song=song, text=text, strength=strength, order=order, source_url=data["source"]
            )
        return song
