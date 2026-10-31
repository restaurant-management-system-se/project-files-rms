from decimal import Decimal
from django.contrib.auth import get_user_model
from django.db import connection,transaction
from booking.models import Booking
from menu.models import MenuItem
from .models import Order,OrderItem,OrderRequestKey
class OrderError(Exception):
    def __init__(self,code,message,status=409,details=None):
        self.code,self.message,self.status,self.details=code,message,status,details or {}
        super().__init__(message)

def create_order(*,user,items,context,idempotency_key,booking_id=None):
    if connection.vendor!='postgresql': raise OrderError('POSTGRESQL_REQUIRED','Checkout requires PostgreSQL.',503)
    items=sorted(items,key=lambda i:i['menu_item_id'])
    payload={'items':items,'context':context,'booking_id':booking_id}
    with transaction.atomic(durable=True):
        actor=get_user_model().objects.select_for_update().get(pk=user.pk)
        if not actor.is_active or actor.role!='Customer': raise OrderError('FORBIDDEN','Customer ordering required.',403)
        previous=OrderRequestKey.objects.select_related('order').filter(customer=actor,key=idempotency_key).first()
        if previous:
            if previous.payload!=payload: raise OrderError('IDEMPOTENCY_CONFLICT','Changed requests need a new key.')
            return previous.order,False
        booking=None
        if booking_id is not None:
            booking=Booking.objects.select_for_update().filter(pk=booking_id,customer=actor,status='Confirmed').first()
            if booking is None: raise OrderError('INVALID_BOOKING','Use your own confirmed booking.',400)
        menu={i.pk:i for i in MenuItem.objects.select_for_update().filter(pk__in=[line['menu_item_id'] for line in items]).order_by('pk')}
        invalid=[line['menu_item_id'] for line in items if line['menu_item_id'] not in menu or not menu[line['menu_item_id']].available]
        if invalid: raise OrderError('UNAVAILABLE_ITEMS','Some dishes are no longer available. Review your cart before confirming again.', details={'unavailable_items':[{'menu_item_id':pk,'name':menu[pk].name if pk in menu else 'Removed dish'} for pk in invalid]})
        total=sum((menu[line['menu_item_id']].price*line['quantity'] for line in items),Decimal('0'))
        if total>Decimal('9999999999.99'): raise OrderError('INVALID_TOTAL','Order total exceeds the supported limit.',400)
        order=Order.objects.create(customer=actor,booking=booking,status='Received',total_amount=total)
        OrderItem.objects.bulk_create([OrderItem(order=order,menu_item=menu[line['menu_item_id']],quantity=line['quantity'],unit_price=menu[line['menu_item_id']].price) for line in items])
        OrderRequestKey.objects.create(customer=actor,key=idempotency_key,payload=payload,order=order)
    return order,True

def order_payload(order):
    return {'id':order.pk,'version':order.version,'booking_id':order.booking_id,'context':'booking' if order.booking_id else 'takeaway','status':order.status,'total_amount':str(order.total_amount),'placed_at':order.placed_at,'items':[{'menu_item_id':i.menu_item_id,'name':i.menu_item.name,'quantity':i.quantity,'unit_price':str(i.unit_price),'line_total':str(i.unit_price*i.quantity)} for i in order.items.select_related('menu_item').order_by('pk')]}


def change_status(*,user,order_id,status,expected_version):
    if connection.vendor!='postgresql':raise OrderError('POSTGRESQL_REQUIRED','Status updates require PostgreSQL.',503)
    from menu.services import privileged_change
    with transaction.atomic(durable=True):
        with privileged_change(user):
            try:order=Order.objects.select_for_update().get(pk=order_id)
            except Order.DoesNotExist:raise OrderError('NOT_FOUND','Order not found.',404)
            if order.status==status:return order,False
            if order.version!=expected_version:raise OrderError('VERSION_CONFLICT','Order changed. Reload the queue.')
            if {'Received':'Preparing','Preparing':'Served'}.get(order.status)!=status:
                raise OrderError('INVALID_TRANSITION','Use Received → Preparing → Served.')
            order.status=status;order.version+=1
            order.save(update_fields=['status','version','updated_at'])
    return order,True
