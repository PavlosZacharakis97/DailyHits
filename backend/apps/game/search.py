"""Song autocomplete: case-, accent- and typo-tolerant (unaccent + pg_trgm)."""

import unicodedata

from django.contrib.postgres.search import TrigramWordSimilarity
from django.db.models import Case, Exists, F, Func, IntegerField, OuterRef, Q, QuerySet, Value, When
from django.db.models.functions import Greatest

from apps.catalog.models import Edition, Song, SongAlias, SongArtist, SongStatus

MAX_RESULTS = 10
# Word similarity above this counts as a fuzzy match (e.g. “bohemain” → “Bohemian”).
FUZZY_THRESHOLD = 0.45


def _plain(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower()


def _unaccent(field: str) -> Func:
    return Func(F(field), function="unaccent")


def search_songs(edition: Edition, query: str, limit: int = MAX_RESULTS) -> QuerySet[Song]:
    term = _plain(query.strip())
    alias = SongAlias.objects.filter(song=OuterRef("pk"), alias__unaccent__icontains=term)
    featured = SongArtist.objects.filter(
        song=OuterRef("pk"), artist__name__unaccent__icontains=term
    )
    return (
        Song.objects.filter(status=SongStatus.VERIFIED, editions=edition)
        .annotate(
            similarity=Greatest(
                TrigramWordSimilarity(Value(term), _unaccent("title")),
                TrigramWordSimilarity(Value(term), _unaccent("primary_artist__name")),
            ),
            starts=Case(
                When(title__unaccent__istartswith=term, then=Value(0)),
                default=Value(1),
                output_field=IntegerField(),
            ),
        )
        .filter(
            Q(title__unaccent__icontains=term)
            | Q(primary_artist__name__unaccent__icontains=term)
            | Exists(alias)
            | Exists(featured)
            | Q(similarity__gte=FUZZY_THRESHOLD)
        )
        .select_related("primary_artist")
        .order_by("starts", "-similarity", "title")[:limit]
    )
