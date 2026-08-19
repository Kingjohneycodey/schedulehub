# ScheduleHub

Personal scheduling web application for a business. Built for SEN 310 with
Python and Django.

The **product** is ScheduleHub. Anyone who registers creates their own
workspace under their own business name. Clients do **not** create accounts
or book themselves — only the owner schedules appointments.

## What it does

- Owner register / login / logout
- Dashboard with today’s and upcoming appointments
- Customer records (name, company, history)
- Services with duration and price
- Working hours and blocked dates
- Appointment create / reschedule / cancel / status
- Availability engine that hides taken slots and blocks double-booking
- Calendar (day / week / month) with FullCalendar.js

## Run locally

```bash
cd sen310
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Open http://127.0.0.1:8000/

`seed_demo` loads one **sample** workspace so you can click around:

- Username: `apex`
- Password: `sen310demo`
- Business name: Apex Digital (example software agency)

Or register with your own business name. That creates a separate workspace
with Mon–Fri 09:00–17:00 hours and starter services.

## How booking is protected

When an appointment is created, Django checks:

1. The business is open that weekday
2. The date is not blocked
3. The service duration fits inside working hours
4. The slot does not overlap another non-cancelled appointment

Taken times are not shown on the form. The same checks run again on save.

## Project layout

```
schedulehub/     Django project settings and URLs
accounts/        Owner register, login, logout
scheduler/       Models, availability, dashboard, CRUD, calendar
templates/       Server-rendered HTML
static/          CSS and vanilla JavaScript
```
