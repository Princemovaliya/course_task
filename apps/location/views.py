from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CitySerializer, CountrySerializer, StateSerializer
from .services import LocationAPIError, get_cities, get_countries, get_states


class CountryListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CountrySerializer(many=True)})
    def get(self, request):
        try:
            data = get_countries()
        except LocationAPIError:
            return Response(
                {"error": "Location service unavailable", "detail": "Could not fetch countries."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = CountrySerializer(data, many=True)
        return Response(serializer.data)


class StateListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="country",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ISO2 country code (e.g. IN)",
            )
        ],
        responses={200: StateSerializer(many=True)},
    )
    def get(self, request):
        country = request.query_params.get("country")
        if not country:
            return Response(
                {"error": "Validation error", "detail": "Query parameter 'country' is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = get_states(country)
        except LocationAPIError:
            return Response(
                {"error": "Location service unavailable", "detail": "Could not fetch states."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = StateSerializer(data, many=True)
        return Response(serializer.data)


class CityListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="country",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="ISO2 country code (e.g. IN)",
            ),
            OpenApiParameter(
                name="state",
                type=str,
                location=OpenApiParameter.QUERY,
                required=True,
                description="State ISO2 code (e.g. GJ)",
            ),
        ],
        responses={200: CitySerializer(many=True)},
    )
    def get(self, request):
        country = request.query_params.get("country")
        state = request.query_params.get("state")
        if not country or not state:
            return Response(
                {
                    "error": "Validation error",
                    "detail": "Query parameters 'country' and 'state' are required.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            data = get_cities(country, state)
        except LocationAPIError:
            return Response(
                {"error": "Location service unavailable", "detail": "Could not fetch cities."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        serializer = CitySerializer(data, many=True)
        return Response(serializer.data)
