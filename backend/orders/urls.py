from django.urls import path
from . import cart_views
urlpatterns = [path('api/cart',cart_views.CartView.as_view()),path('cart/',cart_views.cart_page)]

from . import staff_views
urlpatterns += [path('api/staff/orders',staff_views.StaffOrders.as_view()),path('api/staff/orders/<int:pk>/status',staff_views.StaffStatus.as_view()),path('staff/orders/',staff_views.staff_page)]
