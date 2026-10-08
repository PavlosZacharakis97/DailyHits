from collections.abc import Callable

from django.http import HttpRequest, HttpResponse
from django.utils import translation


class EnglishApiMiddleware:
    """The game is English-only: never translate API responses, whatever the browser asks.

    Must come after LocaleMiddleware, which picks the admin language.
    """

    def __init__(self, get_response: Callable[[HttpRequest], HttpResponse]) -> None:
        self.get_response = get_response

    def __call__(self, request: HttpRequest) -> HttpResponse:
        if request.path.startswith("/api/"):
            translation.activate("en")
            request.LANGUAGE_CODE = "en"
        return self.get_response(request)
