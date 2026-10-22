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
