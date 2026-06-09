from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "email", "role", "first_name", "last_name", "created_at")
        read_only_fields = fields


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.USERNAME_FIELD

    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "role",
            "first_name",
            "last_name",
        )
        read_only_fields = ("id",)
    def validate_password(self, value):
        validate_password(value)   
        return value

    def validate_role(self, value):
        if value not in (User.Role.STUDENT, User.Role.INSTRUCTOR):
            raise serializers.ValidationError("Role must be 'student' or 'instructor'.")
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)





class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()
