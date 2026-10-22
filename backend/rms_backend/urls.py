from django.contrib import admin
from django.urls import include, path
from accounts import views
from booking.views import BookingReadView, BookingView
from orders.views import OrderReadView

urlpatterns = [
    path("", include("booking.urls")),
    path("admin/", admin.site.urls),
    path("api/auth/", include("accounts.urls")),
    path("register/", views.auth_page, {"mode": "register"}, name="register-page"),
    path("login/", views.auth_page, {"mode": "login"}, name="login-page"),
    path("account/", views.account_page, name="account-page"),
    path("logout/", views.logout_page, name="logout-page"),
    path("api/bookings", BookingView.as_view(), name="booking-create"),
    path("api/bookings/<int:pk>", BookingReadView.as_view()),
    path("api/orders", OrderReadView.as_view()),
    path("api/orders/<int:pk>", OrderReadView.as_view()),
]
