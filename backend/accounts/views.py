from time import time
from django.conf import settings
from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST
from rest_framework import status
from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed, ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from .forms import LoginForm, RegistrationForm
from .serializers import LoginSerializer, ProfileSerializer, RegistrationSerializer


def start_session(request, user):
    login(request, user, backend="accounts.authentication.IdentifierBackend")
    request.session["last_activity"] = time()
    request.session.set_expiry(settings.SESSION_IDLE_TIMEOUT)


@method_decorator(never_cache, name="dispatch")
@method_decorator(sensitive_post_parameters("password"), name="dispatch")
class SessionAPIView(APIView):
    """Also protect anonymous login/registration; DRF normally skips their CSRF."""
    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if request.method not in ("GET", "HEAD", "OPTIONS"):
            SessionAuthentication().enforce_csrf(request)


class CSRFView(SessionAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


class RegisterView(SessionAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(ProfileSerializer(user).data, status=status.HTTP_201_CREATED)


class LoginView(SessionAPIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        start_session(request, serializer.validated_data["user"])
        return Response({"user": ProfileSerializer(request.user).data, "csrfToken": get_token(request)})


class LogoutView(SessionAPIView):
    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionView(SessionAPIView):
    def get(self, request):
        return Response({"user": ProfileSerializer(request.user).data,
                         "idleExpiresAt": request.session["last_activity"] + settings.SESSION_IDLE_TIMEOUT})


def add_serializer_errors(form, detail):
    if not isinstance(detail, dict):
        form.add_error(None, "Invalid credentials.")
        return
    for field, errors in detail.items():
        for error in errors if isinstance(errors, list) else [errors]:
            form.add_error(field if field in form.fields else None, str(error))


@never_cache
@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def auth_page(request, mode):
    registration = mode == "register"
    form = (RegistrationForm if registration else LoginForm)(request.POST or None)
    if request.method == "POST" and form.is_valid():
        serializer = (RegistrationSerializer if registration else LoginSerializer)(
            data=form.cleaned_data, context={"request": request})
        try:
            serializer.is_valid(raise_exception=True)
            if registration:
                serializer.save()
                return redirect("login-page")
            start_session(request, serializer.validated_data["user"])
            return redirect("account-page")
        except (ValidationError, AuthenticationFailed) as error:
            add_serializer_errors(form, error.detail)
    return render(request, "accounts/auth.html", {"form": form, "registration": registration},
                  status=400 if request.method == "POST" else 200)


@never_cache
@require_http_methods(["GET"])
def account_page(request):
    if not request.user.is_authenticated:
        return render(request, "accounts/expired.html", status=401)
    return render(request, "accounts/account.html")


@never_cache
@require_POST
def logout_page(request):
    if not request.user.is_authenticated:
        return render(request, "accounts/expired.html", status=401)
    logout(request)
    return redirect("login-page")
