"""Staging for CSV imports: every run and every row is kept with its report."""

from django.db import models
from django.db.models import Q
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Song


class RowStatus(models.TextChoices):
    CREATED = "created", _("Created")
    UPDATED = "updated", _("Updated")
    UNCHANGED = "unchanged", _("Unchanged")
    CONFLICT = "conflict", _("Conflict")
    ERROR = "error", _("Error")


class ImportBatch(models.Model):
    file_name = models.CharField(_("file name"), max_length=255)
    dry_run = models.BooleanField(_("dry run"), default=False)
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    summary = models.JSONField(_("summary"), default=dict, blank=True)

    class Meta:
        verbose_name = _("import")
        verbose_name_plural = _("imports")
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.file_name} ({self.created_at:%Y-%m-%d %H:%M})"


class ImportRow(models.Model):
    Status = RowStatus

    batch = models.ForeignKey(
        ImportBatch, models.CASCADE, related_name="rows", verbose_name=_("import")
    )
    row_number = models.PositiveIntegerField(_("row"))
    raw = models.JSONField(_("raw data"))
    status = models.CharField(_("status"), max_length=10, choices=RowStatus.choices)
    song = models.ForeignKey(
        Song,
        models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_rows",
        verbose_name=_("song"),
    )
    messages = models.JSONField(_("messages"), default=list, blank=True)

    class Meta:
        verbose_name = _("import row")
        verbose_name_plural = _("import rows")
        ordering = ["batch", "row_number"]
        constraints = [
            models.UniqueConstraint(fields=["batch", "row_number"], name="import_row_unique"),
            models.CheckConstraint(
                condition=Q(status__in=RowStatus.values), name="import_row_status_valid"
            ),
        ]

    def __str__(self) -> str:
        return f"#{self.row_number} {self.get_status_display()}"
