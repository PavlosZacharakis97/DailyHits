"""One error format for the whole API: {"error": {"code", "message", "details"?}}."""

from typing import Any

from rest_framework import exceptions
from rest_framework.response import Response
from rest_framework.views import exception_handler


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    response = exception_handler(exc, context)
    if response is None:
        return None  # unexpected error: Django's 500 handling and logging

    if isinstance(exc, exceptions.ValidationError):
        body = {"code": "invalid", "message": "The request is invalid.", "details": response.data}
    else:
        detail = getattr(exc, "detail", "")
        codes = exc.get_codes() if isinstance(exc, exceptions.APIException) else "error"
        body = {"code": codes if isinstance(codes, str) else "error", "message": str(detail)}
        if isinstance(exc, exceptions.Throttled) and exc.wait is not None:
            body["details"] = {"retry_after": int(exc.wait) + 1}

    response.data = {"error": body}
    return response
