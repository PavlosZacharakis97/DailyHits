from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.utils.translation import gettext_lazy as _

from config.views import healthz

admin.site.site_header = _("DailyHit administration")
admin.site.site_title = _("DailyHit admin")
admin.site.index_title = _("Content")

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("i18n/", include("django.conf.urls.i18n")),
    path(settings.ADMIN_URL, admin.site.urls),
]
