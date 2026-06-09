"""Shared test helpers for paginated API responses."""


def get_results(response):
    """Extract list items from paginated or plain list responses."""
    if isinstance(response.data, dict) and "results" in response.data:
        return response.data["results"]
    return response.data
