from django.contrib import admin, messages
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from apps.catalog.models import Edition, SongStatus
from apps.game.conf import game_config
from apps.game.dates import edition_today
from apps.game.models import DailyPuzzle, GameSession, Guess
from apps.game.schedule import missing_dates, puzzle_warnings


@admin.register(DailyPuzzle)
class DailyPuzzleAdmin(admin.ModelAdmin):
    list_display = ["date", "number", "edition", "song", "artist", "genre", "difficulty"]
    list_filter = ["edition"]
    date_hierarchy = "date"
    search_fields = ["song__title", "song__primary_artist__name"]
    list_select_related = ["edition", "song__primary_artist", "song__genre"]
    autocomplete_fields = ["song"]
    ordering = ["-date"]

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "song":
            kwargs["queryset"] = db_field.related_model.objects.filter(status=SongStatus.VERIFIED)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    @admin.display(description=gettext_lazy("artist"), ordering="song__primary_artist__name")
    def artist(self, obj: DailyPuzzle) -> str:
        return str(obj.song.primary_artist)

    @admin.display(description=gettext_lazy("genre"))
    def genre(self, obj: DailyPuzzle) -> str:
        return str(obj.song.genre or "—")

    @admin.display(description=gettext_lazy("difficulty"))
    def difficulty(self, obj: DailyPuzzle) -> str:
        return obj.song.get_difficulty_display()

    def changelist_view(self, request: HttpRequest, extra_context=None) -> TemplateResponse:
        days = game_config().schedule_lookahead_days
        for edition in Edition.objects.filter(is_active=True):
            gaps = missing_dates(edition, edition_today(edition), days)
            if gaps:
                self.message_user(
                    request,
                    _("%(edition)s: no puzzle in the next %(days)s days on %(dates)s.")
                    % {
                        "edition": edition,
                        "days": days,
                        "dates": ", ".join(d.isoformat() for d in gaps),
                    },
                    messages.WARNING,
                )
        return super().changelist_view(request, extra_context)

    def save_model(self, request: HttpRequest, obj: DailyPuzzle, form, change: bool) -> None:
        super().save_model(request, obj, form, change)
        for warning in puzzle_warnings(obj):
            self.message_user(request, warning, messages.WARNING)


class GuessInline(admin.TabularInline):
    model = Guess
    extra = 0
    can_delete = False
    fields = ["attempt_number", "song", "created_at"]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False


@admin.register(GameSession)
class GameSessionAdmin(admin.ModelAdmin):
    """Read-only: sessions are written by the game API only."""

    list_display = ["id", "puzzle", "status", "created_at", "finished_at"]
    list_filter = ["status", "puzzle__edition"]
    search_fields = ["id", "player_token"]
    list_select_related = ["puzzle__edition"]
    readonly_fields = ["id", "player_token", "puzzle", "status", "created_at", "finished_at"]
    inlines = [GuessInline]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False
