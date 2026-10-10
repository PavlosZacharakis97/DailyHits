import pytest
from django.core.management import call_command

from apps.catalog.models import Country, Edition, Genre, Language, Region, Style, Theme

pytestmark = pytest.mark.django_db


def counts() -> dict[str, int]:
    return {
        m.__name__: m.objects.count()
        for m in (Region, Country, Language, Genre, Style, Theme, Edition)
    }


def test_seed_loads_reference_data() -> None:
    call_command("seed_reference")

    assert counts() == {
        "Region": 7,
        "Country": 81,
        "Language": 38,
        "Genre": 13,
        "Style": 66,
        "Theme": 21,
        "Edition": 1,
    }
    assert Country.objects.get(iso_code="NO").name == "Norway"
    assert Country.objects.get(iso_code="JM").region.code == "latin-america"
    assert Language.objects.get(iso_code="zxx").name == "No lyrics"


def test_related_genres_are_symmetric() -> None:
    call_command("seed_reference")

    assert Genre.objects.get(name="Metal").related.filter(name="Rock").exists()
    assert Genre.objects.get(name="Rock").related.filter(name="Metal").exists()


def test_seed_is_idempotent_and_repairs_changes() -> None:
    call_command("seed_reference")
    Style.objects.filter(name="Grunge").update(genre=Genre.objects.get(name="Pop"))
    before = counts()

    call_command("seed_reference")

    assert counts() == before
    assert Style.objects.get(name="Grunge").genre.name == "Rock"
