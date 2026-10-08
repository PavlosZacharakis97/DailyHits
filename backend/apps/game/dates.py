"""The single source of truth for “which day is it” in an edition."""

from datetime import date, datetime
from zoneinfo import ZoneInfo

from django.utils import timezone

from apps.catalog.models import Edition


def edition_today(edition: Edition, now: datetime | None = None) -> date:
    """Current calendar date in the edition's time zone."""
    moment = now if now is not None else timezone.now()
    return moment.astimezone(ZoneInfo(edition.timezone)).date()
