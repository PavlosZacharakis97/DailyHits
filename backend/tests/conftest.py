import pytest


@pytest.fixture(autouse=True)
def _plain_http(settings) -> None:
    """Tests talk plain HTTP; prod-only redirects would turn every response into 301."""
    settings.SECURE_SSL_REDIRECT = False
