# users/urls.py
from django.urls import path
from .views import register, login, google, google_callback

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("google/", google, name="google"),
    path("auth/google/callback/", google_callback, name="google_callback"),
]
