from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "ScheduleHub Admin"
admin.site.site_title = "ScheduleHub"
admin.site.index_title = "Business scheduling"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("scheduler.urls")),
]
