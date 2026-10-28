from accounts.resources import OwnedResourceView
from rest_framework.response import Response
from .models import Order
from .serializers import Checkout
from .services import create_order,order_payload,OrderError

class OrderReadView(OwnedResourceView):
    model = Order
    fields = ('id','booking_id','status','total_amount','placed_at')
    def get(self,request,pk=None):
        response=super().get(request,pk)
        return Response(order_payload(Order.objects.get(pk=pk))) if pk is not None else response
    def post(self,request,pk=None):
        if pk is not None: return Response(status=405)
        if request.user.role!='Customer': return Response({'detail':'Customer ordering required.'},status=403)
        data=Checkout(data=request.data);data.is_valid(raise_exception=True)
        try:order,created=create_order(user=request.user,**data.validated_data)
        except OrderError as e:return Response({'code':e.code,'message':e.message,'details':e.details},status=e.status)
        request.session['rms_cart']=[]
        return Response(order_payload(order),status=201 if created else 200)
