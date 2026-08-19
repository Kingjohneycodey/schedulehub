from django.contrib import admin

from .models import Appointment, BlockedDate, BusinessProfile, Customer, Service, WorkingHours


class WorkingHoursInline(admin.TabularInline):
    model = WorkingHours
    extra = 0


class ServiceInline(admin.TabularInline):
    model = Service
    extra = 0


@admin.register(BusinessProfile)
class BusinessProfileAdmin(admin.ModelAdmin):
    list_display = ("name", "owner", "email", "phone")
    inlines = [WorkingHoursInline, ServiceInline]


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("name", "business", "duration_minutes", "price", "is_active")
    list_filter = ("is_active", "business")


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "company", "email", "phone", "business")
    search_fields = ("first_name", "last_name", "email", "company")


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("date", "start_time", "customer", "service", "status", "business")
    list_filter = ("status", "date", "business")


@admin.register(BlockedDate)
class BlockedDateAdmin(admin.ModelAdmin):
    list_display = ("date", "reason", "business")
