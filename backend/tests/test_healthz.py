from unittest import mock

import pytest
from django.db import OperationalError
from django.test import Client
from django.urls import reverse


@pytest.mark.django_db
def test_healthz_ok(client: Client) -> None:
    response = client.get(reverse("healthz"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}
    assert "no-cache" in response["Cache-Control"]


@pytest.mark.django_db
def test_healthz_reports_unavailable_database(client: Client) -> None:
    with mock.patch("config.views.connection.cursor", side_effect=OperationalError):
        response = client.get(reverse("healthz"))

    assert response.status_code == 503
    assert response.json() == {"status": "error", "database": "unavailable"}


def test_healthz_rejects_post(client: Client) -> None:
    assert client.post(reverse("healthz")).status_code == 405


@pytest.mark.django_db
def test_admin_login_page_is_served(client: Client, settings) -> None:
    response = client.get(f"/{settings.ADMIN_URL}login/")

    assert response.status_code == 200
