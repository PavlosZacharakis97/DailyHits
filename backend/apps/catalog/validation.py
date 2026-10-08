"""Song completeness rules that a database constraint cannot express.

The same rules back the admin (save + bulk “verify” action), the problem badges
in the song list and the validate_data command. Errors block the “verified”
status; warnings are shown but do not block.
"""

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum

from django.utils.translation import gettext as _

from apps.catalog.models import Song

MIN_FACTS = 3
MAX_STYLES = 2
MAX_THEMES = 2


class Level(StrEnum):
    ERROR = "error"
    WARNING = "warning"


@dataclass(frozen=True, slots=True)
class Issue:
    code: str
    level: Level
    message: str


def normalize(text: str) -> str:
    """Case- and accent-insensitive form used for name matching."""
    decomposed = unicodedata.normalize("NFKD", text)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).casefold()


def mentions(text: str, name: str) -> bool:
    """True if ``name`` occurs in ``text`` as a whole word, ignoring case and accents."""
    needle = normalize(name).strip()
    if not needle:
        return False
    return re.search(rf"(?<!\w){re.escape(needle)}(?!\w)", normalize(text)) is not None


def forbidden_names(song: Song) -> list[str]:
    """Names a hint fact must not contain: title, aliases, artists and their members."""
    names = [song.title, *(a.alias for a in song.aliases.all())]
    for credit in song.song_artists.all():
        names.append(credit.artist.name)
        names.extend(m.person.name for m in credit.artist.memberships.all())
    return list(dict.fromkeys(n for n in names if n and n.strip()))


def song_issues(song: Song) -> list[Issue]:
    """All problems of a saved song. Prefetch with ``SONG_ISSUE_PREFETCH`` for lists."""
    issues: list[Issue] = []

    def error(code: str, message: str) -> None:
        issues.append(Issue(code, Level.ERROR, message))

    def warning(code: str, message: str) -> None:
        issues.append(Issue(code, Level.WARNING, message))

    if song.year is None:
        error("missing_year", _("No year."))
    if song.genre_id is None:
        error("missing_genre", _("No genre."))
    if song.language_id is None:
        error("missing_language", _("No language."))
    if not song.vocal:
        error("missing_vocal", _("No vocal."))

    styles = list(song.styles.all())
    if not styles:
        error("no_styles", _("No styles."))
    elif len(styles) > MAX_STYLES:
        error("too_many_styles", _("More than %(n)s styles.") % {"n": MAX_STYLES})

    themes = list(song.song_themes.all())
    if not themes:
        error("no_themes", _("No themes."))
    else:
        if len(themes) > MAX_THEMES:
            error("too_many_themes", _("More than %(n)s themes.") % {"n": MAX_THEMES})
        if sum(t.is_primary for t in themes) != 1:
            error("primary_theme", _("Exactly one theme must be primary."))

    if not song.editions.all():
        error("no_editions", _("Not part of any edition."))

    facts = list(song.facts.all())
    if not facts:
        error("no_facts", _("No facts."))
    elif len(facts) < MIN_FACTS:
        error("few_facts", _("Fewer than %(n)s facts.") % {"n": MIN_FACTS})
    if any(not f.source_url.strip() for f in facts):
        error("fact_no_source", _("A fact has no source."))
    names = forbidden_names(song)
    for fact in facts:
        leaked = [n for n in names if mentions(fact.text, n)]
        if leaked:
            error(
                "fact_mentions_answer",
                _("Fact #%(order)s mentions “%(name)s”.")
                % {"order": fact.order, "name": leaked[0]},
            )

    if not song.youtube_video_id:
        warning("no_youtube", _("No YouTube video."))
    if not song.sources:
        warning("no_sources", _("No sources."))
    return issues


def verification_errors(song: Song) -> list[Issue]:
    return [i for i in song_issues(song) if i.level is Level.ERROR]


SONG_ISSUE_PREFETCH = (
    "styles",
    "song_themes",
    "editions",
    "facts",
    "aliases",
    "song_artists__artist__memberships__person",
)
