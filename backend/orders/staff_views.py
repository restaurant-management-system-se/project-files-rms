from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.response import Response
from accounts.resources import OwnedResourceView
from accounts.permissions import IsStaffOrAdmin,has_role
from .models import Order
from .services import order_payload,change_status,OrderError
from .serializers import StatusChange
class StaffOrders(OwnedResourceView):
    permission_classes=[IsStaffOrAdmin]
    def get(self,request):
        status=request.query_params.get('status','Received')
        if status not in ['Received','Preparing','Served']:return Response({'detail':'Invalid status.'},status=400)
        try:page=max(1,int(request.query_params.get('page','1')))
        except ValueError:return Response({'detail':'Invalid page.'},status=400)
        qs=Order.objects.filter(status=status).order_by('placed_at','pk')
        return Response({'orders':[order_payload(o) for o in qs[(page-1)*25:page*25]],'page':page,'total':qs.count()})
class StaffStatus(StaffOrders):
    http_method_names=['post','options']
    def post(self,request,pk):
        data=StatusChange(data=request.data);data.is_valid(raise_exception=True)
        try:order,changed=change_status(user=request.user,order_id=pk,**data.validated_data)
        except OrderError as e:return Response({'code':e.code,'message':e.message,'details':e.details},status=e.status)
        return Response(order_payload(order)|{'changed':changed})
@never_cache
@ensure_csrf_cookie
def staff_page(request):
    if not has_role(request.user,'Staff','Admin'):return render(request,'accounts/expired.html',status=403 if request.user.is_authenticated else 401)
    return render(request,'orders/staff.html')
