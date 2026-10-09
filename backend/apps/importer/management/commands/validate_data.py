from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.catalog.models import SongStatus
from apps.importer.quality import probable_duplicates, song_findings


class Command(BaseCommand):
    help = (
        "Data quality report: missing fields, odd years, facts without sources or giving "
        "the answer away, too many themes/styles, probable duplicates."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--status",
            action="append",
            choices=SongStatus.values,
            help="Only songs with this status (repeatable). Default: all.",
        )
        parser.add_argument(
            "--fail-on-error",
            action="store_true",
            help="Exit with an error when a verified song has a blocking problem (for CI).",
        )

    def handle(
        self, *args: Any, status: list[str] | None, fail_on_error: bool, **options: Any
    ) -> None:
        findings = song_findings(status)
        current = None
        for f in findings:
            if f.song != current:
                self.stdout.write(f.song)
                current = f.song
            style = self.style.ERROR if f.level == "error" else self.style.WARNING
            self.stdout.write(style(f"    {f.level}: {f.message}"))

        duplicates = probable_duplicates()
        if duplicates:
            self.stdout.write(self.style.WARNING("Probable duplicates:"))
            for a, b, similarity in duplicates:
                self.stdout.write(f"    {a}  ≈  {b}  ({similarity})")

        errors = sum(f.level == "error" for f in findings)
        warnings = len(findings) - errors
        self.stdout.write(
            self.style.SUCCESS(
                f"{errors} errors, {warnings} warnings, {len(duplicates)} probable duplicates."
            )
        )
        verified_errors = [f for f in findings if f.level == "error" and "[verified]" in f.song]
        if fail_on_error and verified_errors:
            raise CommandError(f"{len(verified_errors)} blocking problems in verified songs.")
