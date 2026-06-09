from unittest.mock import patch

import pytest
from django.core.cache import cache
from rest_framework import status
from rest_framework.test import APIClient

from apps.accounts.models import User
from apps.location.services import validate_location

pytestmark = pytest.mark.django_db

SAMPLE_COUNTRIES = [{"iso2": "IN", "name": "India", "iso3": "IND"}]
SAMPLE_STATES = [{"iso2": "GJ", "name": "Gujarat", "country_code": "IN"}]
SAMPLE_CITIES = [{"id": 1, "name": "Ahmedabad", "state_code": "GJ", "country_code": "IN"}]


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user():
    return User.objects.create_user(
        email="student@example.com",
        password="password123",
        role=User.Role.STUDENT,
        first_name="Test",
        last_name="Student",
    )


@pytest.fixture(autouse=True)
def clear_cache():
    cache.clear()
    yield
    cache.clear()


@patch("apps.location.services.get_cities")
@patch("apps.location.services.get_states")
@patch("apps.location.services.get_countries")
def test_validate_location_success(mock_countries, mock_states, mock_cities):
    mock_countries.return_value = SAMPLE_COUNTRIES
    mock_states.return_value = SAMPLE_STATES
    mock_cities.return_value = SAMPLE_CITIES

    result = validate_location("IN", "GJ", "Ahmedabad")
    assert result == {"country": "IN", "state": "GJ", "city": "Ahmedabad"}


@patch("apps.location.services.get_countries")
def test_validate_location_invalid_country(mock_countries):
    mock_countries.return_value = SAMPLE_COUNTRIES

    with pytest.raises(Exception) as exc:
        validate_location("XX", "GJ", "Ahmedabad")
    assert "Invalid country" in str(exc.value)


@patch("apps.location.views.get_countries")
def test_countries_endpoint_requires_auth(mock_get_countries, api_client):
    mock_get_countries.return_value = SAMPLE_COUNTRIES
    response = api_client.get("/api/location/countries/")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@patch("apps.location.views.get_countries")
def test_countries_endpoint_returns_data(mock_get_countries, api_client, student_user):
    mock_get_countries.return_value = SAMPLE_COUNTRIES
    api_client.force_authenticate(user=student_user)

    response = api_client.get("/api/location/countries/")
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["iso2"] == "IN"


@patch("apps.location.views.get_states")
def test_states_endpoint_requires_country(mock_get_states, api_client, student_user):
    api_client.force_authenticate(user=student_user)
    response = api_client.get("/api/location/states/")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("apps.location.views.get_states")
def test_states_endpoint_returns_data(mock_get_states, api_client, student_user):
    mock_get_states.return_value = SAMPLE_STATES
    api_client.force_authenticate(user=student_user)

    response = api_client.get("/api/location/states/?country=IN")
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["name"] == "Gujarat"


@patch("apps.location.views.get_cities")
def test_cities_endpoint_requires_params(mock_get_cities, api_client, student_user):
    api_client.force_authenticate(user=student_user)
    response = api_client.get("/api/location/cities/?state=GJ")
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@patch("apps.location.views.get_cities")
def test_cities_endpoint_returns_data(mock_get_cities, api_client, student_user):
    mock_get_cities.return_value = SAMPLE_CITIES
    api_client.force_authenticate(user=student_user)

    response = api_client.get("/api/location/cities/?country=IN&state=GJ")
    assert response.status_code == status.HTTP_200_OK
    assert response.data[0]["name"] == "Ahmedabad"


def test_city_selector_page_is_public(api_client):
    response = api_client.get("/location/select/")
    assert response.status_code == status.HTTP_200_OK
    assert "City Selector" in response.content.decode()
