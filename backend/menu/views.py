from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from accounts.resources import OwnedResourceView
from accounts.permissions import IsRestaurantAdmin, has_role
from .models import MenuItem
from .serializers import MenuWrite
from .services import save_menu, delete_menu

class MenuManage(OwnedResourceView):
    permission_classes = [IsRestaurantAdmin]
    def get(self, request, pk=None):
        qs = MenuItem.objects.order_by('category', 'name', 'pk')
        if pk is not None:
            try: return Response(MenuWrite(qs.get(pk=pk)).data)
            except MenuItem.DoesNotExist: raise NotFound()
        return Response(MenuWrite(qs[:500], many=True).data)
    def post(self, request):
        data = MenuWrite(data=request.data)
        data.is_valid(raise_exception=True)
        return Response(MenuWrite(save_menu(request.user, data)).data, status=201)
    def patch(self, request, pk):
        data = MenuWrite(data=request.data, partial=True)
        data.is_valid(raise_exception=True)
        try: item = save_menu(request.user, data, pk)
        except MenuItem.DoesNotExist: raise NotFound()
        return Response(MenuWrite(item).data)
    def delete(self, request, pk):
        try: deleted = delete_menu(request.user, pk)
        except MenuItem.DoesNotExist: raise NotFound()
        return Response(status=204) if deleted else Response({'deleted': False, 'available': False, 'reason': 'Order history retained.'})

@never_cache
@ensure_csrf_cookie
def manage_page(request):
    if not has_role(request.user, 'Admin'):
        return render(request, 'accounts/expired.html', status=403 if request.user.is_authenticated else 401)
    return render(request, 'menu/manage.html')


from rest_framework.permissions import AllowAny
class PublicMenu(MenuManage):
    permission_classes = [AllowAny]
    authentication_classes = []
    http_method_names = ['get','head','options']
    def get(self, request):
        items = MenuItem.objects.filter(available=True).order_by('name','pk')
        grouped = [{'category': category, 'items': MenuWrite([i for i in items if i.category == category],many=True).data} for category in MenuItem.Category.values]
        return Response({'categories': grouped})

@never_cache
def menu_page(request):
    return render(request, 'menu/menu.html')
