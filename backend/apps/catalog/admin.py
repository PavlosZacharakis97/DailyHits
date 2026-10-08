from django.contrib import admin, messages
from django.db import models
from django.db.models import QuerySet
from django.http import HttpRequest
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.utils.translation import ngettext

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
    Region,
    Song,
    SongAlias,
    SongArtist,
    SongStatus,
    SongTheme,
    Style,
    Theme,
    ThemeGroup,
)
from apps.catalog.validation import SONG_ISSUE_PREFETCH, Level, song_issues, verification_errors

# --- Reference data ---------------------------------------------------------


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "code"]
    search_fields = ["name", "code"]


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ["name", "iso_code", "region"]
    list_filter = ["region"]
    search_fields = ["name", "iso_code"]
    list_select_related = ["region"]


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ["name", "iso_code"]
    search_fields = ["name", "iso_code"]


class StyleInline(admin.TabularInline):
    model = Style
    extra = 0


@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ["name", "related_list"]
    search_fields = ["name"]
    filter_horizontal = ["related"]
    inlines = [StyleInline]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Genre]:
        return super().get_queryset(request).prefetch_related("related")

    @admin.display(description=_("related genres"))
    def related_list(self, obj: Genre) -> str:
        return ", ".join(g.name for g in obj.related.all())


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    list_display = ["name", "genre"]
    list_filter = ["genre"]
    search_fields = ["name", "genre__name"]
    list_select_related = ["genre"]


class ThemeInline(admin.TabularInline):
    model = Theme
    extra = 0


@admin.register(ThemeGroup)
class ThemeGroupAdmin(admin.ModelAdmin):
    list_display = ["name", "order"]
    inlines = [ThemeInline]


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "order"]
    list_filter = ["group"]
    search_fields = ["name"]
    list_select_related = ["group"]


@admin.register(Edition)
class EditionAdmin(admin.ModelAdmin):
    list_display = ["code", "name", "timezone", "is_active"]
    list_filter = ["is_active"]


# --- Artists ----------------------------------------------------------------


class ArtistMemberInline(admin.TabularInline):
    model = ArtistMember
    extra = 0
    autocomplete_fields = ["person"]


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ["name", "musicbrainz_id"]
    search_fields = ["name", "musicbrainz_id"]


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ["name", "type", "country"]
    list_filter = ["type", "country__region", "country"]
    search_fields = ["name", "musicbrainz_id", "memberships__person__name"]
    list_select_related = ["country"]
    autocomplete_fields = ["country"]
    inlines = [ArtistMemberInline]


# --- Songs ------------------------------------------------------------------


class DecadeFilter(admin.SimpleListFilter):
    title = _("decade")
    parameter_name = "decade"

    def lookups(self, request: HttpRequest, model_admin: admin.ModelAdmin) -> list[tuple[str, str]]:
        years = Song.objects.exclude(year__isnull=True).values_list("year", flat=True)
        decades = sorted({y // 10 * 10 for y in years})
        return [(str(d), f"{d}s") for d in decades]

    def queryset(self, request: HttpRequest, queryset: QuerySet[Song]) -> QuerySet[Song]:
        if self.value() is None:
            return queryset
        start = int(self.value())
        return queryset.filter(year__gte=start, year__lte=start + 9)


class FeaturedArtistInline(admin.TabularInline):
    """Featured artists only; the primary artist is a field on the song itself."""

    model = SongArtist
    extra = 0
    fields = ["artist"]
    autocomplete_fields = ["artist"]
    verbose_name = _("featured artist")
    verbose_name_plural = _("featured artists")

    def get_queryset(self, request: HttpRequest) -> QuerySet[SongArtist]:
        return super().get_queryset(request).filter(role=ArtistRole.FEATURED)


class SongThemeInline(admin.TabularInline):
    model = SongTheme
    extra = 0
    max_num = 2
    autocomplete_fields = ["theme"]


class SongAliasInline(admin.TabularInline):
    model = SongAlias
    extra = 0


class FactInline(admin.StackedInline):
    model = Fact
    extra = 0
    fields = [("strength", "order", "is_verified"), "text", "source_url"]
    formfield_overrides = {models.URLField: {"assume_scheme": "https"}}


@admin.register(Song)
class SongAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "primary_artist",
        "year",
        "genre",
        "difficulty",
        "status",
        "problems",
    ]
    list_filter = [
        "status",
        "genre",
        DecadeFilter,
        "language",
        "editions",
        "difficulty",
    ]
    search_fields = ["title", "aliases__alias", "primary_artist__name", "artists__name"]
    autocomplete_fields = ["primary_artist", "genre", "language"]
    filter_horizontal = ["styles", "editions"]
    readonly_fields = ["created_at", "updated_at"]
    inlines = [FeaturedArtistInline, SongThemeInline, SongAliasInline, FactInline]
    actions = ["mark_review", "mark_verified"]
    list_per_page = 50
    fieldsets = [
        (None, {"fields": ["title", "primary_artist", "status", "difficulty", "editions"]}),
        (_("Tiles"), {"fields": ["year", "genre", "styles", "vocal", "language"]}),
        (_("Links"), {"fields": ["youtube_video_id", "musicbrainz_id", "sources"]}),
        (_("Moderation"), {"fields": ["notes", ("created_at", "updated_at")]}),
    ]

    def get_queryset(self, request: HttpRequest) -> QuerySet[Song]:
        return (
            super()
            .get_queryset(request)
            .select_related("primary_artist", "genre")
            .prefetch_related(*SONG_ISSUE_PREFETCH)
            .distinct()
        )

    @admin.display(description=_("problems"))
    def problems(self, obj: Song) -> str:
        issues = song_issues(obj)
        if not issues:
            return "✓"
        return format_html_join(
            mark_safe("<br>"),
            '<span style="color: {}">{}</span>',
            (("#ba2121" if i.level is Level.ERROR else "#a66a00", i.message) for i in issues),
        )

    def save_related(self, request: HttpRequest, form, formsets, change: bool) -> None:
        super().save_related(request, form, formsets, change)
        song: Song = form.instance
        if song.status != SongStatus.VERIFIED:
            return
        errors = verification_errors(
            Song.objects.prefetch_related(*SONG_ISSUE_PREFETCH).get(pk=song.pk)
        )
        if not errors:
            return
        # Inline data is only saved after the song itself, so completeness can
        # only be checked here; fall back to review instead of saving a broken
        # verified song.
        Song.objects.filter(pk=song.pk).update(status=SongStatus.REVIEW)
        song.status = SongStatus.REVIEW
        self.message_user(
            request,
            format_html(
                "{}<ul>{}</ul>",
                _("The song was saved with status “Review” because it cannot be verified yet:"),
                format_html_join("", "<li>{}</li>", ((e.message,) for e in errors)),
            ),
            messages.ERROR,
        )

    @admin.action(description=_("Move selected songs to review"))
    def mark_review(self, request: HttpRequest, queryset: QuerySet[Song]) -> None:
        updated = queryset.order_by().update(status=SongStatus.REVIEW)
        self.message_user(
            request,
            ngettext("%(n)d song moved to review.", "%(n)d songs moved to review.", updated)
            % {"n": updated},
            messages.SUCCESS,
        )

    @admin.action(description=_("Verify selected songs (only those that pass validation)"))
    def mark_verified(self, request: HttpRequest, queryset: QuerySet[Song]) -> None:
        verified, rejected = [], []
        for song in queryset:
            errors = verification_errors(song)
            if errors:
                rejected.append((song, errors))
            else:
                verified.append(song.pk)
        Song.objects.filter(pk__in=verified).update(status=SongStatus.VERIFIED)
        if verified:
            self.message_user(
                request,
                ngettext("%(n)d song verified.", "%(n)d songs verified.", len(verified))
                % {"n": len(verified)},
                messages.SUCCESS,
            )
        for song, errors in rejected:
            self.message_user(
                request,
                format_html("{} — {}", song, " ".join(str(e.message) for e in errors)),
                messages.ERROR,
            )
