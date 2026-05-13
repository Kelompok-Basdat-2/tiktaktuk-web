# TikTakTuk

TikTakTuk is a role-based event ticketing platform built with Django 6. The system serves three user roles:

- **Admin** — manages platform-wide settings, venues, events, artists, and promotions
- **Organizer** — creates and manages events/activities
- **Customer** — browses events and purchases tickets

---

## Quick Start

### Prerequisites
- Python 3.12+
- PostgreSQL (local via Docker or cloud)

### 1. Start PostgreSQL (Docker)
```bash
docker compose up -d
```
Or connect to any running PostgreSQL instance.

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your PostgreSQL connection details
```

`.env` example for local Docker:
```env
DB_NAME=tiktaktuk_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### 3. Setup Python & seed database
```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_db
```

### 4. Run
```bash
python manage.py runserver
```
Open http://localhost:8000

---

## Demo Accounts

All passwords are pre-hashed with PBKDF2-SHA256. **No password reset needed** — use these to log in immediately after seeding.

### Admin
| Username | Password |
|---|---|
| `admin_reva` | `admin123` |
| `admin_andi` | `admin123` |
| `admin_budi` | `admin123` |

### Organizer
| Username | Password |
|---|---|
| `org_soundfest` | `organizer123` |
| `org_techindo` | `organizer123` |
| `org_comedyclub` | `organizer123` |
| `org_festpro` | `organizer123` |
| `org_musicfest` | `organizer123` |

### Customer
| Username | Password |
|---|---|
| `cust_budi` | `customer123` |
| `cust_siti` | `customer123` |
| `cust_rina` | `customer123` |
| `cust_joko` | `customer123` |
| `cust_dewi` | `customer123` |
| `cust_ange` | `customer123` |
| `cust_kevin` | `customer123` |
| `cust_lina` | `customer123` |
| `cust_michael` | `customer123` |
| `cust_nadia` | `customer123` |

---

## Tech Stack

- Django 6.0.4
- PostgreSQL (via psycopg3)
- Raw SQL only — **zero Django ORM**
- `python-dotenv` for environment config
- `sqlparse` for SQL statement splitting

---

## Project Structure

```
tiktaktuk-web/
├── manage.py
├── requirements.txt
├── .env                          # PostgreSQL + Django config (gitignored)
├── .env.example                  # Template for .env
├── docker-compose.yml            # PostgreSQL 16 container
├── core/                         # Main app
│   ├── auth.py                   # Auth utilities (raw SQL, no ORM)
│   ├── views.py                  # View logic
│   ├── urls.py                   # URL routing
│   ├── templates/core/           # HTML templates
│   └── management/commands/
│       ├── seed_db.py            # Raw SQL seeder command
│       └── seed_data.sql         # Full DDL + 16 tables of dummy data
├── static/                       # CSS and static assets
└── tiktaktuk/                    # Django project settings
    └── settings.py               # PostgreSQL config via .env
```

---

## Management Commands

### `seed_db`
Seeds the database with all tables and dummy data. Idempotent — safe to re-run.

```bash
python manage.py seed_db
# => Seed complete: 48 executed, 1 skipped, 0 errors
```

---

## Architecture Notes

- **All database operations use raw SQL** via `connection.cursor()` — no Django models, no ORM
- **Sessions use signed cookies** (`SESSION_ENGINE = signed_cookies`) — no `django_session` table
- **Passwords are PBKDF2-SHA256 hashed** using Django's `make_password` (utility only, not bound to ORM)
- **Seed data is transactional** — `transaction.atomic()` ensures all-or-nothing seeding
