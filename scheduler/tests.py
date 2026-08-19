from datetime import time, timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from scheduler.availability import get_available_slots
from scheduler.models import Appointment, BusinessProfile, Customer


class AvailabilityTests(TestCase):
    def setUp(self):
        user = User.objects.create_user("owner", password="pass12345")
        self.business = BusinessProfile.objects.create(owner=user, name="Test Studio")
        self.business.setup_defaults()
        self.service = self.business.services.get(name="Discovery Call")
        self.customer = Customer.objects.create(
            business=self.business,
            first_name="Chidi",
            last_name="Nwosu",
            email="chidi@example.com",
        )
        self.day = timezone.localdate() + timedelta(days=1)
        while self.day.weekday() >= 5:
            self.day += timedelta(days=1)

    def test_taken_slot_is_not_offered(self):
        Appointment.objects.create(
            business=self.business,
            customer=self.customer,
            service=self.service,
            date=self.day,
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        slots = get_available_slots(self.business, self.day, self.service)
        self.assertNotIn(time(10, 0), slots)
        self.assertIn(time(10, 30), slots)

    def test_double_booking_is_rejected(self):
        Appointment.objects.create(
            business=self.business,
            customer=self.customer,
            service=self.service,
            date=self.day,
            start_time=time(11, 0),
            end_time=time(11, 30),
        )
        clash = Appointment(
            business=self.business,
            customer=self.customer,
            service=self.service,
            date=self.day,
            start_time=time(11, 0),
            end_time=time(11, 30),
        )
        with self.assertRaises(ValidationError):
            clash.save()
