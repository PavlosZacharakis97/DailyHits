"""Response/request shapes of the game API (also the source of the OpenAPI schema)."""

from rest_framework import serializers

from apps.game.comparison import Color, Direction, TileKey
from apps.game.models import SessionStatus


class SongBriefSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    artist = serializers.CharField()


class TileSerializer(serializers.Serializer):
    key = serializers.ChoiceField(choices=[k.value for k in TileKey])
    value = serializers.CharField()
    color = serializers.ChoiceField(choices=[c.value for c in Color])
    direction = serializers.ChoiceField(
        choices=[d.value for d in Direction], allow_null=True, required=False
    )


class GuessSerializer(serializers.Serializer):
    attempt = serializers.IntegerField()
    song = SongBriefSerializer()
    tiles = TileSerializer(many=True)


class HintSerializer(serializers.Serializer):
    number = serializers.IntegerField()
    text = serializers.CharField()


class HintsSerializer(serializers.Serializer):
    hints = HintSerializer(many=True)


class PuzzleStateSerializer(serializers.Serializer):
    edition = serializers.CharField()
    date = serializers.DateField()
    number = serializers.IntegerField()
    max_attempts = serializers.IntegerField()
    hint_attempts = serializers.ListField(child=serializers.IntegerField())
    year_yellow_range = serializers.IntegerField()
    status = serializers.ChoiceField(choices=SessionStatus.values)
    attempts_used = serializers.IntegerField()
    attempts_left = serializers.IntegerField()
    guesses = GuessSerializer(many=True)
    hints = HintSerializer(many=True)


class GuessRequestSerializer(serializers.Serializer):
    song_id = serializers.IntegerField(min_value=1)


class GuessResponseSerializer(serializers.Serializer):
    guess = GuessSerializer()
    status = serializers.ChoiceField(choices=SessionStatus.values)
    attempts_used = serializers.IntegerField()
    attempts_left = serializers.IntegerField()
    hints = HintSerializer(many=True)


class RevealFactSerializer(serializers.Serializer):
    text = serializers.CharField()
    strength = serializers.CharField()
    source_url = serializers.URLField()


class RevealSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    artist = serializers.CharField()
    featured = serializers.ListField(child=serializers.CharField())
    year = serializers.IntegerField()
    youtube_url = serializers.URLField()
    facts = RevealFactSerializer(many=True)


class ErrorBodySerializer(serializers.Serializer):
    code = serializers.CharField()
    message = serializers.CharField()
    details = serializers.JSONField(required=False)


class ErrorSerializer(serializers.Serializer):
    error = ErrorBodySerializer()
