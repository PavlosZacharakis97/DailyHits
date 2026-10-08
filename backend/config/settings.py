"""Django settings for DailyHit.

All configuration comes from environment variables (see ../.env.example).
There is a single settings module: dev and prod differ only by env values.
"""

from pathlib import Path

import environ
from django.core.exceptions import ImproperlyConfigured
from django.utils.translation import gettext_lazy as _

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()

# --- Core -------------------------------------------------------------------

SECRET_KEY = env.str("DJANGO_SECRET_KEY")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS: list[str] = env.list("DJANGO_ALLOWED_HOSTS", default=[])
CSRF_TRUSTED_ORIGINS: list[str] = env.list("DJANGO_CSRF_TRUSTED_ORIGINS", default=[])

# Admin is served from a configurable path so that prod does not expose /admin/.
ADMIN_URL = env.str("DJANGO_ADMIN_URL", default="admin/")
if not ADMIN_URL.endswith("/") or ADMIN_URL.startswith("/"):
    raise ImproperlyConfigured("DJANGO_ADMIN_URL must be relative and end with '/', e.g. 'admin/'.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
    "rest_framework",
    "drf_spectacular",
    "apps.catalog",
    "apps.game",
    "apps.importer",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "config.middleware.EnglishApiMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# --- Database ---------------------------------------------------------------

DATABASES = {"default": env.db_url("DATABASE_URL")}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Auth -------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# --- I18n -------------------------------------------------------------------
# The game and its data are English-only; the admin UI is available in EN and RU.

LANGUAGE_CODE = "en"
LANGUAGES = [
    ("en", _("English")),
    ("ru", _("Russian")),
]
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True

TIME_ZONE = "UTC"
USE_TZ = True

# --- Static files -----------------------------------------------------------

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# --- Security ---------------------------------------------------------------
# Prod runs behind a TLS-terminating reverse proxy.

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("DJANGO_SECURE_SSL_REDIRECT", default=not DEBUG)
SESSION_COOKIE_SECURE = env.bool("DJANGO_SECURE_COOKIES", default=not DEBUG)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SECURE_HSTS_SECONDS = env.int("DJANGO_HSTS_SECONDS", default=0)
SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_HSTS_SECONDS > 0
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
X_FRAME_OPTIONS = "DENY"
# Health checks come from inside the container over plain HTTP.
SECURE_REDIRECT_EXEMPT = [r"^healthz$"]

# --- Game -----------------------------------------------------------------

GAME = {
    "MAX_ATTEMPTS": env.int("GAME_MAX_ATTEMPTS", default=10),
    # Year tile is yellow when the difference is at most this many years.
    "YEAR_YELLOW_RANGE": env.int("GAME_YEAR_YELLOW_RANGE", default=5),
    # Fact hints unlock after these attempt numbers.
    "HINT_ATTEMPTS": env.list("GAME_HINT_ATTEMPTS", cast=int, default=[5, 8]),
    # A song may appear in an edition's schedule at most once in this many days.
    "SONG_REPEAT_DAYS": env.int("GAME_SONG_REPEAT_DAYS", default=365),
    # How far back the archive goes.
    "ARCHIVE_DAYS": env.int("GAME_ARCHIVE_DAYS", default=50),
    # Admin warns about schedule gaps in this many upcoming days.
    "SCHEDULE_LOOKAHEAD_DAYS": env.int("GAME_SCHEDULE_LOOKAHEAD_DAYS", default=14),
}

# --- REST framework ---------------------------------------------------------

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PARSER_CLASSES": ["rest_framework.parsers.JSONParser"],
    # Players are anonymous (cookie token); no DRF auth, so no session CSRF either —
    # state-changing game requests check the Origin header instead.
    "DEFAULT_AUTHENTICATION_CLASSES": [],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "UNAUTHENTICATED_USER": None,
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    "DEFAULT_THROTTLE_RATES": {
        "search": env.str("API_THROTTLE_SEARCH", default="60/min"),
        "guess": env.str("API_THROTTLE_GUESS", default="20/min"),
    },
    # Number of reverse proxies in front of Django (for the client IP used by throttling).
    "NUM_PROXIES": env.int("API_NUM_PROXIES", default=0),
    "EXCEPTION_HANDLER": "config.exceptions.api_exception_handler",
}

# --- Game cookies -----------------------------------------------------------

CONSENT_COOKIE_NAME = "dh_consent"
# Must match CONSENT_VERSION in frontend/src/consent/consent.js.
CONSENT_COOKIE_VERSION = env.str("CONSENT_COOKIE_VERSION", default="1")
PLAYER_COOKIE_NAME = "dh_player"
PLAYER_COOKIE_AGE = 60 * 60 * 24 * 365
PLAYER_COOKIE_SECURE = SESSION_COOKIE_SECURE

SPECTACULAR_SETTINGS = {
    "TITLE": "DailyHit API",
    "DESCRIPTION": (
        "Daily song guessing game. Game endpoints need the `dh_consent=1` cookie; "
        "the server then sets the anonymous `dh_player` cookie. POST requests must "
        "send an `Origin` header of the game website."
    ),
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

# --- Logging ----------------------------------------------------------------

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {"format": "%(asctime)s %(levelname)s %(name)s: %(message)s"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "default"},
    },
    "root": {"handlers": ["console"], "level": env.str("DJANGO_LOG_LEVEL", default="INFO")},
    # Replace Django's own console handler so records are not printed twice.
    "loggers": {"django": {"handlers": ["console"], "propagate": False}},
}
