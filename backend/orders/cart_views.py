from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.cache import never_cache
from accounts.resources import OwnedResourceView
from accounts.permissions import has_role
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .cart import cart_payload, replace_cart

class CartView(OwnedResourceView):
    permission_classes = [IsAuthenticated]
    def initial(self,request,*args,**kwargs):
        super().initial(request,*args,**kwargs)
        if request.user.role != 'Customer': raise PermissionDenied('Customer cart required.')
    def get(self,request): return Response(cart_payload(request))
    def post(self,request): return Response(replace_cart(request,request.data))
    def delete(self,request):
        request.session['rms_cart']=[]
        return Response(cart_payload(request))

@never_cache
@ensure_csrf_cookie
def cart_page(request):
    if not has_role(request.user,'Customer'):
        return render(request,'accounts/expired.html',status=403 if request.user.is_authenticated else 401)
    return render(request,'orders/cart.html')
