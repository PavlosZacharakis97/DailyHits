"""API errors with stable codes; rendered as {"error": {"code", "message"}}."""

from rest_framework import status
from rest_framework.exceptions import APIException


class GameError(APIException):
    status_code = status.HTTP_409_CONFLICT


class EditionNotFound(GameError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "edition_not_found"
    default_detail = "This edition does not exist."


class PuzzleNotFound(GameError):
    status_code = status.HTTP_404_NOT_FOUND
    default_code = "puzzle_not_found"
    default_detail = "There is no puzzle for this date."


class UnknownSong(GameError):
    status_code = status.HTTP_400_BAD_REQUEST
    default_code = "unknown_song"
    default_detail = "This song is not part of the game."


class GameOver(GameError):
    default_code = "game_over"
    default_detail = "This game is already finished."


class AlreadyGuessed(GameError):
    default_code = "already_guessed"
    default_detail = "You have already tried this song."


class NoAttemptsLeft(GameError):
    default_code = "no_attempts_left"
    default_detail = "You have used all your guesses."


class GameInProgress(GameError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "game_in_progress"
    default_detail = "The answer is revealed only after the game ends."


class ConsentRequired(GameError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "consent_required"
    default_detail = "Accept the essential cookies to play."


class BadOrigin(GameError):
    status_code = status.HTTP_403_FORBIDDEN
    default_code = "bad_origin"
    default_detail = "Requests must come from the game website."
