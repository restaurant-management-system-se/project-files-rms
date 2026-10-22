from uuid import uuid4
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers
from .models import User


class StrictSerializer(serializers.Serializer):
    def to_internal_value(self, data):
        if not isinstance(data, dict):
            raise serializers.ValidationError({"non_field_errors": ["Expected an object."]})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({"non_field_errors": ["Unexpected fields are not accepted."]})
        return super().to_internal_value(data)


class RegistrationSerializer(StrictSerializer):
    name = serializers.CharField(max_length=60)
    email = serializers.EmailField(max_length=254)
    phone = serializers.RegexField(r"^\+?[0-9]{7,15}$", max_length=16, required=False, allow_blank=True)
    password = serializers.CharField(min_length=8, max_length=128, write_only=True, trim_whitespace=False)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("This email is already registered.")
        return value

    def validate_phone(self, value):
        if value and User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("This phone is already registered.")
        return value or None

    def validate(self, attrs):
        candidate = User(email=attrs["email"], first_name=attrs["name"], phone=attrs.get("phone"))
        try:
            validate_password(attrs["password"], candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": error.messages})
        return attrs

    def create(self, validated_data):
        # No role, permission or ownership fields ever come from a public request.
        try:
            with transaction.atomic():
                return User.objects.create_user(
                    username="customer_" + uuid4().hex,
                    email=validated_data["email"], phone=validated_data.get("phone"),
                    first_name=validated_data["name"], password=validated_data["password"],
                )
        except IntegrityError:
            # Concurrent duplicate registration must be a validation error, not a 500.
            raise serializers.ValidationError({"non_field_errors": ["An account with these identifiers already exists."]})


class LoginSerializer(StrictSerializer):
    identifier = serializers.CharField(max_length=254)
    password = serializers.CharField(max_length=128, write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        user = authenticate(request=self.context.get("request"), **attrs)
        if user is None:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed("Invalid credentials.")
        attrs["user"] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source="first_name", read_only=True)

    class Meta:
        model = User
        fields = ("id", "name", "email", "phone", "role")
        read_only_fields = fields
