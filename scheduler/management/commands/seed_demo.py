from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from scheduler.models import Appointment, BusinessProfile, Customer


class Command(BaseCommand):
    help = "Create a demo Apex Digital workspace with sample appointments."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            username="john@apexdigital.dev",
            defaults={
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@apexdigital.dev",
            },
        )
        user.set_password("sen310demo")
        user.save()

        business, _ = BusinessProfile.objects.get_or_create(
            owner=user,
            defaults={
                "name": "Apex Digital",
                "tagline": "Custom software, websites, and product consulting",
                "email": "hello@apexdigital.dev",
                "phone": "+234 801 234 5678",
                "address": "12 Adeola Odeku Street, Victoria Island, Lagos",
                "website": "https://apexdigital.dev",
                "description": (
                    "Apex Digital is a software agency that designs and builds "
                    "web products, internal tools, and digital platforms."
                ),
            },
        )
        business.setup_defaults()

        sample_customers = [
            ("Chidi", "Nwosu", "chidi@brightpath.ng", "BrightPath Schools", "+234 802 111 2233"),
            ("Amaka", "Eze", "amaka@lumenpay.co", "LumenPay", "+234 803 444 5566"),
            ("Tunde", "Balogun", "tunde@northgate.ng", "Northgate Logistics", "+234 805 777 8899"),
            ("Sarah", "Adeyemi", "sarah@kairoshq.com", "Kairos HQ", "+234 809 321 6540"),
        ]
        customers = []
        for first, last, email, company, phone in sample_customers:
            customer, _ = Customer.objects.get_or_create(
                business=business,
                email=email,
                defaults={
                    "first_name": first,
                    "last_name": last,
                    "company": company,
                    "phone": phone,
                },
            )
            customers.append(customer)

        def next_open(day):
            while day.weekday() >= 5:
                day += timedelta(days=1)
            return day

        services = list(business.services.filter(is_active=True).order_by("id"))
        today = next_open(timezone.localdate())
        if not business.appointments.exists() and services:
            plan = [
                (customers[0], services[0], today, "09:00", "09:30", Appointment.STATUS_CONFIRMED),
                (customers[1], services[2], today, "10:30", "11:30", Appointment.STATUS_PENDING),
                (customers[2], services[1], today, "13:00", "13:45", Appointment.STATUS_CONFIRMED),
                (customers[3], services[5], next_open(today + timedelta(days=1)), "11:00", "12:30", Appointment.STATUS_CONFIRMED),
                (customers[1], services[6], next_open(today + timedelta(days=2)), "14:00", "15:00", Appointment.STATUS_PENDING),
            ]
            for customer, service, date, start, end, status in plan:
                Appointment.objects.create(
                    business=business,
                    customer=customer,
                    service=service,
                    date=date,
                    start_time=start,
                    end_time=end,
                    status=status,
                    notes="Seeded demo appointment.",
                )

        self.stdout.write(self.style.SUCCESS("Demo workspace ready."))
        self.stdout.write("  Email: john@apexdigital.dev")
        self.stdout.write("  Password: sen310demo")
