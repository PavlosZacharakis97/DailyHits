from django.contrib import admin
from django.http import HttpRequest
from django.utils.html import format_html_join
from django.utils.translation import gettext_lazy as _

from apps.importer.models import ImportBatch, ImportRow


class ImportRowInline(admin.TabularInline):
    model = ImportRow
    extra = 0
    can_delete = False
    fields = ["row_number", "status", "song", "report"]
    readonly_fields = fields

    def has_add_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    @admin.display(description=_("messages"))
    def report(self, obj: ImportRow) -> str:
        return format_html_join("", "<div>{}</div>", ((m,) for m in obj.messages)) or "—"


@admin.register(ImportBatch)
class ImportBatchAdmin(admin.ModelAdmin):
    """Read-only history of CSV imports (run with `manage.py import_songs`)."""

    list_display = ["created_at", "file_name", "counts"]
    readonly_fields = ["file_name", "dry_run", "created_at", "summary"]
    inlines = [ImportRowInline]

    def has_add_permission(self, request: HttpRequest) -> bool:
        return False

    def has_change_permission(self, request: HttpRequest, obj=None) -> bool:
        return False

    @admin.display(description=_("result"))
    def counts(self, obj: ImportBatch) -> str:
        return ", ".join(f"{k}: {v}" for k, v in obj.summary.items() if v)
