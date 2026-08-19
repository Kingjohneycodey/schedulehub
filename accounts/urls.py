from django.urls import path

from .views import LandingView, OwnerLoginView, OwnerLogoutView, RegisterView

app_name = "accounts"

urlpatterns = [
    path("", LandingView.as_view(), name="landing"),
    path("login/", OwnerLoginView.as_view(), name="login"),
    path("logout/", OwnerLogoutView.as_view(), name="logout"),
    path("register/", RegisterView.as_view(), name="register"),
]
