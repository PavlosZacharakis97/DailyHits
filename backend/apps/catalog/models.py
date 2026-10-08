"""Catalog: reference data, artists, songs and facts.

Everything a song tile compares (genre, style, theme, country, language) is a
reference table, never free text.
"""

from zoneinfo import available_timezones

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, RegexValidator, URLValidator
from django.db import models, transaction
from django.db.models import Q
from django.db.models.functions import ExtractYear, Lower, Now
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

MIN_SONG_YEAR = 1900

youtube_id_validator = RegexValidator(
    r"^[A-Za-z0-9_-]{11}$",
    _("A YouTube video ID is exactly 11 characters: letters, digits, - or _."),
)


def validate_timezone(value: str) -> None:
    if value not in available_timezones():
        raise ValidationError(_("Unknown time zone: %(value)s"), params={"value": value})


def validate_url_list(value: object) -> None:
    if not isinstance(value, list):
        raise ValidationError(_("Sources must be a list of URLs."))
    url = URLValidator()
    for item in value:
        if not isinstance(item, str):
            raise ValidationError(_("Sources must be a list of URLs."))
        url(item)


def not_blank(field: str) -> Q:
    """Q that rejects empty and whitespace-only strings at the database level."""
    return Q(**{f"{field}__regex": r"\S"})


# --- Choices ----------------------------------------------------------------
# Module level so that model Meta constraints can reference them.


class ArtistType(models.TextChoices):
    SOLO = "solo", _("Solo")
    GROUP = "group", _("Group")
    DUO = "duo", _("Duo")
    COLLABORATION = "collaboration", _("Collaboration")


class Vocal(models.TextChoices):
    MALE = "male", _("Male")
    FEMALE = "female", _("Female")
    MIXED = "mixed", _("Mixed")
    INSTRUMENTAL = "instrumental", _("Instrumental")


class Difficulty(models.TextChoices):
    EASY = "easy", _("Easy")
    MEDIUM = "medium", _("Medium")
    HARD = "hard", _("Hard")


class SongStatus(models.TextChoices):
    DRAFT = "draft", _("Draft")
    REVIEW = "review", _("Review")
    VERIFIED = "verified", _("Verified")


class ArtistRole(models.TextChoices):
    PRIMARY = "primary", _("Primary")
    FEATURED = "featured", _("Featured")


class FactStrength(models.TextChoices):
    # How much the fact gives the answer away. Hint #1 uses the subtlest fact.
    EASY = "easy", _("Easy — subtle")
    MEDIUM = "medium", _("Medium")
    STRONG = "strong", _("Strong — revealing")


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)

    class Meta:
        abstract = True


# --- Reference data ---------------------------------------------------------


class Region(models.Model):
    code = models.SlugField(_("code"), max_length=32, unique=True)
    name = models.CharField(_("name"), max_length=64, unique=True)

    class Meta:
        verbose_name = _("region")
        verbose_name_plural = _("regions")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Country(models.Model):
    name = models.CharField(_("name"), max_length=64, unique=True)
    iso_code = models.CharField(
        _("ISO code"),
        max_length=2,
        unique=True,
        validators=[RegexValidator(r"^[A-Z]{2}$", _("Two uppercase letters, ISO 3166-1 alpha-2."))],
    )
    region = models.ForeignKey(
        Region, models.PROTECT, related_name="countries", verbose_name=_("region")
    )

    class Meta:
        verbose_name = _("country")
        verbose_name_plural = _("countries")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(iso_code__regex=r"^[A-Z]{2}$"), name="country_iso_code_format"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Language(models.Model):
    name = models.CharField(_("name"), max_length=64, unique=True)
    iso_code = models.CharField(
        _("ISO code"),
        max_length=3,
        unique=True,
        help_text=_(
            "ISO 639-1 (en), or ISO 639-3 when there is no two-letter code (zxx = no lyrics)."
        ),
        validators=[RegexValidator(r"^[a-z]{2,3}$", _("Two or three lowercase letters."))],
    )

    class Meta:
        verbose_name = _("language")
        verbose_name_plural = _("languages")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(
                condition=Q(iso_code__regex=r"^[a-z]{2,3}$"), name="language_iso_code_format"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class Genre(models.Model):
    name = models.CharField(_("name"), max_length=64, unique=True)
    related = models.ManyToManyField(
        "self",
        symmetrical=True,
        blank=True,
        verbose_name=_("related genres"),
        help_text=_("A guess in a related genre gets a yellow tile."),
    )

    class Meta:
        verbose_name = _("genre")
        verbose_name_plural = _("genres")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class Style(models.Model):
    name = models.CharField(_("name"), max_length=64, unique=True)
    genre = models.ForeignKey(Genre, models.PROTECT, related_name="styles", verbose_name=_("genre"))

    class Meta:
        verbose_name = _("style")
        verbose_name_plural = _("styles")
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ThemeGroup(models.Model):
    name = models.CharField(_("name"), max_length=64, unique=True)
    order = models.PositiveSmallIntegerField(_("order"), default=0)

    class Meta:
        verbose_name = _("theme group")
        verbose_name_plural = _("theme groups")
        ordering = ["order", "name"]

    def __str__(self) -> str:
        return self.name


class Theme(models.Model):
    name = models.CharField(_("name"), max_length=64, unique=True)
    group = models.ForeignKey(
        ThemeGroup, models.PROTECT, related_name="themes", verbose_name=_("group")
    )
    order = models.PositiveSmallIntegerField(_("order"), default=0)

    class Meta:
        verbose_name = _("theme")
        verbose_name_plural = _("themes")
        ordering = ["group__order", "order", "name"]

    def __str__(self) -> str:
        return self.name


class Edition(models.Model):
    code = models.SlugField(_("code"), max_length=32, unique=True)
    name = models.CharField(_("name"), max_length=64)
    timezone = models.CharField(
        _("time zone"),
        max_length=64,
        default="UTC",
        validators=[validate_timezone],
        help_text=_("The daily puzzle changes at midnight in this time zone."),
    )
    is_active = models.BooleanField(_("active"), default=True)

    class Meta:
        verbose_name = _("edition")
        verbose_name_plural = _("editions")
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name


# --- Artists ----------------------------------------------------------------


class Person(models.Model):
    name = models.CharField(_("name"), max_length=200, db_index=True)
    musicbrainz_id = models.UUIDField(_("MusicBrainz ID"), unique=True, null=True, blank=True)

    class Meta:
        verbose_name = _("person")
        verbose_name_plural = _("people")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=not_blank("name"), name="person_name_not_blank")
        ]

    def __str__(self) -> str:
        return self.name


class Artist(models.Model):
    Type = ArtistType

    name = models.CharField(_("name"), max_length=200, db_index=True)
    type = models.CharField(_("type"), max_length=16, choices=Type.choices)
    country = models.ForeignKey(
        Country, models.PROTECT, related_name="artists", verbose_name=_("country")
    )
    musicbrainz_id = models.UUIDField(_("MusicBrainz ID"), unique=True, null=True, blank=True)
    members = models.ManyToManyField(
        Person, through="ArtistMember", related_name="artists", verbose_name=_("members")
    )

    class Meta:
        verbose_name = _("artist")
        verbose_name_plural = _("artists")
        ordering = ["name"]
        constraints = [
            models.CheckConstraint(condition=not_blank("name"), name="artist_name_not_blank"),
            models.CheckConstraint(
                condition=Q(type__in=ArtistType.values), name="artist_type_valid"
            ),
        ]

    def __str__(self) -> str:
        return self.name


class ArtistMember(models.Model):
    artist = models.ForeignKey(
        Artist, models.CASCADE, related_name="memberships", verbose_name=_("artist")
    )
    person = models.ForeignKey(
        Person, models.CASCADE, related_name="memberships", verbose_name=_("person")
    )

    class Meta:
        verbose_name = _("artist member")
        verbose_name_plural = _("artist members")
        constraints = [
            models.UniqueConstraint(fields=["artist", "person"], name="artist_member_unique"),
        ]

    def __str__(self) -> str:
        return f"{self.person} — {self.artist}"


# --- Songs ------------------------------------------------------------------


class Song(TimestampedModel):
    Vocal = Vocal
    Difficulty = Difficulty
    Status = SongStatus

    title = models.CharField(
        _("title"),
        max_length=200,
        help_text=_("Official title, without “(Remastered)”, “– Radio Edit” and the like."),
    )
    primary_artist = models.ForeignKey(
        Artist,
        models.PROTECT,
        related_name="primary_songs",
        verbose_name=_("primary artist"),
        help_text=_("The artist credited on the original release. Featured artists go below."),
    )
    year = models.PositiveSmallIntegerField(
        _("year"),
        null=True,
        blank=True,
        validators=[MinValueValidator(MIN_SONG_YEAR)],
        help_text=_("Year of the first official release (not a remaster or compilation)."),
    )
    genre = models.ForeignKey(
        Genre, models.PROTECT, null=True, blank=True, related_name="songs", verbose_name=_("genre")
    )
    styles = models.ManyToManyField(
        Style,
        blank=True,
        related_name="songs",
        verbose_name=_("styles"),
        help_text=_("1–2 styles."),
    )
    themes = models.ManyToManyField(
        Theme, through="SongTheme", related_name="songs", verbose_name=_("themes")
    )
    vocal = models.CharField(_("vocal"), max_length=16, choices=Vocal.choices, blank=True)
    language = models.ForeignKey(
        Language,
        models.PROTECT,
        null=True,
        blank=True,
        related_name="songs",
        verbose_name=_("language"),
    )
    # NULL, not "", so that "no video" is unambiguous (the spec asks for a nullable field).
    youtube_video_id = models.CharField(  # noqa: DJ001
        _("YouTube video ID"),
        max_length=11,
        null=True,
        blank=True,
        validators=[youtube_id_validator],
        help_text=_("Without it the game links to a YouTube search for “artist title”."),
    )
    musicbrainz_id = models.UUIDField(_("MusicBrainz ID"), unique=True, null=True, blank=True)
    difficulty = models.CharField(
        _("difficulty"), max_length=8, choices=Difficulty.choices, default=Difficulty.MEDIUM
    )
    status = models.CharField(
        _("status"), max_length=8, choices=SongStatus.choices, default=SongStatus.DRAFT
    )
    editions = models.ManyToManyField(
        Edition, blank=True, related_name="songs", verbose_name=_("editions")
    )
    sources = models.JSONField(
        _("sources"),
        default=list,
        blank=True,
        validators=[validate_url_list],
        help_text=_("List of source URLs."),
    )
    notes = models.TextField(_("moderator notes"), blank=True)
    artists = models.ManyToManyField(
        Artist, through="SongArtist", related_name="songs", verbose_name=_("artists")
    )

    class Meta:
        verbose_name = _("song")
        verbose_name_plural = _("songs")
        ordering = ["title"]
        constraints = [
            models.UniqueConstraint(
                Lower("title"),
                "primary_artist",
                name="song_unique_title_primary_artist",
                violation_error_message=_("This artist already has a song with this title."),
            ),
            models.CheckConstraint(condition=not_blank("title"), name="song_title_not_blank"),
            models.CheckConstraint(
                condition=Q(year__isnull=True)
                | Q(year__gte=MIN_SONG_YEAR, year__lte=ExtractYear(Now())),
                name="song_year_range",
                violation_error_message=_("The year must be between 1900 and the current year."),
            ),
            models.CheckConstraint(
                condition=Q(youtube_video_id__isnull=True)
                | Q(youtube_video_id__regex=r"^[A-Za-z0-9_-]{11}$"),
                name="song_youtube_video_id_format",
            ),
            models.CheckConstraint(
                condition=Q(vocal__in=["", *Vocal.values]), name="song_vocal_valid"
            ),
            models.CheckConstraint(
                condition=Q(difficulty__in=Difficulty.values), name="song_difficulty_valid"
            ),
            models.CheckConstraint(
                condition=Q(status__in=SongStatus.values), name="song_status_valid"
            ),
            # A verified song can never lack the fields every tile needs.
            models.CheckConstraint(
                condition=~Q(status=SongStatus.VERIFIED)
                | Q(
                    year__isnull=False,
                    genre__isnull=False,
                    language__isnull=False,
                    vocal__in=Vocal.values,
                ),
                name="song_verified_has_tile_fields",
                violation_error_message=_(
                    "A verified song needs a year, genre, vocal and language."
                ),
            ),
        ]
        indexes = [models.Index(fields=["status", "year"], name="song_status_year_idx")]

    def __str__(self) -> str:
        return self.title

    def save(self, *args, **kwargs) -> None:
        with transaction.atomic():
            super().save(*args, **kwargs)
            self._sync_primary_artist()

    def clean(self) -> None:
        super().clean()
        if self.title:
            self.title = self.title.strip()
        if self.youtube_video_id == "":
            self.youtube_video_id = None
        current_year = timezone.now().year
        if self.year is not None and self.year > current_year:
            raise ValidationError(
                {"year": _("The year cannot be later than %(year)s.") % {"year": current_year}}
            )

    def _sync_primary_artist(self) -> None:
        """Keep the single primary SongArtist row equal to ``primary_artist``."""
        SongArtist.objects.filter(song=self, role=ArtistRole.PRIMARY).exclude(
            artist_id=self.primary_artist_id
        ).delete()
        SongArtist.objects.update_or_create(
            song=self, artist_id=self.primary_artist_id, defaults={"role": ArtistRole.PRIMARY}
        )


class SongArtist(models.Model):
    Role = ArtistRole

    song = models.ForeignKey(
        Song, models.CASCADE, related_name="song_artists", verbose_name=_("song")
    )
    artist = models.ForeignKey(
        Artist, models.PROTECT, related_name="song_credits", verbose_name=_("artist")
    )
    role = models.CharField(
        _("role"), max_length=8, choices=ArtistRole.choices, default=ArtistRole.FEATURED
    )

    class Meta:
        verbose_name = _("song artist")
        verbose_name_plural = _("song artists")
        constraints = [
            models.UniqueConstraint(fields=["song", "artist"], name="song_artist_unique"),
            models.UniqueConstraint(
                fields=["song"],
                condition=Q(role=ArtistRole.PRIMARY),
                name="song_artist_single_primary",
            ),
            models.CheckConstraint(
                condition=Q(role__in=ArtistRole.values), name="song_artist_role_valid"
            ),
        ]

    def __str__(self) -> str:
        return f"{self.artist} ({self.get_role_display()})"

    def clean(self) -> None:
        super().clean()
        # The song may still be unsaved (admin “add” page), so use the related
        # instance rather than song_id.
        try:
            song = self.song
        except Song.DoesNotExist:
            return
        if (
            self.role == ArtistRole.FEATURED
            and self.artist_id is not None
            and self.artist_id == song.primary_artist_id
        ):
            raise ValidationError(
                {"artist": _("This artist is already the primary artist of the song.")}
            )


class SongTheme(models.Model):
    song = models.ForeignKey(
        Song, models.CASCADE, related_name="song_themes", verbose_name=_("song")
    )
    theme = models.ForeignKey(
        Theme, models.PROTECT, related_name="song_themes", verbose_name=_("theme")
    )
    is_primary = models.BooleanField(_("primary"), default=False)

    class Meta:
        verbose_name = _("song theme")
        verbose_name_plural = _("song themes")
        ordering = ["-is_primary", "theme__name"]
        constraints = [
            models.UniqueConstraint(fields=["song", "theme"], name="song_theme_unique"),
            models.UniqueConstraint(
                fields=["song"],
                condition=Q(is_primary=True),
                name="song_theme_single_primary",
                violation_error_message=_("A song can have only one primary theme."),
            ),
        ]

    def __str__(self) -> str:
        return str(self.theme)


class SongAlias(models.Model):
    song = models.ForeignKey(Song, models.CASCADE, related_name="aliases", verbose_name=_("song"))
    alias = models.CharField(
        _("alias"),
        max_length=200,
        help_text=_("Alternative spelling players may type, e.g. “Despasito”."),
    )

    class Meta:
        verbose_name = _("alias")
        verbose_name_plural = _("aliases")
        ordering = ["alias"]
        constraints = [
            models.UniqueConstraint(
                "song",
                Lower("alias"),
                name="song_alias_unique",
                violation_error_message=_("This song already has this alias."),
            ),
            models.CheckConstraint(condition=not_blank("alias"), name="song_alias_not_blank"),
        ]

    def __str__(self) -> str:
        return self.alias


class Fact(models.Model):
    Strength = FactStrength

    song = models.ForeignKey(Song, models.CASCADE, related_name="facts", verbose_name=_("song"))
    text = models.TextField(
        _("text"),
        help_text=_(
            "In your own words. No lyric quotes. Must not mention the title or the artist."
        ),
    )
    strength = models.CharField(_("strength"), max_length=8, choices=FactStrength.choices)
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    source_url = models.URLField(_("source URL"), max_length=500)
    is_verified = models.BooleanField(_("verified"), default=False)

    class Meta:
        verbose_name = _("fact")
        verbose_name_plural = _("facts")
        ordering = ["order", "pk"]
        constraints = [
            models.CheckConstraint(condition=not_blank("text"), name="fact_text_not_blank"),
            models.CheckConstraint(
                condition=not_blank("source_url"), name="fact_source_url_not_blank"
            ),
            models.CheckConstraint(
                condition=Q(strength__in=FactStrength.values), name="fact_strength_valid"
            ),
        ]

    def __str__(self) -> str:
        return self.text[:60]
