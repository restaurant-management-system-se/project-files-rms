from decimal import Decimal
from menu.models import MenuItem
from .serializers import CartWrite
from rest_framework.exceptions import ValidationError

def replace_cart(request, data):
    serializer = CartWrite(data=data); serializer.is_valid(raise_exception=True)
    items=serializer.validated_data['items']
    available=set(MenuItem.objects.filter(pk__in=[i['menu_item_id'] for i in items],available=True).values_list('pk',flat=True))
    missing=[i['menu_item_id'] for i in items if i['menu_item_id'] not in available]
    if missing: raise ValidationError({'unavailable_items':missing})
    request.session['rms_cart']=items
    return cart_payload(request)

def cart_payload(request):
    lines=request.session.get('rms_cart',[])
    menu=MenuItem.objects.in_bulk([i['menu_item_id'] for i in lines])
    result=[]; total=Decimal('0')
    for line in lines:
        item=menu.get(line['menu_item_id']); amount=(item.price*line['quantity']) if item else Decimal('0')
        result.append(line|{'name':item.name if item else 'Removed dish','available':bool(item and item.available),'unit_price':str(item.price) if item else None,'line_total':str(amount)})
        total+=amount
    return {'items':result,'total':str(total),'provisional':True}
