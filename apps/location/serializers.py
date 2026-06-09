from rest_framework import serializers


class CountrySerializer(serializers.Serializer):
    iso2 = serializers.CharField()
    name = serializers.CharField()
    iso3 = serializers.CharField(required=False, allow_null=True)
    phonecode = serializers.CharField(required=False, allow_null=True)


class StateSerializer(serializers.Serializer):
    iso2 = serializers.CharField(required=False, allow_null=True)
    state_code = serializers.CharField(required=False, allow_null=True)
    name = serializers.CharField()
    country_code = serializers.CharField(required=False, allow_null=True)

    def to_representation(self, instance):
        data = super().to_representation(instance)
        if not data.get("iso2") and data.get("state_code"):
            data["iso2"] = data["state_code"]
        return data


class CitySerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
    name = serializers.CharField()
    state_code = serializers.CharField(required=False, allow_null=True)
    country_code = serializers.CharField(required=False, allow_null=True)
