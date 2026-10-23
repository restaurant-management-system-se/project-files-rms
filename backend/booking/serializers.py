from collections.abc import Mapping
from datetime import datetime

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import serializers


class AwareDateTimeField(serializers.DateTimeField):
    def to_internal_value(self, value):
        try:
            parsed = value if isinstance(value, datetime) else parse_datetime(value)
        except (TypeError, ValueError):
            parsed = None
        if parsed is None or timezone.is_naive(parsed) or parsed.year >= 9999:
            raise serializers.ValidationError("Use ISO-8601 date/time with a timezone offset.")
        return super().to_internal_value(value)


class StrictIntegerField(serializers.IntegerField):
    def to_internal_value(self, data):
        if isinstance(data, bool) or isinstance(data, float):
            raise serializers.ValidationError("Enter a whole number.")
        return super().to_internal_value(data)


class AvailabilityQuery(serializers.Serializer):
    start_at = AwareDateTimeField()
    party_size = StrictIntegerField(min_value=1, max_value=32767)

    def validate(self, attrs):
        if attrs["start_at"] <= timezone.now():
            raise serializers.ValidationError({"start_at": "Choose a future date and time."})
        return attrs


class BookingCreate(AvailabilityQuery):
    table_id = StrictIntegerField(min_value=1, max_value=9223372036854775807)
    idempotency_key = serializers.RegexField(r"\A[A-Za-z0-9_-]{1,128}\Z", trim_whitespace=False)

    def to_internal_value(self, data):
        if not isinstance(data, Mapping):
            raise serializers.ValidationError({"non_field_errors": "Expected a JSON object."})
        unknown = set(data) - set(self.fields)
        if unknown:
            raise serializers.ValidationError({name: "This field is not accepted." for name in unknown})
        return super().to_internal_value(data)

    def validate(self, attrs):
        # A successful retry may arrive after the original start; service checks
        # the durable key before applying the future-time rule to new bookings.
        return attrs
