import logging

import certifi
import requests
from django.conf import settings
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

logger = logging.getLogger(__name__)

CACHE_TIMEOUT = 60 * 60  # 1 hour


class LocationAPIError(Exception):
    """Raised when the upstream location API returns an error."""


def _headers():
    return {"X-CSCAPI-KEY": settings.LOCATION_API_KEY}


def _api_url(path):
    base = settings.LOCATION_API_BASE_URL.rstrip("/")
    return f"{base}/{path.lstrip('/')}"


def _cached_request(cache_key, path):
    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    url = _api_url(path)
    try:
        response = requests.get(
            url,
            headers=_headers(),
            timeout=15,
            verify=certifi.where(),
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.exception("Location API request failed: %s", url)
        raise LocationAPIError("Unable to fetch location data.") from exc

    data = response.json()
    cache.set(cache_key, data, CACHE_TIMEOUT)
    return data


def get_countries():
    return _cached_request("location:countries", "countries")


def get_states(country_code):
    country_code = country_code.upper()
    return _cached_request(
        f"location:states:{country_code}",
        f"countries/{country_code}/states",
    )


def get_cities(country_code, state_code):
    country_code = country_code.upper()
    state_code = state_code.upper()
    return _cached_request(
        f"location:cities:{country_code}:{state_code}",
        f"countries/{country_code}/states/{state_code}/cities",
    )


def _find_by_code(items, code, code_field="iso2"):
    code = code.upper()
    for item in items:
        if str(item.get(code_field, "")).upper() == code:
            return item
    return None


def _find_city_by_name(cities, city_name):
    city_name_lower = city_name.strip().lower()
    for item in cities:
        if str(item.get("name", "")).strip().lower() == city_name_lower:
            return item
    return None


def validate_location(country, state, city):
    """
    Verify country, state, and city exist in the Location API.
    Raises ValidationError if any value is invalid.
    """
    if not country or not state or not city:
        raise ValidationError("Country, state, and city are all required.")

    countries = get_countries()
    country_obj = _find_by_code(countries, country)
    if not country_obj:
        raise ValidationError(f"Invalid country code: {country}")

    country_code = country_obj["iso2"]
    states = get_states(country_code)
    state_obj = _find_by_code(states, state)
    if not state_obj:
        raise ValidationError(f"Invalid state code: {state} for country {country_code}")

    state_code = state_obj.get("iso2") or state_obj.get("state_code") or state
    cities = get_cities(country_code, state_code)
    city_obj = _find_city_by_name(cities, city)
    if not city_obj:
        raise ValidationError(
            f"Invalid city: {city} for state {state_code}, country {country_code}"
        )

    return {
        "country": country_code,
        "state": state_code,
        "city": city_obj["name"],
    }
