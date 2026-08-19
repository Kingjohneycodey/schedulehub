from .models import BusinessProfile


def business_profile(request):
    if not request.user.is_authenticated:
        return {"business": None}
    business = BusinessProfile.objects.filter(owner=request.user).first()
    return {"business": business}
