from django.urls import path, register_converter

from apps.game import api


class DayConverter:
    """“today” or YYYY-MM-DD; anything else falls through to the JSON 404."""

    regex = r"today|\d{4}-\d{2}-\d{2}"

    def to_python(self, value: str) -> str:
        return value

    def to_url(self, value: str) -> str:
        return value


register_converter(DayConverter, "day")

urlpatterns = [
    path("puzzles/<day:day>", api.PuzzleView.as_view(), name="puzzle"),
    path("puzzles/<day:day>/guess", api.GuessView.as_view(), name="puzzle-guess"),
    path("puzzles/<day:day>/hints", api.HintsView.as_view(), name="puzzle-hints"),
    path("puzzles/<day:day>/give-up", api.GiveUpView.as_view(), name="puzzle-give-up"),
    path("puzzles/<day:day>/reveal", api.RevealView.as_view(), name="puzzle-reveal"),
    path("songs/search", api.SongSearchView.as_view(), name="song-search"),
]
