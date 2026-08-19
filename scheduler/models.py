from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


class BusinessProfile(models.Model):
    """One workspace owned by a logged-in business owner."""

    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business",
    )
    name = models.CharField(max_length=120)
    tagline = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=40, blank=True)
    address = models.CharField(max_length=255, blank=True)
    website = models.URLField(blank=True)
    description = models.TextField(blank=True)
    slot_interval = models.PositiveIntegerField(
        default=30,
        help_text="Minutes between bookable start times (e.g. 30).",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "business profile"

    def __str__(self):
        return self.name

    def setup_defaults(self):
        """Create weekday hours and starter services for a software business."""
        if not self.working_hours.exists():
            for weekday in range(7):
                is_open = weekday < 5  # Monday–Friday
                WorkingHours.objects.create(
                    business=self,
                    weekday=weekday,
                    is_open=is_open,
                    open_time="09:00",
                    close_time="17:00",
                )

        if not self.services.exists():
            defaults = [
                ("Discovery Call", "Understand goals, timeline, and budget.", 30, 0),
                ("Website Consultation", "Scope a new site or redesign.", 45, 25000),
                ("Software Architecture Review", "Review stack, structure, and risks.", 60, 80000),
                ("UI/UX Review", "Walk through product screens and UX issues.", 45, 40000),
                ("Technical Audit", "Security, performance, and code health check.", 60, 90000),
                ("Project Kickoff", "Align team, milestones, and deliverables.", 90, 0),
                ("Sprint Planning", "Plan the next development cycle.", 60, 50000),
                ("Mentoring Session", "One-to-one technical advisory.", 45, 35000),
            ]
            for name, description, duration, price in defaults:
                Service.objects.create(
                    business=self,
                    name=name,
                    description=description,
                    duration_minutes=duration,
                    price=price,
                )


class Service(models.Model):
    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    duration_minutes = models.PositiveIntegerField(default=30)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.duration_minutes} min)"


class WorkingHours(models.Model):
    WEEKDAYS = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday"),
        (6, "Sunday"),
    ]

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="working_hours",
    )
    weekday = models.IntegerField(choices=WEEKDAYS)
    is_open = models.BooleanField(default=True)
    open_time = models.TimeField(default="09:00")
    close_time = models.TimeField(default="17:00")

    class Meta:
        ordering = ["weekday"]
        unique_together = ("business", "weekday")
        verbose_name_plural = "working hours"

    def __str__(self):
        day = self.get_weekday_display()
        if not self.is_open:
            return f"{day}: Closed"
        return f"{day}: {self.open_time.strftime('%H:%M')}–{self.close_time.strftime('%H:%M')}"


class BlockedDate(models.Model):
    """Dates the business cannot take appointments (holidays, offsites)."""

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="blocked_dates",
    )
    date = models.DateField()
    reason = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["-date"]
        unique_together = ("business", "date")

    def __str__(self):
        return f"{self.date} ({self.reason or 'Unavailable'})"


class Customer(models.Model):
    """A client of the business — not a login account."""

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="customers",
    )
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    company = models.CharField(max_length=120, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["first_name", "last_name"]
        unique_together = ("business", "email")

    def __str__(self):
        if self.company:
            return f"{self.full_name} ({self.company})"
        return self.full_name

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("scheduler:customer-detail", args=[self.pk])


class Appointment(models.Model):
    STATUS_PENDING = "pending"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    business = models.ForeignKey(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="appointments",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.PROTECT,
        related_name="appointments",
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_CONFIRMED,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["date", "start_time"]

    def __str__(self):
        return f"{self.customer} — {self.service.name} on {self.date}"

    @property
    def is_active_booking(self):
        return self.status != self.STATUS_CANCELLED

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("scheduler:appointment-detail", args=[self.pk])

    def clean(self):
        """Reject bookings that fall outside hours or collide with others."""
        from scheduler.availability import validate_appointment

        if self.business_id and self.customer_id:
            if self.customer.business_id != self.business_id:
                raise ValidationError("Customer does not belong to this business.")
        if self.business_id and self.service_id:
            if self.service.business_id != self.business_id:
                raise ValidationError("Service does not belong to this business.")
        if self.status != self.STATUS_CANCELLED:
            validate_appointment(self)

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
