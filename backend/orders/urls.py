from django.urls import path
from . import cart_views
urlpatterns = [path('api/cart',cart_views.CartView.as_view()),path('cart/',cart_views.cart_page)]
