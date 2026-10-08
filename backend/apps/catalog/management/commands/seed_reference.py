from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from django.core.management.base import BaseCommand, CommandError
from django.db import models, transaction

from apps.catalog.models import (
    Country,
    Edition,
    Genre,
    Language,
    Region,
    Style,
    Theme,
    ThemeGroup,
)

SEED_FILE = Path(__file__).resolve().parents[2] / "seed" / "reference.yaml"


class Command(BaseCommand):
    help = "Load reference data (regions, countries, languages, genres, styles, themes, editions)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("--file", type=Path, default=SEED_FILE, help="YAML seed file.")

    def handle(self, *args: Any, file: Path, **options: Any) -> None:
        try:
            data = yaml.safe_load(file.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError) as exc:
            raise CommandError(f"Cannot read {file}: {exc}") from exc

        self.stats: Counter[str] = Counter()
        with transaction.atomic():
            self._seed(data)

        summary = ", ".join(f"{k}: {v}" for k, v in sorted(self.stats.items())) or "no changes"
        self.stdout.write(self.style.SUCCESS(f"Reference data is up to date ({summary})."))

    def _upsert(self, model: type[models.Model], lookup: dict, values: dict) -> models.Model:
        obj, created = model.objects.get_or_create(**lookup, defaults=values)
        name = model._meta.verbose_name_plural
        if created:
            self.stats[f"{name} created"] += 1
            return obj
        changed = [f for f, v in values.items() if getattr(obj, f) != v]
        if changed:
            for f in changed:
                setattr(obj, f, values[f])
            obj.save(update_fields=changed)
            self.stats[f"{name} updated"] += 1
        return obj

    def _seed(self, data: dict) -> None:
        for e in data["editions"]:
            self._upsert(
                Edition,
                {"code": e["code"]},
                {"name": e["name"], "timezone": e["timezone"], "is_active": e["is_active"]},
            )

        regions = {
            r["code"]: self._upsert(Region, {"code": r["code"]}, {"name": r["name"]})
            for r in data["regions"]
        }
        for region_code, countries in data["countries"].items():
            if region_code not in regions:
                raise CommandError(f"Unknown region code in countries: {region_code}")
            for iso, name in countries.items():
                self._upsert(
                    Country, {"iso_code": iso}, {"name": name, "region": regions[region_code]}
                )

        for iso, name in data["languages"].items():
            self._upsert(Language, {"iso_code": iso}, {"name": name})

        genres: dict[str, Genre] = {}
        for genre_name, styles in data["genres"].items():
            genre = self._upsert(Genre, {"name": genre_name}, {})
            genres[genre_name] = genre
            for style_name in styles:
                self._upsert(Style, {"name": style_name}, {"genre": genre})

        for left, right in data["related_genres"]:
            try:
                a, b = genres[left], genres[right]
            except KeyError as exc:
                raise CommandError(f"Unknown genre in related_genres: {exc}") from exc
            if not a.related.filter(pk=b.pk).exists():
                a.related.add(b)
                self.stats["genre links created"] += 1

        for group_order, (group_name, themes) in enumerate(data["themes"].items(), start=1):
            group = self._upsert(ThemeGroup, {"name": group_name}, {"order": group_order})
            for order, theme_name in enumerate(themes, start=1):
                self._upsert(Theme, {"name": theme_name}, {"group": group, "order": order})
