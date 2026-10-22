from django.urls import path
from . import views

urlpatterns = [
    path("csrf", views.CSRFView.as_view()),
    path("register", views.RegisterView.as_view()),
    path("login", views.LoginView.as_view()),
    path("logout", views.LogoutView.as_view()),
    path("session", views.SessionView.as_view()),
]
