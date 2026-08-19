"""
Core scheduling rules for ScheduleHub.

When the owner creates or reschedules an appointment, Django checks:
1. The business is open on that weekday
2. The date is not blocked
3. The service duration fits inside working hours
4. The time does not overlap another non-cancelled appointment
"""
from datetime import datetime, timedelta

from django.core.exceptions import ValidationError
from django.utils import timezone


def combine(date, time):
    return datetime.combine(date, time)


def overlapping_qs(appointment):
    """Other bookings that share time with this one on the same day."""
    from scheduler.models import Appointment

    qs = Appointment.objects.filter(
        business=appointment.business,
        date=appointment.date,
    ).exclude(status=Appointment.STATUS_CANCELLED)

    if appointment.pk:
        qs = qs.exclude(pk=appointment.pk)

    return qs.filter(
        start_time__lt=appointment.end_time,
        end_time__gt=appointment.start_time,
    )


def get_hours_for(business, date):
    return business.working_hours.filter(weekday=date.weekday()).first()


def validate_appointment(appointment):
    if not appointment.date or not appointment.start_time or not appointment.end_time:
        return

    if appointment.end_time <= appointment.start_time:
        raise ValidationError("End time must be after start time.")

    hours = get_hours_for(appointment.business, appointment.date)
    if not hours or not hours.is_open:
        raise ValidationError("The business is closed on this day.")

    if appointment.start_time < hours.open_time or appointment.end_time > hours.close_time:
        raise ValidationError("This time is outside working hours.")

    if appointment.business.blocked_dates.filter(date=appointment.date).exists():
        raise ValidationError("This date is blocked and cannot be booked.")

    if overlapping_qs(appointment).exists():
        raise ValidationError("That time overlaps another appointment.")


def get_available_slots(business, date, service, exclude_appointment=None):
    """
    Return start times the owner can still use on `date` for `service`.
    Cancelled appointments do not occupy a slot.
    """
    from scheduler.models import Appointment

    hours = get_hours_for(business, date)
    if not hours or not hours.is_open:
        return []

    if business.blocked_dates.filter(date=date).exists():
        return []

    if date < timezone.localdate():
        return []

    duration = timedelta(minutes=service.duration_minutes)
    step = timedelta(minutes=business.slot_interval or 30)
    open_dt = combine(date, hours.open_time)
    close_dt = combine(date, hours.close_time)

    booked = Appointment.objects.filter(
        business=business,
        date=date,
    ).exclude(status=Appointment.STATUS_CANCELLED)
    if exclude_appointment:
        booked = booked.exclude(pk=exclude_appointment.pk)

    busy = [
        (combine(date, item.start_time), combine(date, item.end_time))
        for item in booked
    ]

    now = timezone.localtime().replace(tzinfo=None)
    slots = []
    cursor = open_dt
    while cursor + duration <= close_dt:
        end = cursor + duration
        if date == now.date() and cursor < now:
            cursor += step
            continue
        collision = any(cursor < busy_end and end > busy_start for busy_start, busy_end in busy)
        if not collision:
            slots.append(cursor.time())
        cursor += step
    return slots
