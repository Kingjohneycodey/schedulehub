from datetime import datetime, timedelta

from django import forms
from django.forms import inlineformset_factory

from .availability import get_available_slots
from .models import Appointment, BlockedDate, BusinessProfile, Customer, Service, WorkingHours


def add_bootstrap(form):
    for field in form.fields.values():
        css = field.widget.attrs.get("class", "")
        if isinstance(field.widget, forms.CheckboxInput):
            field.widget.attrs["class"] = f"{css} form-check-input".strip()
        elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
            field.widget.attrs["class"] = f"{css} form-select".strip()
        elif isinstance(field.widget, forms.Textarea):
            field.widget.attrs["class"] = f"{css} form-control".strip()
            field.widget.attrs.setdefault("rows", 3)
        else:
            field.widget.attrs["class"] = f"{css} form-control".strip()


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = (
            "name",
            "tagline",
            "email",
            "phone",
            "address",
            "website",
            "description",
            "slot_interval",
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)
        self.fields["slot_interval"].help_text = "Minutes between possible start times."


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ("name", "description", "duration_minutes", "price", "is_active")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ("first_name", "last_name", "email", "phone", "company", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)


class WorkingHoursForm(forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ("weekday", "is_open", "open_time", "close_time")
        widgets = {
            "weekday": forms.HiddenInput(),
            "open_time": forms.TimeInput(attrs={"type": "time"}),
            "close_time": forms.TimeInput(attrs={"type": "time"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)


WorkingHoursFormSet = inlineformset_factory(
    BusinessProfile,
    WorkingHours,
    form=WorkingHoursForm,
    extra=0,
    can_delete=False,
    max_num=7,
)


class BlockedDateForm(forms.ModelForm):
    class Meta:
        model = BlockedDate
        fields = ("date", "reason")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        add_bootstrap(self)


class AppointmentForm(forms.ModelForm):
    start_time = forms.TimeField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta:
        model = Appointment
        fields = ("customer", "service", "date", "start_time", "status", "notes")
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, business=None, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        self.business = business
        add_bootstrap(self)
        customers = Customer.objects.filter(business=business)
        services = Service.objects.filter(business=business, is_active=True)
        if instance:
            services = Service.objects.filter(business=business)
        self.fields["customer"].queryset = customers
        self.fields["service"].queryset = services
        self.fields["status"].initial = Appointment.STATUS_CONFIRMED
        if not instance:
            self.fields["date"].widget.attrs["min"] = datetime.now().date().isoformat()

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get("service")
        date = cleaned.get("date")
        start_time = cleaned.get("start_time")
        if not (service and date and start_time):
            if not start_time:
                self.add_error("start_time", "Select an available time slot.")
            return cleaned

        slots = get_available_slots(
            self.business,
            date,
            service,
            exclude_appointment=self.instance if self.instance.pk else None,
        )
        if start_time not in slots:
            raise forms.ValidationError(
                "That time is not available. Choose another slot."
            )

        end_dt = datetime.combine(date, start_time) + timedelta(minutes=service.duration_minutes)
        cleaned["end_time"] = end_dt.time()
        return cleaned

    def save(self, commit=True):
        appointment = super().save(commit=False)
        appointment.business = self.business
        appointment.end_time = self.cleaned_data["end_time"]
        if commit:
            appointment.save()
        return appointment
