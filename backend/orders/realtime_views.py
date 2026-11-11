import secrets
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render,get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from accounts.models import User
from accounts.permissions import owned_queryset
from .models import Order,OrderEvent
from .events import event_payload

def internal_allowed(request):
    key=getattr(settings,'RMS_REALTIME_KEY','')
    return len(key)>=32 and secrets.compare_digest(request.headers.get('X-RMS-Key',''),key)
@never_cache
@require_GET
def order_access(request,pk):
    if not internal_allowed(request):return JsonResponse({'detail':'Forbidden'},status=403)
    try:actor_id=int(request.headers.get('X-RMS-Actor',''))
    except ValueError:return JsonResponse({'detail':'Forbidden'},status=403)
    actor=User.objects.filter(pk=actor_id,is_active=True).first()
    order=Order.objects.filter(pk=pk).first()
    if not actor or not order or not(actor.role in ['Staff','Admin'] or actor.role=='Customer' and order.customer_id==actor.pk):
        return JsonResponse({'detail':'Forbidden'},status=403)
    return JsonResponse({'order_id':order.pk,'version':order.version})
@never_cache
@require_GET
def committed_event(request,event_id):
    if not internal_allowed(request):return JsonResponse({'detail':'Forbidden'},status=403)
    event=get_object_or_404(OrderEvent,pk=event_id)
    return JsonResponse(event_payload(event))
@never_cache
def tracking_page(request,pk):
    if not request.user.is_authenticated:return render(request,'accounts/expired.html',status=401)
    order=get_object_or_404(owned_queryset(Order.objects.all(),request.user),pk=pk)
    return render(request,'orders/tracking.html',{'order':order})
