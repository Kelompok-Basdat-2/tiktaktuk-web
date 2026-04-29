# TikTakTuk Web

Django 6.0.4 — Python venv
**Status:** DUMMY/PLACEHOLDER — UI and templates only, no functional backend yet.

**Database:** Raw SQL only. NO Django ORM. All queries in `queries.sql`.

**Models:** DO NOT use Django models.py. All data operations via raw SQL only.

---

## Aesthetic

**Principles:** Minimal. Sharp. Functional.

No clutter. No decoration for its own sake. Every pixel earns its place.

**Surfaces:**
- Cards float on `#F8F9FA` with soft shadow (`0 2px 8px rgba(0,0,0,0.04), 0 4px 16px rgba(0,0,0,0.06)`)
- `border-radius: 12px` — consistent across all elements
- Generous whitespace; content breathes

**Colors:**
- `#FFFFFF` — surface
- `#F8F9FA` — background
- `#FF6B4A` — accent (CTAs, active states, the punch)
- `#212529` — primary text (near-black charcoal)
- `#6C757D` — secondary text (cool gray)

**Type:** Poppins (Google Fonts). 600/700 for headings, 400/500 for body. Strong hierarchy, geometric clarity.

**Interactions:**
- CUD actions (Create, Update, Delete) — dialogs and modal variants. No page reloads for mutations.
- Login/Register: dedicated pages
- All other interactions: inline, contextual, immediate feedback

**Layout:**
- Sidebar: 260px fixed, left
- Header: 64px sticky, top
- Content: modular grid of cards and widgets

---

## Structure

```
tiktaktuk-web/
├── manage.py
├── requirements.txt
├── static/css/          # Design system
├── templates/           # HTML partials
├── core/                # Main app
└── tiktaktuk/           # Project settings
```

---

## Run

```bash
./venv/Scripts/python manage.py runserver
./venv/Scripts/python manage.py makemigrations
./venv/Scripts/python manage.py migrate
```