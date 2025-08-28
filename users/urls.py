# users/urls.py
from django.urls import path
from .views import register, login, google

urlpatterns = [
    path("register/", register, name="register"),
    path("login/", login, name="login"),
    path("google/", google, name="google"),
]
