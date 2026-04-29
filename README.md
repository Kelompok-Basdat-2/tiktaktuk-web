# TikTakTuk

TikTakTuk is a role-based web platform built with Django 6. The system serves three user roles:

- **Admin** — manages platform-wide settings and users
- **Organizer** — creates and manages events/activities
- **Customer** — browses and participates in events

## Quick Start

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

## Tech Stack

- Django 6.0.4
- Python virtual environment
- SQLite (default)

## Project Structure

```
tiktaktuk-web/
├── manage.py
├── requirements.txt
├── core/                  # Main app (views, templates, urls)
├── static/               # CSS and static assets
├── templates/            # HTML templates
└── tiktaktuk/            # Django project settings
```