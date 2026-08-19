# ScheduleHub

A personal scheduling web application for managing business appointments, clients, and services. Built with Python and Django.

---

## Overview

ScheduleHub is an internal scheduling tool for business owners. You log in, manage your clients as records, and create appointments yourself. Clients do not sign up or book themselves.

**Key features:**

- Owner registration, login, and logout
- Dashboard with statistics, charts, and today's schedule
- Customer management (add, edit, delete, view history)
- Service management with duration and pricing
- Appointment scheduling with automatic availability checking
- Double-booking prevention
- Working hours configuration per weekday
- Blocked dates (holidays, unavailable days)
- Calendar view (day, week, month) with FullCalendar.js
- Appointment status management (pending, confirmed, completed, cancelled)
- Search and filter with real-time debounced input

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.9+, Django 4.2 |
| Database | SQLite (development), can swap to PostgreSQL |
| Frontend | HTML, CSS, Bootstrap 5, Vanilla JavaScript |
| Charts | Chart.js |
| Calendar | FullCalendar.js |
| Production Server | Gunicorn |
| Reverse Proxy | Nginx |
| Process Manager | Systemd |

---

## Project Structure

```
schedulehub/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── DEPLOY.md
│
├── schedulehub/          # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── accounts/             # Authentication app
│   ├── forms.py          # Login & registration forms
│   ├── views.py          # Login, logout, register views
│   └── urls.py
│
├── scheduler/            # Core scheduling app
│   ├── models.py         # BusinessProfile, Service, Customer, Appointment, WorkingHours, BlockedDate
│   ├── views.py          # Dashboard, CRUD, calendar, slots API
│   ├── forms.py          # All model forms with Bootstrap styling
│   ├── availability.py   # Slot calculation & conflict validation
│   ├── admin.py          # Django admin configuration
│   ├── context_processors.py
│   ├── urls.py
│   └── management/
│       └── commands/
│           └── seed_demo.py   # Load sample data
│
├── templates/            # HTML templates
│   ├── base.html         # Main layout with sidebar
│   ├── includes/
│   │   └── pagination.html
│   ├── accounts/
│   │   ├── auth_base.html
│   │   ├── landing.html
│   │   ├── login.html
│   │   └── register.html
│   └── scheduler/
│       ├── dashboard.html
│       ├── calendar.html
│       ├── appointments/
│       │   ├── list.html
│       │   ├── form.html
│       │   └── detail.html
│       ├── customers/
│       │   ├── list.html
│       │   ├── form.html
│       │   ├── detail.html
│       │   └── confirm_delete.html
│       ├── services/
│       │   ├── list.html
│       │   ├── form.html
│       │   └── confirm_delete.html
│       └── settings/
│           ├── business.html
│           ├── hours.html
│           └── blocked.html
│
└── static/
    ├── css/
    │   └── app.css       # Custom styles
    └── js/
        ├── app.js        # Alerts, auto-submit filters
        ├── booking.js    # Available slots loader
        └── calendar.js   # FullCalendar initialization
```

---

## Database Models

```
User (Django built-in)
 └── BusinessProfile (one-to-one)
       ├── Service (many)
       ├── WorkingHours (7 days)
       ├── BlockedDate (many)
       ├── Customer (many)
       └── Appointment (many)
             ├── → Customer (FK)
             └── → Service (FK)
```

**Appointment fields:** business, customer, service, date, start_time, end_time, status, notes, created_at, updated_at

**Status options:** pending, confirmed, completed, cancelled

---

## How Scheduling Works

When an appointment is created, Django validates:

1. **Is the business open?** — checks WorkingHours for that weekday
2. **Is the date blocked?** — checks BlockedDate entries
3. **Does it fit inside working hours?** — start_time ≥ open_time, end_time ≤ close_time
4. **Is there a conflict?** — checks for overlapping non-cancelled appointments

The appointment form only shows **available time slots** based on these rules. Even if someone bypasses the form, the model's `clean()` method rejects invalid bookings on save.

**Slot calculation:**
- Start from opening time
- Step forward by the business's `slot_interval` (default 30 min)
- For each potential start, check if start + service duration fits without overlapping existing bookings
- Past times on today's date are excluded
- Cancelled appointments do not occupy slots

---

## Local Development Setup

### 1. Clone the repository

```bash
git clone git@github.com:Kingjohneycodey/schedulehub.git
cd schedulehub
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run migrations

```bash
python manage.py migrate
```

### 5. Load demo data (optional)

```bash
python manage.py seed_demo
```

This creates a sample workspace:
- **Email:** john@apexdigital.dev
- **Password:** sen310demo
- 4 sample customers
- 8 services (Discovery Call, Website Consultation, etc.)
- 5 sample appointments
- Mon–Fri 09:00–17:00 working hours

### 6. Run the development server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/

### 7. Or register a fresh account

Visit http://127.0.0.1:8000/register/ and enter your own business name. Default working hours and services are created automatically.

---

## Running Tests

```bash
source venv/bin/activate
python manage.py test scheduler
```

Tests cover:
- Taken slots are excluded from availability
- Double-booking is rejected with a ValidationError

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DJANGO_SECRET_KEY` | insecure dev key | Production secret key |
| `DJANGO_DEBUG` | `True` | Set to `False` in production |
| `DJANGO_ALLOWED_HOSTS` | `127.0.0.1,localhost,testserver` | Comma-separated hostnames |

See `.env.example` for reference.

---

## Production Deployment

See **[DEPLOY.md](DEPLOY.md)** for the full step-by-step VPS deployment guide (Gunicorn + Nginx + SSL + GitHub Actions).

---

## Available URLs

| URL | Description |
|-----|-------------|
| `/` | Landing page |
| `/login/` | Owner login |
| `/register/` | Owner registration |
| `/logout/` | Logout (POST) |
| `/dashboard/` | Main dashboard with stats and charts |
| `/appointments/` | Appointment list with search/filter |
| `/appointments/new/` | Create appointment |
| `/appointments/<id>/` | Appointment detail |
| `/appointments/<id>/edit/` | Reschedule appointment |
| `/appointments/<id>/cancel/` | Cancel appointment (POST) |
| `/appointments/<id>/status/` | Update status (POST) |
| `/appointments/slots/` | JSON API for available times |
| `/calendar/` | Calendar view |
| `/calendar/events/` | JSON API for FullCalendar |
| `/customers/` | Customer list |
| `/customers/new/` | Add customer |
| `/customers/<id>/` | Customer detail + history |
| `/customers/<id>/edit/` | Edit customer |
| `/customers/<id>/delete/` | Delete customer |
| `/services/` | Service list |
| `/services/new/` | Add service |
| `/services/<id>/edit/` | Edit service |
| `/services/<id>/delete/` | Delete service |
| `/settings/` | Business profile settings |
| `/settings/hours/` | Working hours configuration |
| `/settings/blocked/` | Blocked dates management |
| `/admin/` | Django admin panel |

---

## License

This project was built for SEN 310 coursework.

© 2026 [Ahiakwo John](https://ahiakwojohn.com)
