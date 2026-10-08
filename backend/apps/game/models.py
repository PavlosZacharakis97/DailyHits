"""Game: the daily schedule and server-side player progress."""

import uuid

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Max, Q
from django.utils.translation import gettext_lazy as _

from apps.catalog.models import Edition, Song


class DailyPuzzle(models.Model):
    edition = models.ForeignKey(
        Edition, models.PROTECT, related_name="puzzles", verbose_name=_("edition")
    )
    date = models.DateField(_("date"))
    song = models.ForeignKey(Song, models.PROTECT, related_name="puzzles", verbose_name=_("song"))
    number = models.PositiveIntegerField(
        _("number"),
        blank=True,
        help_text=_("Issue number. Leave empty to use the next free number."),
    )

    class Meta:
        verbose_name = _("daily puzzle")
        verbose_name_plural = _("daily puzzles")
        ordering = ["-date"]
        constraints = [
            models.UniqueConstraint(
                fields=["edition", "date"],
                name="puzzle_unique_edition_date",
                violation_error_message=_("This edition already has a puzzle on this date."),
            ),
            models.UniqueConstraint(
                fields=["edition", "number"],
                name="puzzle_unique_edition_number",
                violation_error_message=_("This edition already has a puzzle with this number."),
            ),
            models.CheckConstraint(condition=Q(number__gte=1), name="puzzle_number_positive"),
        ]

    def __str__(self) -> str:
        return f"#{self.number} {self.date} ({self.edition.code})"

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            if self.number is None:
                # Lock the edition row so concurrent creates cannot take the same number.
                Edition.objects.select_for_update().filter(pk=self.edition_id).get()
                last = DailyPuzzle.objects.filter(edition_id=self.edition_id).aggregate(
                    last=Max("number")
                )["last"]
                self.number = (last or 0) + 1
            super().save(*args, **kwargs)

    def clean(self) -> None:
        super().clean()
        if self.edition_id is None or self.song_id is None or self.date is None:
            return
        from apps.game.schedule import puzzle_errors

        errors = puzzle_errors(self)
        if errors:
            raise ValidationError(errors)


class SessionStatus(models.TextChoices):
    IN_PROGRESS = "in_progress", _("In progress")
    WON = "won", _("Won")
    LOST = "lost", _("Lost")
    GAVE_UP = "gave_up", _("Gave up")


class GameSession(models.Model):
    Status = SessionStatus

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    player_token = models.UUIDField(
        _("player token"), help_text=_("Anonymous player ID from an httpOnly cookie.")
    )
    puzzle = models.ForeignKey(
        DailyPuzzle, models.PROTECT, related_name="sessions", verbose_name=_("puzzle")
    )
    status = models.CharField(
        _("status"), max_length=16, choices=SessionStatus.choices, default=SessionStatus.IN_PROGRESS
    )
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    finished_at = models.DateTimeField(_("finished at"), null=True, blank=True)

    class Meta:
        verbose_name = _("game session")
        verbose_name_plural = _("game sessions")
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["player_token", "puzzle"], name="session_unique_player_puzzle"
            ),
            models.CheckConstraint(
                condition=Q(status__in=SessionStatus.values), name="session_status_valid"
            ),
            # finished_at is set exactly when the game is over.
            models.CheckConstraint(
                condition=Q(status=SessionStatus.IN_PROGRESS, finished_at__isnull=True)
                | (~Q(status=SessionStatus.IN_PROGRESS) & Q(finished_at__isnull=False)),
                name="session_finished_at_matches_status",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.puzzle} — {self.get_status_display()}"


class Guess(models.Model):
    session = models.ForeignKey(
        GameSession, models.CASCADE, related_name="guesses", verbose_name=_("session")
    )
    song = models.ForeignKey(Song, models.PROTECT, related_name="guesses", verbose_name=_("song"))
    attempt_number = models.PositiveSmallIntegerField(_("attempt number"))
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)

    class Meta:
        verbose_name = _("guess")
        verbose_name_plural = _("guesses")
        ordering = ["session", "attempt_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "attempt_number"], name="guess_unique_attempt"
            ),
            models.UniqueConstraint(fields=["session", "song"], name="guess_unique_song"),
            models.CheckConstraint(
                condition=Q(attempt_number__gte=1), name="guess_attempt_positive"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.attempt_number}. {self.song}"
