from rest_framework import serializers
class StrictInteger(serializers.IntegerField):
    def to_internal_value(self, data):
        if type(data) is not int:
            self.fail('invalid')
        return super().to_internal_value(data)
class CartLine(serializers.Serializer):
    menu_item_id = StrictInteger(min_value=1)
    quantity = StrictInteger(min_value=1,max_value=99)
class CartWrite(serializers.Serializer):
    items = CartLine(many=True,allow_empty=False,max_length=100)
    def validate_items(self, items):
        if len({i['menu_item_id'] for i in items}) != len(items):
            raise serializers.ValidationError('Combine duplicate dishes into one quantity.')
        return items
