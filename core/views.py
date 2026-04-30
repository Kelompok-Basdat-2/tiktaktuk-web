from datetime import date, timedelta

from django.shortcuts import render, redirect


def landing_view(request):
    """Landing page - frontend only."""
    return render(request, 'core/landing.html', {})


def login_view(request):
    """Login page - frontend only, no backend logic."""
    return render(request, 'core/login.html', {})


def logout_view(request):
    """Logout - redirect to login page."""
    return redirect('/login/')


def register_view(request):
    """Registration page - frontend only, no backend logic."""
    return render(request, 'core/register.html', {})


def dashboard_admin(request):
    """Admin dashboard - frontend only."""
    return render(request, 'core/dashboard_admin.html', {})


def dashboard_organizer(request):
    """Organizer dashboard - frontend only."""
    return render(request, 'core/dashboard_organizer.html', {})


def dashboard_customer(request):
    """Customer dashboard - frontend only."""
    return render(request, 'core/dashboard_customer.html', {})


def promotion(request):
    """Promotion list page - frontend only."""
    role = (request.GET.get('role') or 'guest').strip().lower()
    if role not in {'admin', 'organizer', 'customer', 'guest'}:
        role = 'guest'

    today = date.today()
    promotions = [
        {
            'id': 'PR001',
            'promo_code': 'TIKTAK20',
            'discount_type': 'percentage',
            'discount_type_label': 'Persentase',
            'discount_value_display': '20%',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'usage': '45 / 100',
            'status': 'active',
            'status_label': 'Aktif',
        },
        {
            'id': 'PR002',
            'promo_code': 'HEMAT50K',
            'discount_type': 'nominal',
            'discount_type_label': 'Nominal',
            'discount_value_display': 'Rp 50,000',
            'start_date': '2024-01-01',
            'end_date': '2024-12-31',
            'usage': '12 / 50',
            'status': 'inactive',
            'status_label': 'Nominal',
        },
        {
            'id': 'PR003',
            'promo_code': 'NEWUSER30',
            'discount_type': 'percentage',
            'discount_type_label': 'Persentase',
            'discount_value_display': '30%',
            'start_date': '2024-03-01',
            'end_date': '2024-06-30',
            'usage': '87 / 200',
            'status': 'active',
            'status_label': 'Aktif',
        },
    ]

    stats = {
        'total_promo': len(promotions),
        'total_usage': 144,
        'percentage_type': sum(1 for promotion in promotions if promotion['discount_type'] == 'percentage'),
    }

    return render(
        request,
        'core/promotion.html',
        {
            'role': role,
            'is_admin': role == 'admin',
            'page_title': 'Manajemen Promosi',
            'page_subtitle': 'Kelola kode promo dan kampanye diskon',
            'promotions': promotions,
            'stats': stats,
        },
    )


def profile_customer(request):
    """Customer profile page - frontend only."""
    return render(request, 'core/profile_customer.html', {})


def profile_organizer(request):
    """Organizer profile page - frontend only."""
    return render(request, 'core/profile_organizer.html', {})


def profile_admin(request):
    """Admin profile page - frontend only."""
    return render(request, 'core/profile_admin.html', {})
