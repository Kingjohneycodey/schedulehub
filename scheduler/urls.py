from django.urls import path

from . import views

app_name = "scheduler"

urlpatterns = [
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("appointments/", views.AppointmentListView.as_view(), name="appointment-list"),
    path("appointments/new/", views.AppointmentCreateView.as_view(), name="appointment-create"),
    path("appointments/slots/", views.SlotListView.as_view(), name="appointment-slots"),
    path("appointments/<int:pk>/", views.AppointmentDetailView.as_view(), name="appointment-detail"),
    path("appointments/<int:pk>/edit/", views.AppointmentUpdateView.as_view(), name="appointment-update"),
    path("appointments/<int:pk>/cancel/", views.AppointmentCancelView.as_view(), name="appointment-cancel"),
    path("appointments/<int:pk>/status/", views.AppointmentStatusView.as_view(), name="appointment-status"),
    path("calendar/", views.CalendarView.as_view(), name="calendar"),
    path("calendar/events/", views.CalendarEventsView.as_view(), name="calendar-events"),
    path("customers/", views.CustomerListView.as_view(), name="customer-list"),
    path("customers/new/", views.CustomerCreateView.as_view(), name="customer-create"),
    path("customers/<int:pk>/", views.CustomerDetailView.as_view(), name="customer-detail"),
    path("customers/<int:pk>/edit/", views.CustomerUpdateView.as_view(), name="customer-update"),
    path("customers/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer-delete"),
    path("services/", views.ServiceListView.as_view(), name="service-list"),
    path("services/new/", views.ServiceCreateView.as_view(), name="service-create"),
    path("services/<int:pk>/edit/", views.ServiceUpdateView.as_view(), name="service-update"),
    path("services/<int:pk>/delete/", views.ServiceDeleteView.as_view(), name="service-delete"),
    path("settings/", views.BusinessSettingsView.as_view(), name="settings-business"),
    path("settings/hours/", views.WorkingHoursView.as_view(), name="settings-hours"),
    path("settings/blocked/", views.BlockedDateListView.as_view(), name="settings-blocked"),
    path("settings/blocked/<int:pk>/delete/", views.BlockedDateDeleteView.as_view(), name="settings-blocked-delete"),
]
