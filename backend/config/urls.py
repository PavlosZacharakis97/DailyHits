from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.utils.translation import gettext_lazy as _
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from config.views import api_not_found, healthz

admin.site.site_header = _("DailyHit administration")
admin.site.site_title = _("DailyHit admin")
admin.site.index_title = _("Content")

urlpatterns = [
    path("healthz", healthz, name="healthz"),
    path("i18n/", include("django.conf.urls.i18n")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="api-schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="api-schema"), name="api-docs"),
    path("api/v1/", include("apps.game.urls")),
    re_path(r"^api/", api_not_found),
    path(settings.ADMIN_URL, admin.site.urls),
]
