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


class Checkout(CartWrite):
    context = serializers.ChoiceField(choices=['takeaway','booking'])
    booking_id = StrictInteger(min_value=1,required=False)
    idempotency_key = serializers.UUIDField()
    def to_internal_value(self,data):
        if isinstance(data,dict) and set(data)-set(self.fields):
            raise serializers.ValidationError({'non_field_errors':['Unknown fields, including client prices, are not accepted.']})
        for line in data.get('items',[]) if isinstance(data,dict) and isinstance(data.get('items'),list) else []:
            if isinstance(line,dict) and set(line)-{'menu_item_id','quantity'}:
                raise serializers.ValidationError({'items':['Only item ID and quantity are accepted.']})
        return super().to_internal_value(data)
    def validate(self,data):
        if (data['context']=='booking') != ('booking_id' in data):
            raise serializers.ValidationError({'booking_id':['Provide an owned booking only for booking context.']})
        return data
