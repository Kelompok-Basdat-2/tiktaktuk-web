from datetime import date

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


def order(request):
    """Order list page - frontend only."""
    role = (request.GET.get('role') or 'customer').strip().lower()
    if role not in {'admin', 'organizer', 'customer', 'guest'}:
        role = 'customer'

    orders = {
        'customer': [
            {
                'id': 'ord_001',
                'customer': 'You',
                'date': '2024-04-10 14:32',
                'status': 'Lunas',
                'status_key': 'paid',
                'total': 'Rp 1,200,000',
            },
            {
                'id': 'ord_002',
                'customer': 'You',
                'date': '2024-04-11 09:15',
                'status': 'Lunas',
                'status_key': 'paid',
                'total': 'Rp 150,000',
            },
        ],
        'organizer': [
            {
                'id': 'ord_001',
                'customer': 'Budi Santoso',
                'date': '2024-04-10 14:32',
                'status': 'Lunas',
                'status_key': 'paid',
                'total': 'Rp 1,200,000',
            },
            {
                'id': 'ord_002',
                'customer': 'Budi Santoso',
                'date': '2024-04-11 09:15',
                'status': 'Lunas',
                'status_key': 'paid',
                'total': 'Rp 150,000',
            },
            {
                'id': 'ord_003',
                'customer': 'Siti Rahayu',
                'date': '2024-04-12 18:44',
                'status': 'Pending',
                'status_key': 'pending',
                'total': 'Rp 1,500,000',
            },
        ],
        'admin': [
            {
                'id': 'ord_001',
                'customer': 'Budi Santoso',
                'date': '2024-04-10 14:32',
                'status': 'Lunas',
                'status_key': 'paid',
                'total': 'Rp 1,200,000',
            },
            {
                'id': 'ord_002',
                'customer': 'Budi Santoso',
                'date': '2024-04-11 09:15',
                'status': 'Lunas',
                'status_key': 'paid',
                'total': 'Rp 150,000',
            },
            {
                'id': 'ord_003',
                'customer': 'Siti Rahayu',
                'date': '2024-04-12 18:44',
                'status': 'Pending',
                'status_key': 'pending',
                'total': 'Rp 1,500,000',
            },
            {
                'id': 'ord_004',
                'customer': 'Siti Rahayu',
                'date': '2024-04-13 11:00',
                'status': 'Dibatalkan',
                'status_key': 'cancelled',
                'total': 'Rp 700,000',
            },
        ],
        'guest': [],
    }

    current_orders = orders.get(role, orders['customer'])
    total_order = len(current_orders)
    paid_count = sum(1 for order_item in current_orders if order_item['status_key'] == 'paid')
    pending_count = sum(1 for order_item in current_orders if order_item['status_key'] == 'pending')
    total_revenue = 'Rp 1,350,000' if role in {'admin', 'organizer'} else None

    return render(
        request,
        'core/order.html',
        {
            'role': role,
            'is_admin': role == 'admin',
            'is_organizer': role == 'organizer',
            'is_customer': role == 'customer',
            'page_title': 'Daftar Order',
            'page_subtitle': {
                'customer': 'Riwayat pembelian tiket Anda',
                'organizer': 'Order dari event yang Anda selenggarakan',
                'admin': 'Semua order yang terdaftar di sistem',
                'guest': 'Data order frontend testing',
            }.get(role, 'Riwayat pembelian tiket Anda'),
            'stats': {
                'total_order': total_order,
                'paid_count': paid_count,
                'pending_count': pending_count,
                'total_revenue': total_revenue,
            },
            'orders': current_orders,
            'selected_status': 'all',
        },
    )


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


def checkout(request):
    """Checkout page - order creation/ticket purchase - frontend only."""
    # Mock event data
    event = {
        'id': 'evt_001',
        'name': 'Konser Melodi Senja',
        'category': 'Musik',
        'date': '25 Mei 2026',
        'time': '19:00',
        'venue': 'Jakarta Convention Center',
        'image': '#',
    }

    # Mock ticket categories
    ticket_categories = [
        {'id': 'cat_1', 'name': 'VVIP', 'price': 1500000, 'available': 50},
        {'id': 'cat_2', 'name': 'VIP', 'price': 750000, 'available': 80},
        {'id': 'cat_3', 'name': 'Category 1', 'price': 450000, 'available': 300},
        {'id': 'cat_4', 'name': 'Category 2', 'price': 250000, 'available': 500},
    ]

    # Mock seating
    seating = {
        'rows': ['A1', 'A2', 'A3', 'A4', 'B1', 'B2', 'B3', 'B4', 'C1', 'C2', 'C3', 'C4'],
    }

    return render(
        request,
        'core/checkout.html',
        {
            'event': event,
            'ticket_categories': ticket_categories,
            'seating': seating,
        },
    )
