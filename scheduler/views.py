import json
from collections import Counter
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, TemplateView, UpdateView

from .availability import get_available_slots
from .forms import (
    AppointmentForm,
    BlockedDateForm,
    BusinessProfileForm,
    CustomerForm,
    ServiceForm,
    WorkingHoursFormSet,
)
from .models import Appointment, BlockedDate, BusinessProfile, Customer, Service


class BusinessRequiredMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        self.business = BusinessProfile.objects.filter(owner=request.user).first()
        if not self.business:
            raise Http404("No business profile is linked to this account.")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["business"] = self.business
        return context


class DashboardView(BusinessRequiredMixin, TemplateView):
    template_name = "scheduler/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        appointments = self.business.appointments.select_related("customer", "service")
        today_qs = appointments.filter(date=today).exclude(status=Appointment.STATUS_CANCELLED)
        upcoming = appointments.filter(date__gte=today).exclude(
            status__in=[Appointment.STATUS_CANCELLED, Appointment.STATUS_COMPLETED]
        )
        # Weekly chart: appointments per day (Mon–Sun of this week)
        start_of_week = today - timedelta(days=today.weekday())
        week_days = [start_of_week + timedelta(days=i) for i in range(7)]
        week_labels = [d.strftime("%a") for d in week_days]
        week_qs = appointments.filter(
            date__gte=start_of_week, date__lte=week_days[-1]
        ).exclude(status=Appointment.STATUS_CANCELLED)
        week_counts = Counter(item.date for item in week_qs)
        week_data = [week_counts.get(d, 0) for d in week_days]

        # Service chart: appointments per service (all time, non-cancelled)
        service_qs = appointments.exclude(status=Appointment.STATUS_CANCELLED)
        service_counts = Counter(item.service.name for item in service_qs)
        service_labels = list(service_counts.keys()) or ["No data"]
        service_data = list(service_counts.values()) or [0]

        context.update(
            {
                "today": today,
                "today_count": today_qs.count(),
                "upcoming_count": upcoming.count(),
                "customer_count": self.business.customers.count(),
                "service_count": self.business.services.filter(is_active=True).count(),
                "today_schedule": today_qs.order_by("start_time"),
                "upcoming_list": upcoming.order_by("date", "start_time")[:6],
                "week_labels": json.dumps(week_labels),
                "week_data": json.dumps(week_data),
                "service_labels": json.dumps(service_labels),
                "service_data": json.dumps(service_data),
            }
        )
        return context


class AppointmentListView(BusinessRequiredMixin, ListView):
    template_name = "scheduler/appointments/list.html"
    context_object_name = "appointments"
    paginate_by = 15

    def get_queryset(self):
        qs = self.business.appointments.select_related("customer", "service")
        status = self.request.GET.get("status")
        search = self.request.GET.get("q", "").strip()
        if status:
            qs = qs.filter(status=status)
        if search:
            qs = qs.filter(
                Q(customer__first_name__icontains=search)
                | Q(customer__last_name__icontains=search)
                | Q(customer__company__icontains=search)
                | Q(service__name__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["status_filter"] = self.request.GET.get("status", "")
        context["search"] = self.request.GET.get("q", "")
        context["statuses"] = Appointment.STATUS_CHOICES
        return context


class AppointmentDetailView(BusinessRequiredMixin, DetailView):
    template_name = "scheduler/appointments/detail.html"
    context_object_name = "appointment"

    def get_queryset(self):
        return self.business.appointments.select_related("customer", "service")


class AppointmentCreateView(BusinessRequiredMixin, View):
    def get(self, request):
        initial = {}
        customer_id = request.GET.get("customer")
        if customer_id:
            initial["customer"] = customer_id
        form = AppointmentForm(business=self.business, initial=initial)
        return render(
            request,
            "scheduler/appointments/form.html",
            {"form": form, "title": "New appointment", "appointment": None},
        )

    def post(self, request):
        form = AppointmentForm(request.POST, business=self.business)
        if form.is_valid():
            appointment = form.save()
            messages.success(request, "Appointment scheduled.")
            return redirect(appointment)
        return render(
            request,
            "scheduler/appointments/form.html",
            {"form": form, "title": "New appointment", "appointment": None},
        )


class AppointmentUpdateView(BusinessRequiredMixin, View):
    def get_appointment(self, pk):
        return get_object_or_404(self.business.appointments, pk=pk)

    def get(self, request, pk):
        appointment = self.get_appointment(pk)
        form = AppointmentForm(business=self.business, instance=appointment)
        return render(
            request,
            "scheduler/appointments/form.html",
            {"form": form, "title": "Reschedule appointment", "appointment": appointment},
        )

    def post(self, request, pk):
        appointment = self.get_appointment(pk)
        form = AppointmentForm(request.POST, business=self.business, instance=appointment)
        if form.is_valid():
            form.save()
            messages.success(request, "Appointment updated.")
            return redirect(appointment)
        return render(
            request,
            "scheduler/appointments/form.html",
            {"form": form, "title": "Reschedule appointment", "appointment": appointment},
        )


class AppointmentCancelView(BusinessRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(self.business.appointments, pk=pk)
        appointment.status = Appointment.STATUS_CANCELLED
        appointment.save()
        messages.success(request, "Appointment cancelled. That slot is free again.")
        return redirect("scheduler:appointment-list")


class AppointmentStatusView(BusinessRequiredMixin, View):
    def post(self, request, pk):
        appointment = get_object_or_404(self.business.appointments, pk=pk)
        status = request.POST.get("status")
        allowed = {choice[0] for choice in Appointment.STATUS_CHOICES}
        if status in allowed:
            appointment.status = status
            appointment.save()
            messages.success(request, f"Status set to {appointment.get_status_display()}.")
        return redirect(appointment)


class SlotListView(BusinessRequiredMixin, View):
    """JSON endpoint used by the appointment form to show free times only."""

    def get(self, request):
        service_id = request.GET.get("service")
        date_str = request.GET.get("date")
        appointment_id = request.GET.get("appointment")
        if not service_id or not date_str:
            return JsonResponse({"slots": [], "message": "Choose a service and date."})

        service = get_object_or_404(self.business.services, pk=service_id)
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"slots": [], "message": "Invalid date."})

        exclude = None
        if appointment_id:
            exclude = self.business.appointments.filter(pk=appointment_id).first()

        slots = get_available_slots(self.business, date, service, exclude_appointment=exclude)
        formatted = [slot.strftime("%H:%M") for slot in slots]
        message = "" if formatted else "No free slots on this day."
        return JsonResponse({"slots": formatted, "message": message})


class CalendarView(BusinessRequiredMixin, TemplateView):
    template_name = "scheduler/calendar.html"


class CalendarEventsView(BusinessRequiredMixin, View):
    def get(self, request):
        start = request.GET.get("start", "")[:10]
        end = request.GET.get("end", "")[:10]
        qs = self.business.appointments.select_related("customer", "service")
        if start:
            qs = qs.filter(date__gte=start)
        if end:
            qs = qs.filter(date__lt=end)

        colors = {
            Appointment.STATUS_PENDING: "#d97706",
            Appointment.STATUS_CONFIRMED: "#2563eb",
            Appointment.STATUS_COMPLETED: "#059669",
            Appointment.STATUS_CANCELLED: "#94a3b8",
        }
        events = []
        for item in qs:
            start_dt = datetime.combine(item.date, item.start_time).isoformat()
            end_dt = datetime.combine(item.date, item.end_time).isoformat()
            events.append(
                {
                    "id": item.pk,
                    "title": f"{item.customer.full_name} · {item.service.name}",
                    "start": start_dt,
                    "end": end_dt,
                    "url": reverse("scheduler:appointment-detail", args=[item.pk]),
                    "backgroundColor": colors.get(item.status, "#2563eb"),
                    "borderColor": colors.get(item.status, "#2563eb"),
                }
            )
        return JsonResponse(events, safe=False)


class CustomerListView(BusinessRequiredMixin, ListView):
    template_name = "scheduler/customers/list.html"
    context_object_name = "customers"
    paginate_by = 12

    def get_queryset(self):
        qs = self.business.customers.all()
        search = self.request.GET.get("q", "").strip()
        if search:
            qs = qs.filter(
                Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(email__icontains=search)
                | Q(company__icontains=search)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search"] = self.request.GET.get("q", "")
        return context


class CustomerDetailView(BusinessRequiredMixin, DetailView):
    template_name = "scheduler/customers/detail.html"
    context_object_name = "customer"

    def get_queryset(self):
        return self.business.customers.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["history"] = self.object.appointments.select_related("service")
        return context


class CustomerCreateView(BusinessRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "scheduler/customers/form.html",
            {"form": CustomerForm(), "title": "Add customer"},
        )

    def post(self, request):
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.business = self.business
            customer.save()
            messages.success(request, "Customer added.")
            return redirect(customer)
        return render(
            request,
            "scheduler/customers/form.html",
            {"form": form, "title": "Add customer"},
        )


class CustomerUpdateView(BusinessRequiredMixin, UpdateView):
    template_name = "scheduler/customers/form.html"
    form_class = CustomerForm
    context_object_name = "customer"

    def get_queryset(self):
        return self.business.customers.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit customer"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Customer updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("scheduler:customer-detail", args=[self.object.pk])


class CustomerDeleteView(BusinessRequiredMixin, DeleteView):
    template_name = "scheduler/customers/confirm_delete.html"
    context_object_name = "customer"

    def get_queryset(self):
        return self.business.customers.all()

    def get_success_url(self):
        messages.success(self.request, "Customer removed.")
        return reverse("scheduler:customer-list")


class ServiceListView(BusinessRequiredMixin, ListView):
    template_name = "scheduler/services/list.html"
    context_object_name = "services"

    def get_queryset(self):
        return self.business.services.all()


class ServiceCreateView(BusinessRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "scheduler/services/form.html",
            {"form": ServiceForm(), "title": "Add service"},
        )

    def post(self, request):
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.business = self.business
            service.save()
            messages.success(request, "Service added.")
            return redirect("scheduler:service-list")
        return render(
            request,
            "scheduler/services/form.html",
            {"form": form, "title": "Add service"},
        )


class ServiceUpdateView(BusinessRequiredMixin, UpdateView):
    template_name = "scheduler/services/form.html"
    form_class = ServiceForm

    def get_queryset(self):
        return self.business.services.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit service"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Service updated.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("scheduler:service-list")


class ServiceDeleteView(BusinessRequiredMixin, DeleteView):
    template_name = "scheduler/services/confirm_delete.html"
    context_object_name = "service"

    def get_queryset(self):
        return self.business.services.all()

    def form_valid(self, form):
        if self.object.appointments.exists():
            messages.error(
                self.request,
                "This service has appointments. Deactivate it instead of deleting.",
            )
            return redirect("scheduler:service-list")
        messages.success(self.request, "Service deleted.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("scheduler:service-list")


class BusinessSettingsView(BusinessRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "scheduler/settings/business.html",
            {"form": BusinessProfileForm(instance=self.business)},
        )

    def post(self, request):
        form = BusinessProfileForm(request.POST, instance=self.business)
        if form.is_valid():
            form.save()
            messages.success(request, "Business profile saved.")
            return redirect("scheduler:settings-business")
        return render(request, "scheduler/settings/business.html", {"form": form})


class WorkingHoursView(BusinessRequiredMixin, View):
    def get(self, request):
        formset = WorkingHoursFormSet(instance=self.business)
        return render(request, "scheduler/settings/hours.html", {"formset": formset})

    def post(self, request):
        formset = WorkingHoursFormSet(request.POST, instance=self.business)
        if formset.is_valid():
            formset.save()
            messages.success(request, "Working hours updated.")
            return redirect("scheduler:settings-hours")
        return render(request, "scheduler/settings/hours.html", {"formset": formset})


class BlockedDateListView(BusinessRequiredMixin, View):
    def get(self, request):
        return render(
            request,
            "scheduler/settings/blocked.html",
            {
                "form": BlockedDateForm(),
                "blocked_dates": self.business.blocked_dates.all(),
            },
        )

    def post(self, request):
        form = BlockedDateForm(request.POST)
        if form.is_valid():
            blocked = form.save(commit=False)
            blocked.business = self.business
            blocked.save()
            messages.success(request, "Date blocked.")
            return redirect("scheduler:settings-blocked")
        return render(
            request,
            "scheduler/settings/blocked.html",
            {"form": form, "blocked_dates": self.business.blocked_dates.all()},
        )


class BlockedDateDeleteView(BusinessRequiredMixin, View):
    def post(self, request, pk):
        blocked = get_object_or_404(self.business.blocked_dates, pk=pk)
        blocked.delete()
        messages.success(request, "Blocked date removed.")
        return redirect("scheduler:settings-blocked")
