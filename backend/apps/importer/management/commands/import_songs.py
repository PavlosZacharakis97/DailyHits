from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError

from apps.importer.models import RowStatus
from apps.importer.services import SongImporter

STYLE = {
    RowStatus.CREATED: "SUCCESS",
    RowStatus.UPDATED: "SUCCESS",
    RowStatus.UNCHANGED: "HTTP_INFO",
    RowStatus.CONFLICT: "WARNING",
    RowStatus.ERROR: "ERROR",
}


class Command(BaseCommand):
    help = "Import songs from a CSV file as drafts (format: docs/import-format.md)."

    def add_arguments(self, parser) -> None:
        parser.add_argument("csv", type=Path, help="Path to the CSV file.")
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Check the file and show the report; save nothing.",
        )
        parser.add_argument(
            "--edition",
            action="append",
            dest="editions",
            help="Edition code for rows without an “editions” column (default: world).",
        )

    def handle(
        self, *args: Any, csv: Path, dry_run: bool, editions: list[str] | None, **options: Any
    ) -> None:
        if not csv.is_file():
            raise CommandError(f"File not found: {csv}")
        try:
            report = SongImporter(default_editions=editions or ["world"]).run(csv, dry_run=dry_run)
        except UnicodeDecodeError as exc:
            raise CommandError(f"{csv} is not UTF-8 text: save it as “CSV UTF-8”.") from exc

        for row in report.rows:
            style = getattr(self.style, STYLE[row.status])
            title = row.raw.get("title") or "?"
            self.stdout.write(style(f"row {row.row_number}: {row.status} — {title}"))
            for message in row.messages:
                self.stdout.write(f"    {message}")

        summary = ", ".join(f"{k}: {v}" for k, v in report.summary.items() if v)
        prefix = "DRY RUN, nothing saved. " if dry_run else ""
        self.stdout.write(
            self.style.SUCCESS(f"{prefix}{len(report.rows)} rows — {summary or 'empty file'}.")
        )
        if report.batch:
            self.stdout.write(f"Report saved as import #{report.batch.pk} (see the admin).")
