import csv
from io import StringIO
from pathlib import Path

import pytest
from django.core.management import CommandError, call_command

from apps.catalog.models import Artist, ArtistRole, Song, SongStatus
from apps.importer.models import ImportBatch, RowStatus
from apps.importer.services import SongImporter, read_rows

pytestmark = pytest.mark.django_db

HEADER = [
    "title", "artist", "artist_type", "artist_country", "artist_members", "featured",
    "year", "genre", "styles", "vocal", "language", "themes", "difficulty", "youtube_id",
    "musicbrainz_id", "aliases", "sources", "editions",
    "fact1", "fact1_strength", "fact1_source",
    "fact2", "fact2_strength", "fact2_source",
    "fact3", "fact3_strength", "fact3_source",
]  # fmt: skip

GOOD = {
    "title": "Dancing Queen",
    "artist": "ABBA",
    "artist_type": "group",
    "artist_country": "SE",
    "artist_members": "Agnetha Fältskog|Björn Ulvaeus",
    "year": "1976",
    "genre": "Disco/Funk",
    "styles": "Disco",
    "vocal": "female",
    "language": "en",
    "themes": "Party / Dancing|Freedom / Carefree",
    "difficulty": "medium",
    "youtube_id": "xFrGuyw1V8s",
    "aliases": "Dansing Queen",
    "sources": "https://en.wikipedia.org/wiki/Dancing_Queen",
    "fact1": "It was first performed at a royal gala in 1976.",
    "fact1_strength": "easy",
    "fact1_source": "https://en.wikipedia.org/wiki/Dancing_Queen",
    "fact2": "It was the group's only US number one.",
    "fact2_strength": "medium",
    "fact2_source": "https://en.wikipedia.org/wiki/Dancing_Queen",
    "fact3": "The band wanted it as the follow-up to “Mamma Mia”.",
    "fact3_strength": "strong",
    "fact3_source": "https://en.wikipedia.org/wiki/Dancing_Queen",
}


@pytest.fixture(autouse=True)
def _reference() -> None:
    call_command("seed_reference", stdout=StringIO())


def write_csv(
    tmp_path: Path, rows: list[dict], delimiter: str = ",", name: str = "songs.csv"
) -> Path:
    path = tmp_path / name
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADER, delimiter=delimiter)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: row.get(k, "") for k in HEADER})
    return path


def run(path: Path, **kwargs):
    return SongImporter().run(path, **kwargs)


class TestCreate:
    def test_complete_row_creates_a_ready_draft(self, tmp_path) -> None:
        report = run(write_csv(tmp_path, [GOOD]))

        row = report.rows[0]
        song = Song.objects.get(title="Dancing Queen")
        assert (row.status, row.messages) == (RowStatus.CREATED, [])
        assert song.status == SongStatus.DRAFT
        assert (song.year, song.genre.name, song.vocal, song.language.iso_code) == (
            1976, "Disco/Funk", "female", "en",
        )  # fmt: skip
        assert song.primary_artist.country.iso_code == "SE"
        assert sorted(song.primary_artist.members.values_list("name", flat=True)) == [
            "Agnetha Fältskog", "Björn Ulvaeus",
        ]  # fmt: skip
        assert song.song_themes.get(is_primary=True).theme.name == "Party / Dancing"
        assert list(song.facts.values_list("strength", flat=True)) == ["easy", "medium", "strong"]
        assert list(song.editions.values_list("code", flat=True)) == ["world"]
        assert song.aliases.get().alias == "Dansing Queen"

    def test_incomplete_row_is_imported_with_a_readiness_note(self, tmp_path) -> None:
        report = run(
            write_csv(tmp_path, [{"title": "Waterloo", "artist": "ABBA", "artist_country": "SE"}])
        )

        row = report.rows[0]
        assert row.status == RowStatus.CREATED
        assert row.messages[0].startswith("not ready to verify:")

    def test_featured_artist_with_country(self, tmp_path) -> None:
        run(write_csv(tmp_path, [GOOD | {"featured": "Guest Star:US"}]))

        credit = Song.objects.get().song_artists.get(role=ArtistRole.FEATURED)
        assert (credit.artist.name, credit.artist.country.iso_code) == ("Guest Star", "US")

    def test_existing_artist_is_reused_case_insensitively(self, tmp_path) -> None:
        run(write_csv(tmp_path, [GOOD]))
        run(write_csv(tmp_path, [{"title": "Waterloo", "artist": "abba"}], name="b.csv"))

        assert Artist.objects.filter(name__iexact="abba").count() == 1

    @pytest.mark.parametrize("delimiter", [";", "\t"])
    def test_excel_delimiters(self, tmp_path, delimiter) -> None:
        report = run(write_csv(tmp_path, [GOOD], delimiter=delimiter))
        assert report.rows[0].status == RowStatus.CREATED


class TestRejectedRows:
    @pytest.mark.parametrize(
        ("change", "message"),
        [
            ({"title": ""}, "title is required"),
            ({"genre": "Polka"}, "unknown genre “Polka”"),
            ({"styles": "Disco|Space Opera"}, "unknown style “Space Opera”"),
            ({"themes": "Robots"}, "unknown theme “Robots”"),
            ({"language": "xx"}, "unknown language “xx”"),
            ({"editions": "mars"}, "unknown edition “mars”"),
            ({"year": "1976a"}, "is not a number"),
            ({"vocal": "choir"}, "vocal “choir” must be one of"),
            ({"youtube_id": "short"}, "youtube_id “short” must be 11 characters"),
            ({"musicbrainz_id": "nope"}, "is not a valid ID"),
            ({"fact1_source": ""}, "fact1_source is required"),
            ({"fact2_strength": "huge"}, "fact2_strength must be one of"),
            ({"sources": "not a url"}, "source “not a url” is not a valid URL"),
            ({"artist": "New Band", "artist_country": ""}, "is new: give its country"),
            ({"artist": "New Band", "artist_country": "XX"}, "unknown country “XX”"),
            ({"featured": "Nobody New"}, "is new: give its country"),
            ({"year": "2999"}, "year"),
        ],
    )
    def test_reason_is_reported_and_nothing_is_created(self, tmp_path, change, message) -> None:
        report = run(write_csv(tmp_path, [GOOD | change]))

        row = report.rows[0]
        assert row.status == RowStatus.ERROR
        assert any(message in m for m in row.messages), row.messages
        assert not Song.objects.exists()

    def test_unknown_values_are_never_created(self, tmp_path) -> None:
        from apps.catalog.models import Genre

        run(write_csv(tmp_path, [GOOD | {"genre": "Polka"}]))
        assert not Genre.objects.filter(name="Polka").exists()

    def test_one_bad_row_does_not_stop_the_others(self, tmp_path) -> None:
        bad = GOOD | {"title": "Broken", "genre": "Polka"}
        good2 = GOOD | {"title": "Waterloo"}
        report = run(write_csv(tmp_path, [GOOD, bad, good2]))

        assert [r.status for r in report.rows] == [
            RowStatus.CREATED,
            RowStatus.ERROR,
            RowStatus.CREATED,
        ]
        assert [r.row_number for r in report.rows] == [2, 3, 4]


class TestReimport:
    def test_same_file_twice_changes_nothing(self, tmp_path) -> None:
        path = write_csv(tmp_path, [GOOD])
        run(path)
        report = run(path)

        assert report.rows[0].status == RowStatus.UNCHANGED
        assert Song.objects.count() == 1

    def test_draft_is_updated(self, tmp_path) -> None:
        run(write_csv(tmp_path, [GOOD]))
        report = run(write_csv(tmp_path, [GOOD | {"year": "1977"}], name="b.csv"))

        assert report.rows[0].status == RowStatus.UPDATED
        assert Song.objects.get().year == 1977

    def test_blank_cells_keep_existing_data(self, tmp_path) -> None:
        run(write_csv(tmp_path, [GOOD]))
        partial = {"title": "Dancing Queen", "artist": "ABBA", "year": "1977"}
        run(write_csv(tmp_path, [partial], name="b.csv"))

        song = Song.objects.get()
        assert song.facts.count() == 3 and song.aliases.count() == 1 and song.genre is not None

    def test_matched_by_musicbrainz_id_even_if_renamed(self, tmp_path) -> None:
        mbid = "b1a9c0e9-d987-4042-ae91-78d6a3267d69"
        run(write_csv(tmp_path, [GOOD | {"musicbrainz_id": mbid}]))
        run(
            write_csv(
                tmp_path, [GOOD | {"musicbrainz_id": mbid, "title": "Dancing Queen!"}], name="b.csv"
            )
        )

        assert Song.objects.get().title == "Dancing Queen!"

    @pytest.mark.parametrize("status", [SongStatus.REVIEW, SongStatus.VERIFIED])
    def test_reviewed_songs_are_not_overwritten(self, tmp_path, status) -> None:
        run(write_csv(tmp_path, [GOOD]))
        Song.objects.update(status=status)

        report = run(
            write_csv(tmp_path, [GOOD | {"year": "1977", "styles": "Disco|Funk"}], name="b.csv")
        )

        row = report.rows[0]
        assert row.status == RowStatus.CONFLICT
        assert any("year: database “1976” ≠ CSV “1977”" in m for m in row.messages)
        assert any(m.startswith("styles:") for m in row.messages)
        assert Song.objects.get().year == 1976

    def test_unchanged_verified_song_is_not_a_conflict(self, tmp_path) -> None:
        path = write_csv(tmp_path, [GOOD])
        run(path)
        Song.objects.update(status=SongStatus.VERIFIED)

        assert run(path).rows[0].status == RowStatus.UNCHANGED


class TestReport:
    def test_saved_with_every_row(self, tmp_path) -> None:
        report = run(write_csv(tmp_path, [GOOD, GOOD | {"genre": "Polka", "title": "X"}]))

        batch = ImportBatch.objects.get()
        assert report.batch == batch
        assert batch.summary["created"] == 1 and batch.summary["error"] == 1
        assert list(batch.rows.values_list("row_number", "status")) == [
            (2, "created"),
            (3, "error"),
        ]

    def test_dry_run_saves_nothing(self, tmp_path) -> None:
        report = run(write_csv(tmp_path, [GOOD]), dry_run=True)

        assert report.rows[0].status == RowStatus.CREATED
        assert not Song.objects.exists() and not Artist.objects.exists()
        assert not ImportBatch.objects.exists()

    def test_command_output(self, tmp_path) -> None:
        out = StringIO()
        call_command(
            "import_songs", str(write_csv(tmp_path, [GOOD | {"genre": "Polka"}])), stdout=out
        )

        text = out.getvalue()
        assert "row 2: error — Dancing Queen" in text
        assert "unknown genre “Polka”" in text
        assert "Report saved as import #" in text

    def test_command_missing_file(self) -> None:
        with pytest.raises(CommandError, match="File not found"):
            call_command("import_songs", "/nope.csv")

    def test_example_file_from_the_docs(self) -> None:
        example = Path(__file__).resolve().parents[3] / "docs" / "import-example.csv"
        if not example.exists():
            pytest.skip("docs/ is not mounted in this container")
        statuses = [r.status for r in run(example, dry_run=True).rows]
        assert statuses == [RowStatus.CREATED, RowStatus.ERROR]


def test_read_rows_skips_empty_lines_and_strips(tmp_path) -> None:
    path = tmp_path / "x.csv"
    path.write_text("Title , Artist\n  Hello , Adele \n,\n", encoding="utf-8-sig")
    assert read_rows(path) == [{"title": "Hello", "artist": "Adele"}]
