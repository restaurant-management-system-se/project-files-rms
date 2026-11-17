from rest_framework import serializers
from .models import MenuItem
class MenuWrite(serializers.ModelSerializer):
    class Meta:
        model = MenuItem
        fields = ('id', 'name', 'description', 'price', 'category', 'available')
        read_only_fields = ('id',)
        extra_kwargs = {'price': {'min_value': 0}, 'name': {'allow_blank': False, 'trim_whitespace': True}}
    def to_internal_value(self, data):
        if isinstance(data, dict) and set(data) - (set(self.fields) - {'id'}):
            raise serializers.ValidationError({'non_field_errors':['Unknown fields are not accepted.']})
        return super().to_internal_value(data)
