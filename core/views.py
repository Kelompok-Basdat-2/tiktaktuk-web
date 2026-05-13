from datetime import date

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction

from . import auth


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _session_user(request) -> dict | None:
    """Return session user dict or None."""
    user_id = request.session.get('user_id')
    if not user_id:
        return None
    user = auth.get_user_by_id(user_id)
    if not user:
        request.session.flush()
        return None
    return user


def _redirect_dashboard(role: str):
    return redirect(f'/dashboard/{role}/')


def _clean_db_error(error: Exception) -> str:
    """Extract user-facing message from a PostgreSQL trigger/stored-proc error."""
    msg = str(error)
    for line in msg.split('\n'):
        line = line.strip()
        # PostgreSQL prepends 'ERROR:  ' — match anywhere 'Error:' appears
        if 'Error:' in line:
            idx = line.index('Error:')
            return line[idx:]
    return msg.split('\n')[0].strip()


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 1: Navbar (handled in _sidebar.html via session context)
# ═══════════════════════════════════════════════════════════════════════════════

def landing_view(request):
    user = _session_user(request)
    if user:
        role = auth.get_primary_role(user['user_id'])
        if role:
            return _redirect_dashboard(role)
    return render(request, 'core/landing.html', {})


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 2: C - Register
# ═══════════════════════════════════════════════════════════════════════════════

def register_view(request):
    if request.method == 'POST':
        role = (request.POST.get('role') or '').strip()
        username = (request.POST.get('username') or '').strip()
        password = (request.POST.get('password') or '')
        password2 = (request.POST.get('password2') or '')
        fullname = (request.POST.get('fullname') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()

        # Validate role
        if role not in ('admin', 'organizer', 'customer'):
            messages.error(request, 'Pilih peran (role) terlebih dahulu.')
            return render(request, 'core/register.html', {})

        # Validate username (trigger handles duplicate & special-char checks)
        if not username:
            messages.error(request, 'Username wajib diisi.')
            return render(request, 'core/register.html', {})

        # Validate password
        if len(password) < 8:
            messages.error(request, 'Password minimal 8 karakter.')
            return render(request, 'core/register.html', {})
        if password != password2:
            messages.error(request, 'Password dan konfirmasi tidak cocok.')
            return render(request, 'core/register.html', {})

        # Map role
        role_name_map = {
            'admin': 'administrator',
            'organizer': 'organizer',
            'customer': 'customer',
        }
        db_role = role_name_map[role]

        try:
            with transaction.atomic():
                user_id = auth.create_user(username, password, db_role)
                if not user_id:
                    raise Exception('Gagal membuat akun.')

                if role == 'organizer':
                    if not fullname:
                        raise Exception('Nama lengkap wajib diisi untuk Organizer.')
                    if not email:
                        raise Exception('Email wajib diisi untuk Organizer.')
                    auth.create_organizer_profile(user_id, fullname, email, phone)
                elif role == 'customer':
                    if not fullname:
                        raise Exception('Nama lengkap wajib diisi untuk Customer.')
                    if not email:
                        raise Exception('Email wajib diisi untuk Customer.')
                    auth.create_customer_profile(user_id, fullname, phone)

            messages.success(request, 'Akun berhasil dibuat. Silakan login.')
            return redirect('core:login')
        except Exception as e:
            # Trigger/stored-procedure errors surface via _clean_db_error
            messages.error(request, _clean_db_error(e))

    return render(request, 'core/register.html', {})


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 3: R - Login & Logout
# ═══════════════════════════════════════════════════════════════════════════════

def login_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''

        user = auth.get_user_by_username(username)
        if not user:
            messages.error(request, 'Username tidak ditemukan.')
            return render(request, 'core/login.html', {})

        if not auth.verify_password(password, user['password']):
            messages.error(request, 'Password salah.')
            return render(request, 'core/login.html', {})

        # Set session
        request.session['user_id'] = user['user_id']
        request.session['username'] = user['username']

        role = auth.get_primary_role(user['user_id'])
        if role:
            return _redirect_dashboard(role)

        messages.error(request, 'Akun tidak memiliki role.')
        request.session.flush()
        return render(request, 'core/login.html', {})

    return render(request, 'core/login.html', {})


def logout_view(request):
    request.session.flush()
    return redirect('core:login')


# ═══════════════════════════════════════════════════════════════════════════════
# Feature 4: RU - Dashboard
# ═══════════════════════════════════════════════════════════════════════════════

def _dashboard_context(request, role: str, profile: dict | None) -> dict:
    """Build common dashboard template context."""
    user = _session_user(request)
    if not user:
        return {}

    display_name = ''
    if profile:
        display_name = profile.get('full_name') or profile.get('organizer_name') or user['username']

    return {
        'user': user,
        'user_name': display_name or user['username'],
        'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer'}.get(role, 'User'),
        'role': role,
        'profile': profile,
    }


def dashboard_admin(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'admin':
        return _redirect_dashboard(role) if role else redirect('core:login')

    ctx = _dashboard_context(request, 'admin', None)
    ctx['active'] = 'dashboard'
    return render(request, 'core/dashboard_admin.html', ctx)


def dashboard_organizer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'organizer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    profile = auth.get_organizer_profile(user['user_id'])
    ctx = _dashboard_context(request, 'organizer', profile)
    ctx['active'] = 'dashboard'
    return render(request, 'core/dashboard_organizer.html', ctx)


def dashboard_customer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'customer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    profile = auth.get_customer_profile(user['user_id'])
    ctx = _dashboard_context(request, 'customer', profile)
    ctx['active'] = 'dashboard'
    return render(request, 'core/dashboard_customer.html', ctx)


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
def venue_admin(request):
    """Admin venue management - frontend only."""
    return render(request, 'core/venue_admin.html', {})


def venue_organizer(request):
    """Organizer venue management - frontend only."""
    return render(request, 'core/venue_organizer.html', {})


def venue_customer(request):
    """Customer venue directory - frontend only."""
    return render(request, 'core/venue_customer.html', {})


def event_admin(request):
    """Admin event management - frontend only."""
    return render(request, 'core/event_admin.html', {})


def event_organizer(request):
    """Organizer event management - frontend only."""
    return render(request, 'core/event_organizer.html', {})


def event_customer(request):
    """Customer event directory - frontend only."""
    return render(request, 'core/event_customer.html', {})


def profile_customer(request):
    """Customer profile page - frontend only."""
    return render(request, 'core/profile_customer.html', {})


def profile_organizer(request):
    """Organizer profile page - frontend only."""
    return render(request, 'core/profile_organizer.html', {})


def profile_admin(request):
    """Admin profile page - frontend only."""
    return render(request, 'core/profile_admin.html', {})


# =============================================================================
# Features 9-10: Artist Management
# =============================================================================

artists = [
    {"id": "ART001", "name": "Fourtwnty", "genre": "Indie Folk", "on_event": True},
    {"id": "ART002", "name": "Hindia", "genre": "Indie Pop", "on_event": True},
    {"id": "ART003", "name": "Tulus", "genre": "Pop", "on_event": True},
    {"id": "ART004", "name": "Nadin Amizah", "genre": "Folk", "on_event": True},
    {"id": "ART005", "name": "Pamungkas", "genre": "Singer-Songwriter", "on_event": True},
    {"id": "ART006", "name": "Raisa", "genre": "R&B / Pop", "on_event": False},
    {"id": "ART007", "name": "Isyana Sarasvati", "genre": "Pop", "on_event": True},
    {"id": "ART008", "name": "Ardhito Pramono", "genre": "Jazz / Pop", "on_event": False},
]


def artist_list(request):
    """Fitur 9/10 - R Artist list (admin with actions, customer read-only)."""
    role = (request.GET.get('role') or 'customer').strip().lower()
    if role not in {'admin', 'organizer', 'customer'}:
        role = 'customer'

    search_query = (request.GET.get('search') or '').strip().lower()
    filtered_artists = [a for a in artists if not search_query or search_query in a['name'].lower() or search_query in (a.get('genre') or '').lower()]

    total_artists = len(artists)
    total_genres = len(set(a.get('genre') for a in artists if a.get('genre')))
    total_event_artists = sum(1 for a in artists if a.get('on_event'))

    return render(request, 'artist/artist_list.html', {
        'role': role,
        'artists': filtered_artists,
        'artist_found': len(filtered_artists),
        'search_query': search_query,
        'total_artists': total_artists,
        'total_genres': total_genres,
        'total_event_artists': total_event_artists,
    })


def artist_read(request):
    """Fitur 10 - R Artist (customer/organizer/admin, tanpa action button)."""
    return render(request, 'artist/artist_read.html')


def artist_create(request):
    """Fitur 9 - C Artist (admin only)."""
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        genre = request.POST.get('genre', '').strip()
        if name:
            new_id = f"ART{len(artists) + 1:03d}"
            artists.append({'id': new_id, 'name': name, 'genre': genre, 'on_event': False})
            messages.success(request, f"Artist '{name}' berhasil ditambahkan.")
            return redirect('artist_list')
        else:
            messages.error(request, "Nama artist wajib diisi.")
    return render(request, 'artist/artist_create.html', {'form_data': {}})


def artist_update(request, id):
    """Fitur 10 - U Artist (admin only)."""
    artist = next((a for a in artists if a['id'] == id), None)
    if not artist:
        messages.error(request, "Artist tidak ditemukan.")
        return redirect('artist_list')
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        genre = request.POST.get('genre', '').strip()
        if name:
            artist['name'] = name
            artist['genre'] = genre
            messages.success(request, f"Artist '{name}' berhasil diperbarui.")
            return redirect('artist_list')
        else:
            messages.error(request, "Nama artist wajib diisi.")
    return render(request, 'artist/artist_update.html', {'artist': artist})


def artist_delete(request, id):
    """Fitur 10 - D Artist (admin only)."""
    artist = next((a for a in artists if a['id'] == id), None)
    if not artist:
        messages.error(request, "Artist tidak ditemukan.")
        return redirect('artist_list')
    if request.method == 'POST':
        artists.remove(artist)
        messages.success(request, f"Artist '{artist['name']}' berhasil dihapus.")
        return redirect('artist_list')
    return render(request, 'artist/artist_delete.html', {'artist': artist})


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

    return render(request, 'core/checkout.html', {
        'event': event,
        'ticket_categories': ticket_categories,
        'seating': seating,
    })


def ticket_category_list(request):
    """
    Fitur 11/12 - CUD + R Ticket Category
    Tampilan ini: sidebar admin, dengan tombol tambah + modal CUD
    URL: /ticket-categories/
    """
    return render(request, 'ticket_category/ticket_category_list.html')

def ticket_category_list_customer(request):
    """
    Fitur 12 - R Ticket Category
    Tampilan untuk Customer/Guest - read only, tanpa tombol aksi
    URL: /ticket-categories/customer/
    """
    return render(request, 'ticket_category/ticket_category_list_customer.html')

# =============================================================================
# Features 18-20: Ticket Management
# =============================================================================

def tickets_admin(request):
    """Admin ticket list page - all tickets system-wide."""
    return render(request, 'core/tickets_admin.html', {})


def tickets_organizer(request):
    """Organizer ticket list page - only their events."""
    return render(request, 'core/tickets_organizer.html', {})


def my_tickets(request):
    """Customer ticket list page."""
    return render(request, 'core/my_tickets.html', {})


def ticket_create_admin(request):
    """Create ticket - Admin only."""
    return render(request, 'core/tickets_admin.html', {})


def ticket_create_organizer(request):
    """Create ticket - Organizer only."""
    return render(request, 'core/tickets_organizer.html', {})


def ticket_update(request, ticket_id):
    """Update ticket - Admin, Organizer (filtered by backend)."""
    return render(request, 'core/tickets_admin.html', {})


def ticket_delete(request, ticket_id):
    """Delete ticket - Admin, Organizer (filtered by backend)."""
    return render(request, 'core/tickets_admin.html', {})


# =============================================================================
# Features 21-22: Seat Management
# =============================================================================

def seats(request):
    """Seat list page - unified, role determined by sidebar."""
    return render(request, 'core/seats.html', {})


def seats_admin(request):
    """Seat list page - Admin view (all venues)."""
    return render(request, 'core/seats_admin.html', {})


def seats_organizer(request):
    """Seat list page - Organizer view (their venues only)."""
    return render(request, 'core/seats_organizer.html', {})


def seat_create(request):
    """Create seat - Admin, Organizer (filtered by backend)."""
    return render(request, 'core/seats.html', {})


def seat_update(request, seat_id):
    """Update seat - Admin, Organizer (filtered by backend)."""
    return render(request, 'core/seats.html', {})


def seat_delete(request, seat_id):
    """Delete seat - Admin, Organizer (filtered by backend)."""
    return render(request, 'core/seats.html', {})
