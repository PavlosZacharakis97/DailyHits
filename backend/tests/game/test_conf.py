from apps.game.conf import game_config


def test_default_game_rules() -> None:
    config = game_config()

    assert config.max_attempts == 10
    assert config.hint_attempts == (5, 8)
    assert config.year_yellow_range == 5
