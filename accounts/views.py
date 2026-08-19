from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import redirect, render
from django.views import View

from scheduler.models import BusinessProfile

from .forms import OwnerRegistrationForm, StyledAuthenticationForm


class LandingView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("scheduler:dashboard")
        return render(request, "accounts/landing.html")


class OwnerLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = StyledAuthenticationForm
    redirect_authenticated_user = True


class OwnerLogoutView(LogoutView):
    next_page = "accounts:login"


class RegisterView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return redirect("scheduler:dashboard")
        return render(request, "accounts/register.html", {"form": OwnerRegistrationForm()})

    def post(self, request):
        form = OwnerRegistrationForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/register.html", {"form": form})

        user = form.save()
        business = BusinessProfile.objects.create(
            owner=user,
            name=form.cleaned_data["business_name"],
            email=user.email,
        )
        business.setup_defaults()
        login(request, user)
        return redirect("scheduler:dashboard")
