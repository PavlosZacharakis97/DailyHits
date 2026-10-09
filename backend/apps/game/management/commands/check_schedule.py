from datetime import timedelta
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import Edition
from apps.game.dates import edition_today
from apps.game.models import DailyPuzzle
from apps.game.schedule import missing_dates, puzzle_errors, puzzle_warnings


class Command(BaseCommand):
    help = "Check the upcoming schedule: gaps, rule violations and balance warnings."

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--days", type=int, default=60, help="How many days ahead (default 60)."
        )
        parser.add_argument("--edition", help="Only this edition code (default: all active).")
        parser.add_argument(
            "--strict", action="store_true", help="Exit with an error on gaps or rule violations."
        )

    def handle(
        self, *args: Any, days: int, edition: str | None, strict: bool, **options: Any
    ) -> None:
        editions = Edition.objects.filter(is_active=True)
        if edition:
            editions = editions.filter(code=edition)
            if not editions.exists():
                raise CommandError(f"No active edition “{edition}”.")

        problems = 0
        for ed in editions:
            start = edition_today(ed)
            end = start + timedelta(days=days - 1)
            self.stdout.write(self.style.MIGRATE_HEADING(f"{ed} ({ed.code}): {start} → {end}"))

            gaps = missing_dates(ed, start, days)
            if gaps:
                problems += len(gaps)
                self.stdout.write(self.style.ERROR(f"  {len(gaps)} days without a puzzle:"))
                for line in _ranges(gaps):
                    self.stdout.write(f"    {line}")

            puzzles = DailyPuzzle.objects.filter(
                edition=ed, date__range=(start, end)
            ).select_related("song__primary_artist", "song__genre", "edition")
            warnings: dict[str, None] = {}  # ordered set: a 3-day run is reported once
            for puzzle in puzzles.order_by("date"):
                for messages in puzzle_errors(puzzle).values():
                    for message in messages:
                        problems += 1
                        self.stdout.write(
                            self.style.ERROR(f"  {puzzle.date} {puzzle.song}: {message}")
                        )
                warnings |= dict.fromkeys(puzzle_warnings(puzzle))
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"  warning: {warning}"))

        if problems:
            message = f"{problems} problems found."
            if strict:
                raise CommandError(message)
            self.stdout.write(self.style.ERROR(message))
        else:
            self.stdout.write(self.style.SUCCESS("Schedule is complete and valid."))


def _ranges(dates) -> list[str]:
    """Collapse consecutive dates into “start – end” ranges."""
    out = []
    start = prev = dates[0]
    for day in [*dates[1:], None]:
        if day is not None and day - prev == timedelta(days=1):
            prev = day
            continue
        out.append(
            str(start) if start == prev else f"{start} – {prev} ({(prev - start).days + 1} days)"
        )
        if day is not None:
            start = prev = day
    return out
