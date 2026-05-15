import json
from datetime import date, timedelta

from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.utils import timezone

from . import auth
from . import tickets as tkt
from . import artists as art
from . import orders as od
from . import promotions as promo
from . import ticket_categories as tc_mod
from . import venues as vn
from . import events as ev


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
            return line[idx:].replace('Error:', 'ERROR:', 1)
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
    # Consume lingering messages before clearing session
    list(messages.get_messages(request))
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

    now = timezone.now()
    all_orders = od.get_all_orders()
    all_events = ev.get_all_events()
    all_promos = promo.get_promotions()
    venue_stats = vn.get_venue_stats()
    artist_stats = art.get_artist_stats()
    user_counts = auth.get_user_count()

    total_revenue = sum(o['total_amount'] for o in all_orders)
    pending_orders = sum(1 for o in all_orders if o['payment_status'].lower() == 'pending')
    active_promos = sum(1 for p in all_promos if p['start_date'] <= date.today() <= p['end_date'])
    recent_orders = sorted(all_orders, key=lambda o: o['order_date'], reverse=True)[:3]

    ctx = _dashboard_context(request, 'admin', None)
    ctx['active'] = 'dashboard'
    ctx.update({
        'stats': {
            'total_venues': venue_stats['total_venues'],
            'total_events': len(all_events),
            'total_users': user_counts['total'],
            'total_orders': len(all_orders),
            'total_revenue': _format_rupiah(total_revenue),
            'active_promos': active_promos,
            'total_artists': artist_stats['total_artists'],
            'pending_orders': pending_orders,
        },
        'recent_orders': recent_orders,
    })
    return render(request, 'core/dashboard_admin.html', ctx)


def dashboard_organizer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'organizer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    now = timezone.now()
    profile = auth.get_organizer_profile(user['user_id'])
    organizer_id = profile['organizer_id'] if profile else ''

    org_events = ev.get_all_events(organizer_id=organizer_id)
    org_orders = od.get_orders_by_organizer(user['user_id'])
    org_tickets = tkt.get_tickets_by_organizer(user['user_id'])
    all_promos = promo.get_promotions()
    artist_stats = art.get_artist_stats()

    revenue = sum(o['total_amount'] for o in org_orders)
    pending = sum(1 for o in org_orders if o['payment_status'].lower() == 'pending')
    active_promos = sum(1 for p in all_promos if p['start_date'] <= date.today() <= p['end_date'])
    my_venues = len({e['venue_id'] for e in org_events})
    recent_events = sorted(org_events, key=lambda e: e['event_datetime'] or '', reverse=True)[:3]

    ctx = _dashboard_context(request, 'organizer', profile)
    ctx['active'] = 'dashboard'
    ctx.update({
        'stats': {
            'my_events': len(org_events),
            'tickets_sold': len(org_tickets),
            'my_venues': my_venues,
            'revenue': _format_rupiah(revenue),
            'pending_orders': pending,
            'active_promos': active_promos,
            'total_artists': artist_stats['total_artists'],
        },
        'recent_events': recent_events,
    })
    return render(request, 'core/dashboard_organizer.html', ctx)


def dashboard_customer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'customer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    now = timezone.now()
    profile = auth.get_customer_profile(user['user_id'])
    my_tickets = tkt.get_tickets_by_customer(user['user_id'])
    my_orders = od.get_orders_by_customer(user['user_id'])
    all_events = ev.get_all_events()
    all_promos = promo.get_promotions()

    total_spent = sum(o['total_amount'] for o in my_orders)
    active_promos = sum(1 for p in all_promos if p['start_date'] <= date.today() <= p['end_date'])
    upcoming_events = [e for e in all_events if _ensure_event_datetime(e['event_datetime']) and _ensure_event_datetime(e['event_datetime']) >= now]
    next_events = sorted(upcoming_events, key=lambda e: e['event_datetime'])[:3]

    ctx = _dashboard_context(request, 'customer', profile)
    ctx['active'] = 'dashboard'
    ctx.update({
        'stats': {
            'my_tickets': len(my_tickets),
            'my_orders': len(my_orders),
            'total_spent': _format_rupiah(total_spent),
            'active_promos': active_promos,
            'upcoming_events': len(upcoming_events),
        },
        'upcoming_events_list': next_events,
    })
    return render(request, 'core/dashboard_customer.html', ctx)


def order(request):
    """Order list page."""
    user = _session_user(request)
    role = (request.GET.get('role') or 'customer').strip().lower()
    if role not in {'admin', 'organizer', 'customer', 'guest'}:
        role = 'customer'

    if request.method == 'POST':
        post_role = (request.POST.get('role') or role).strip().lower()
        if post_role == 'admin' and user and auth.get_primary_role(user['user_id']) == 'admin':
            action = (request.POST.get('action') or '').strip()
            order_id = (request.POST.get('order_id') or '').strip()
            payment_status_key = (request.POST.get('payment_status') or '').strip().lower()

            status_map = {
                'paid': 'Lunas',
                'pending': 'Pending',
                'cancelled': 'Dibatalkan',
            }

            try:
                with transaction.atomic():
                    if action == 'update' and order_id and payment_status_key in status_map:
                        od.update_order_status(order_id, status_map[payment_status_key])
                        messages.success(request, f'Order {order_id} berhasil diperbarui.')
                    elif action == 'delete' and order_id:
                        od.delete_order(order_id)
                        messages.success(request, f'Order {order_id} berhasil dihapus.')
                    else:
                        messages.error(request, 'Aksi order tidak valid.')
            except Exception as e:
                messages.error(request, _clean_db_error(e))

            return redirect(f"{request.path}?role=admin")

        return redirect('core:login')

    if role == 'admin':
        current_orders = od.get_all_orders()
    elif role == 'organizer' and user:
        current_orders = od.get_orders_by_organizer(user['user_id'])
    elif role == 'customer' and user:
        current_orders = od.get_orders_by_customer(user['user_id'])
    else:
        current_orders = []

    for order_item in current_orders:
        order_item['id'] = order_item['order_id']
        order_item['customer'] = order_item['customer_name']
        order_item['date'] = order_item['order_date'].strftime('%Y-%m-%d %H:%M')
        normalized_status = order_item['payment_status'].lower()
        if normalized_status == 'lunas':
            order_item['status_key'] = 'paid'
        elif normalized_status == 'dibatalkan':
            order_item['status_key'] = 'cancelled'
        else:
            order_item['status_key'] = normalized_status
        order_item['status'] = normalized_status
        order_item['total'] = f'Rp {order_item["total_amount"]:,.0f}'.replace(',', '.')

    total_order = len(current_orders)
    paid_count = sum(1 for order_item in current_orders if order_item['status_key'] == 'paid')
    pending_count = sum(1 for order_item in current_orders if order_item['status_key'] == 'pending')
    total_revenue = (
        f'Rp {sum(order_item["total_amount"] for order_item in current_orders):,.0f}'.replace(',', '.')
        if role in {'admin', 'organizer'} and current_orders
        else None
    )

    return render(
        request,
        'core/order.html',
        {
            'role': role,
            'user_name': user['username'] if user else '',
            'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer', 'guest': 'Guest'}.get(role, 'User'),
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
    """Promotion list page."""
    user = _session_user(request)
    role = (request.GET.get('role') or 'guest').strip().lower()
    if role not in {'admin', 'organizer', 'customer', 'guest'}:
        role = 'guest'

    if request.method == 'POST':
        if not user or auth.get_primary_role(user['user_id']) != 'admin':
            return redirect('core:login')

        action = (request.POST.get('action') or '').strip()
        promotion_id = (request.POST.get('promotion_id') or '').strip()
        promo_code = (request.POST.get('promo_code') or '').strip()
        discount_type = (request.POST.get('discount_type') or '').strip().lower()
        discount_value_raw = (request.POST.get('discount_value') or '').strip()
        start_date = (request.POST.get('start_date') or '').strip()
        end_date = (request.POST.get('end_date') or '').strip()
        usage_limit_raw = (request.POST.get('usage_limit') or '').strip()

        if action not in {'create', 'update', 'delete'}:
            messages.error(request, 'Aksi promo tidak valid.')
            return redirect(f'{request.path}?role=admin')

        try:
            with transaction.atomic():
                if action == 'delete':
                    if not promotion_id:
                        messages.error(request, 'Promo tidak ditemukan.')
                    else:
                        promo.delete_promotion(promotion_id)
                        messages.success(request, 'Promo berhasil dihapus.')
                else:
                    if not all([promo_code, discount_type, discount_value_raw, start_date, end_date, usage_limit_raw]):
                        raise ValueError('Semua field promo wajib diisi.')

                    discount_value = float(discount_value_raw)
                    usage_limit = int(usage_limit_raw)

                    if discount_type not in {'percentage', 'nominal'}:
                        raise ValueError('Tipe diskon tidak valid.')
                    if discount_value < 0:
                        raise ValueError('Nilai diskon tidak boleh negatif.')
                    if usage_limit <= 0:
                        raise ValueError('Batas penggunaan harus lebih dari 0.')

                    if action == 'create':
                        promo.create_promotion(promo_code, discount_type, discount_value, start_date, end_date, usage_limit)
                        messages.success(request, 'Promo berhasil dibuat.')
                    else:
                        if not promotion_id:
                            raise ValueError('Promo tidak ditemukan.')
                        promo.update_promotion(promotion_id, promo_code, discount_type, discount_value, start_date, end_date, usage_limit)
                        messages.success(request, 'Promo berhasil diperbarui.')
        except Exception as e:
            messages.error(request, _clean_db_error(e) if 'Error:' in str(e) else str(e))

        return redirect(f'{request.path}?role=admin')

    raw_promotions = promo.get_promotions()
    promotions = []
    total_usage = 0
    for promotion_item in raw_promotions:
        discount_type = (promotion_item['discount_type'] or '').lower()
        total_usage += int(promotion_item.get('usage_count') or 0)
        promotions.append({
            'id': promotion_item['promotion_id'],
            'promo_code': promotion_item['promo_code'],
            'discount_type': discount_type,
            'discount_type_label': 'Persentase' if discount_type == 'percentage' else 'Nominal',
            'discount_type_value': discount_type,
            'discount_value': float(promotion_item['discount_value']),
            'discount_value_display': (
                f'{promotion_item["discount_value"]:.0f}%'
                if discount_type == 'percentage'
                else f'Rp {promotion_item["discount_value"]:,.0f}'.replace(',', '.')
            ),
            'start_date': promotion_item['start_date'].isoformat(),
            'start_date_value': promotion_item['start_date'].isoformat(),
            'end_date': promotion_item['end_date'].isoformat(),
            'end_date_value': promotion_item['end_date'].isoformat(),
            'usage_limit': promotion_item['usage_limit'],
            'usage_count': promotion_item['usage_count'],
            'usage': f'{promotion_item["usage_count"]} / {promotion_item["usage_limit"]}',
            'status': 'active' if promotion_item['start_date'] <= date.today() <= promotion_item['end_date'] else 'expired',
            'status_label': 'Aktif' if promotion_item['start_date'] <= date.today() <= promotion_item['end_date'] else 'Tidak Aktif',
        })

    stats = {
        'total_promo': len(promotions),
        'total_usage': total_usage,
        'percentage_type': sum(1 for promotion in promotions if promotion['discount_type'] == 'percentage'),
    }

    return render(
        request,
        'core/promotion.html',
        {
            'role': role,
            'user_name': user['username'] if user else '',
            'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer', 'guest': 'Guest'}.get(role, 'User'),
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



# =============================================================================
# Features 5-8: Venue & Event
# =============================================================================

def _role_context(request, role: str, active: str, profile: dict | None = None) -> dict:
    user = _session_user(request)
    display_name = ''
    if profile:
        display_name = profile.get('full_name') or profile.get('organizer_name') or ''
    if not display_name and user:
        display_name = user.get('username', '')

    return {
        'role': role,
        'active': active,
        'user_name': display_name,
        'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer'}.get(role, 'User'),
    }


def _format_rupiah(value) -> str:
    if value is None:
        return '-'
    try:
        return f"Rp {int(value):,}".replace(',', '.')
    except (TypeError, ValueError):
        return '-'


def _ensure_event_datetime(event_dt):
    if not event_dt:
        return event_dt
    if timezone.is_naive(event_dt) and timezone.is_aware(timezone.now()):
        return timezone.make_aware(event_dt, timezone.get_current_timezone())
    return event_dt


def _event_status_label(event_dt) -> tuple[str, str]:
    event_dt = _ensure_event_datetime(event_dt)
    if not event_dt:
        return 'Draft', 'badge-warning'
    now = timezone.now()
    if event_dt >= now:
        return 'Aktif', 'badge-success'
    return 'Berjalan', 'badge-muted'


def _format_event_date(event_dt) -> str:
    event_dt = _ensure_event_datetime(event_dt)
    if not event_dt:
        return '-'
    if timezone.is_aware(event_dt):
        event_dt = timezone.localtime(event_dt)
    return event_dt.strftime('%d %b %Y')


def _format_event_datetime_local(event_dt) -> str:
    event_dt = _ensure_event_datetime(event_dt)
    if not event_dt:
        return ''
    if timezone.is_aware(event_dt):
        event_dt = timezone.localtime(event_dt)
    return event_dt.strftime('%Y-%m-%dT%H:%M')


def venue_admin(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'admin':
        return _redirect_dashboard(role) if role else redirect('core:login')

    search = (request.GET.get('search') or '').strip()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        venue_name = (request.POST.get('venue_name') or '').strip()
        city = (request.POST.get('city') or '').strip()
        address = (request.POST.get('address') or '').strip()
        capacity_raw = (request.POST.get('capacity') or '').strip()
        venue_id = (request.POST.get('venue_id') or '').strip()

        if action in ('create', 'update'):
            if not all([venue_name, city, address, capacity_raw]):
                messages.error(request, 'Semua field wajib diisi.')
                return redirect('core:venue_admin')
            try:
                capacity = int(capacity_raw)
                if capacity <= 0:
                    raise ValueError('capacity')
            except ValueError:
                messages.error(request, 'Kapasitas harus berupa angka > 0.')
                return redirect('core:venue_admin')

        try:
            with transaction.atomic():
                if action == 'create':
                    vn.create_venue(venue_name, capacity, address, city)
                    messages.success(request, f"Venue '{venue_name}' berhasil ditambahkan.")
                elif action == 'update':
                    if not venue_id:
                        messages.error(request, 'Venue tidak ditemukan.')
                        return redirect('core:venue_admin')
                    vn.update_venue(venue_id, venue_name, capacity, address, city)
                    messages.success(request, f"Venue '{venue_name}' berhasil diperbarui.")
                elif action == 'delete':
                    if not venue_id:
                        messages.error(request, 'Venue tidak ditemukan.')
                        return redirect('core:venue_admin')
                    existing = vn.get_venue_by_id(venue_id)
                    vn.delete_venue(venue_id)
                    messages.success(request, f"Venue '{existing['venue_name'] if existing else venue_id}' berhasil dihapus.")
        except Exception as e:
            messages.error(request, _clean_db_error(e))

        return redirect('core:venue_admin')

    venues = vn.get_all_venues(search=search)
    stats = vn.get_venue_stats()
    for venue in venues:
        if venue['active_event_count'] > 0:
            status_label, status_class = 'Aktif', 'badge-success'
        elif venue['event_count'] == 0:
            status_label, status_class = 'Draft', 'badge-muted'
        else:
            status_label, status_class = 'Perlu review', 'badge-warning'
        venue['status_label'] = status_label
        venue['status_class'] = status_class
        venue['updated_label'] = '—'

    ctx = _role_context(request, 'admin', 'venue')
    ctx.update({
        'venues': venues,
        'stats': stats,
        'search': search,
    })
    return render(request, 'core/venue_admin.html', ctx)


def venue_organizer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'organizer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    profile = auth.get_organizer_profile(user['user_id'])
    organizer_id = profile['organizer_id'] if profile else ''

    search = (request.GET.get('search') or '').strip()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        venue_name = (request.POST.get('venue_name') or '').strip()
        city = (request.POST.get('city') or '').strip()
        address = (request.POST.get('address') or '').strip()
        capacity_raw = (request.POST.get('capacity') or '').strip()
        venue_id = (request.POST.get('venue_id') or '').strip()

        if action in ('create', 'update'):
            if not all([venue_name, city, address, capacity_raw]):
                messages.error(request, 'Semua field wajib diisi.')
                return redirect('core:venue_organizer')
            try:
                capacity = int(capacity_raw)
                if capacity <= 0:
                    raise ValueError('capacity')
            except ValueError:
                messages.error(request, 'Kapasitas harus berupa angka > 0.')
                return redirect('core:venue_organizer')

        try:
            with transaction.atomic():
                if action == 'create':
                    vn.create_venue(venue_name, capacity, address, city)
                    messages.success(request, f"Venue '{venue_name}' berhasil diajukan.")
                elif action == 'update':
                    if not venue_id:
                        messages.error(request, 'Venue tidak ditemukan.')
                        return redirect('core:venue_organizer')
                    vn.update_venue(venue_id, venue_name, capacity, address, city)
                    messages.success(request, f"Venue '{venue_name}' berhasil diperbarui.")
                elif action == 'delete':
                    if not venue_id:
                        messages.error(request, 'Venue tidak ditemukan.')
                        return redirect('core:venue_organizer')
                    existing = vn.get_venue_by_id(venue_id)
                    vn.delete_venue(venue_id)
                    messages.success(request, f"Venue '{existing['venue_name'] if existing else venue_id}' berhasil dihapus.")
        except Exception as e:
            messages.error(request, _clean_db_error(e))

        return redirect('core:venue_organizer')

    venues = vn.get_all_venues(search=search)
    approved = 0
    pending = 0
    city_set = set()
    for venue in venues:
        city_set.add(venue['city'])
        if venue['active_event_count'] > 0:
            status_label, status_class = 'Aktif', 'badge-success'
            approved += 1
        elif venue['event_count'] == 0:
            status_label, status_class = 'Draft', 'badge-muted'
        else:
            status_label, status_class = 'Menunggu', 'badge-warning'
            pending += 1
        venue['status_label'] = status_label
        venue['status_class'] = status_class

    ctx = _role_context(request, 'organizer', 'venue', profile)
    ctx.update({
        'venues': venues,
        'search': search,
        'stats': {
            'total_venues': len(venues),
            'approved': approved,
            'pending': pending,
            'city_count': len(city_set),
        },
    })
    return render(request, 'core/venue_organizer.html', ctx)


def venue_customer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id']) or 'customer'

    profile = None
    if role == 'customer':
        profile = auth.get_customer_profile(user['user_id'])
    elif role == 'organizer':
        profile = auth.get_organizer_profile(user['user_id'])

    search = (request.GET.get('search') or '').strip()
    venues = vn.get_all_venues(search=search)
    stats = vn.get_venue_stats()

    ctx = _role_context(request, role, 'venue', profile)
    ctx.update({
        'venues': venues,
        'stats': stats,
        'search': search,
    })
    return render(request, 'core/venue_customer.html', ctx)


def event_admin(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'admin':
        return _redirect_dashboard(role) if role else redirect('core:login')

    search = (request.GET.get('search') or '').strip()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        event_id = (request.POST.get('event_id') or '').strip()
        event_title = (request.POST.get('event_title') or '').strip()
        event_datetime = (request.POST.get('event_datetime') or '').strip()
        venue_id = (request.POST.get('venue_id') or '').strip()
        organizer_id = (request.POST.get('organizer_id') or '').strip()

        if not all([event_title, event_datetime, venue_id, organizer_id]):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect('core:event_admin')

        try:
            with transaction.atomic():
                if action == 'create':
                    ev.create_event(event_title, event_datetime, venue_id, organizer_id)
                    messages.success(request, f"Event '{event_title}' berhasil dibuat.")
                elif action == 'update':
                    if not event_id:
                        messages.error(request, 'Event tidak ditemukan.')
                        return redirect('core:event_admin')
                    ev.update_event(event_id, event_title, event_datetime, venue_id, organizer_id)
                    messages.success(request, f"Event '{event_title}' berhasil diperbarui.")
        except Exception as e:
            messages.error(request, _clean_db_error(e))

        return redirect('core:event_admin')

    events = ev.get_all_events(search=search)
    total_events = len(events)
    active_events = 0
    upcoming_week = 0
    now = timezone.now()

    for event in events:
        event_dt = _ensure_event_datetime(event['event_datetime'])
        status_label, status_class = _event_status_label(event_dt)
        if status_label == 'Aktif':
            active_events += 1
        if event_dt and event_dt >= now and event_dt <= now + timedelta(days=7):
            upcoming_week += 1

        event['status_label'] = status_label
        event['status_class'] = status_class
        event['event_date_display'] = _format_event_date(event_dt)
        event['event_datetime_local'] = _format_event_datetime_local(event_dt)

    ctx = _role_context(request, 'admin', 'event')
    ctx.update({
        'events': events,
        'search': search,
        'venues': tkt.get_venues_for_dropdown(),
        'organizers': ev.get_organizers_for_dropdown(),
        'stats': {
            'total_events': total_events,
            'active_events': active_events,
            'draft_events': max(total_events - active_events, 0),
            'busy_week': upcoming_week,
        },
    })
    return render(request, 'core/event_admin.html', ctx)


def event_organizer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'organizer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    profile = auth.get_organizer_profile(user['user_id'])
    organizer_id = profile['organizer_id'] if profile else ''

    search = (request.GET.get('search') or '').strip()

    if request.method == 'POST':
        action = request.POST.get('action', '')
        event_id = (request.POST.get('event_id') or '').strip()
        event_title = (request.POST.get('event_title') or '').strip()
        event_datetime = (request.POST.get('event_datetime') or '').strip()
        venue_id = (request.POST.get('venue_id') or '').strip()

        if not all([event_title, event_datetime, venue_id]):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect('core:event_organizer')

        try:
            with transaction.atomic():
                if action == 'create':
                    ev.create_event(event_title, event_datetime, venue_id, organizer_id)
                    messages.success(request, f"Event '{event_title}' berhasil dibuat.")
                elif action == 'update':
                    if not event_id:
                        messages.error(request, 'Event tidak ditemukan.')
                        return redirect('core:event_organizer')
                    existing = ev.get_event_by_id(event_id)
                    if not existing or existing['organizer_id'] != organizer_id:
                        messages.error(request, 'Event tidak ditemukan atau bukan milik Anda.')
                        return redirect('core:event_organizer')
                    ev.update_event(event_id, event_title, event_datetime, venue_id, organizer_id)
                    messages.success(request, f"Event '{event_title}' berhasil diperbarui.")
        except Exception as e:
            messages.error(request, _clean_db_error(e))

        return redirect('core:event_organizer')

    events = ev.get_all_events(search=search, organizer_id=organizer_id)
    now = timezone.now()
    active_events = 0
    for event in events:
        event_dt = _ensure_event_datetime(event['event_datetime'])
        status_label, status_class = _event_status_label(event_dt)
        if status_label == 'Aktif':
            active_events += 1
        event['status_label'] = status_label
        event['status_class'] = status_class
        event['event_date_display'] = _format_event_date(event_dt)
        event['event_datetime_local'] = _format_event_datetime_local(event_dt)

    ctx = _role_context(request, 'organizer', 'event', profile)
    ctx.update({
        'events': events,
        'search': search,
        'venues': tkt.get_venues_for_dropdown(),
        'organizer_id': organizer_id,
        'stats': {
            'total_events': len(events),
            'active_events': active_events,
            'draft_events': max(len(events) - active_events, 0),
            'venue_count': len({event['venue_id'] for event in events}),
        },
    })
    return render(request, 'core/event_organizer.html', ctx)


def event_customer(request):
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id']) or 'customer'

    profile = None
    if role == 'customer':
        profile = auth.get_customer_profile(user['user_id'])
    elif role == 'organizer':
        profile = auth.get_organizer_profile(user['user_id'])

    search = (request.GET.get('search') or '').strip()
    events = ev.get_all_events(search=search)

    now = timezone.now()
    upcoming_week = 0
    cities = set()
    for event in events:
        cities.add(event['city'])
        event_dt = _ensure_event_datetime(event['event_datetime'])
        status_label, status_class = _event_status_label(event_dt)
        event['status_label'] = status_label
        event['status_class'] = status_class
        event['event_date_display'] = _format_event_date(event_dt)
        event['min_price_display'] = _format_rupiah(event['min_price'])
        if event_dt and event_dt >= now and event_dt <= now + timedelta(days=7):
            upcoming_week += 1

    ctx = _role_context(request, role, 'event', profile)
    ctx.update({
        'events': events,
        'search': search,
        'stats': {
            'total_events': len(events),
            'upcoming_week': upcoming_week,
            'city_count': len(cities),
            'promo_active': 0,
        },
    })
    return render(request, 'core/event_customer.html', ctx)


def profile_admin(request):
    """Admin profile page - frontend only."""
    return render(request, 'core/profile_admin.html', {})


def profile_customer(request):
    """Customer profile page - frontend only."""
    return render(request, 'core/profile_customer.html', {})


def profile_organizer(request):
    """Organizer profile page - frontend only."""
    return render(request, 'core/profile_organizer.html', {})


# =============================================================================
# Features 9-10: Artist Management
# =============================================================================

def _artist_role(request) -> str | None:
    user = _session_user(request)
    if not user:
        return None
    return auth.get_primary_role(user['user_id'])


def _artist_context(request, role: str) -> dict:
    user = _session_user(request)
    return {
        'role': role,
        'user_name': user['username'] if user else '',
        'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer'}.get(role, 'User'),
        'active': 'artists',
    }


def artist_list(request):
    """Fitur 9/10 - Daftar artist. Admin: CUD buttons. Others: read-only."""
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if not role:
        return redirect('core:login')

    search_query = (request.GET.get('search') or '').strip()
    artist_list_data = art.get_all_artists(search=search_query)
    stats = art.get_artist_stats()

    # Map DB column names to what template expects
    for a in artist_list_data:
        a['id'] = a['artist_id']

    ctx = _artist_context(request, role)
    ctx.update({
        'artists': artist_list_data,
        'artist_found': len(artist_list_data),
        'search_query': search_query,
        **stats,
    })
    return render(request, 'artist/artist_list.html', ctx)


def artist_read(request):
    """Fitur 10 - R Artist (customer/organizer view tanpa action)."""
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])

    search_query = (request.GET.get('search') or '').strip()
    artist_list_data = art.get_all_artists(search=search_query)
    for a in artist_list_data:
        a['id'] = a['artist_id']

    stats = art.get_artist_stats()
    ctx = _artist_context(request, role or 'customer')
    ctx.update({
        'artists': artist_list_data,
        'artist_found': len(artist_list_data),
        'search_query': search_query,
        **stats,
    })
    return render(request, 'artist/artist_read.html', ctx)


def artist_create(request):
    """Fitur 9 - C Artist (admin only)."""
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'admin':
        return redirect('core:artist_list')

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        genre = (request.POST.get('genre') or '').strip()
        if not name:
            messages.error(request, 'Nama artist wajib diisi.')
            return render(request, 'artist/artist_create.html', {
                'form_data': {'name': name, 'genre': genre},
                **_artist_context(request, role),
            })
        try:
            with transaction.atomic():
                art.create_artist(name, genre or None)
            messages.success(request, f"Artist '{name}' berhasil ditambahkan.")
            return redirect('core:artist_list')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
            return render(request, 'artist/artist_create.html', {
                'form_data': {'name': name, 'genre': genre},
                **_artist_context(request, role),
            })

    return render(request, 'artist/artist_create.html', {
        'form_data': {},
        **_artist_context(request, role),
    })


def artist_update(request, id):
    """Fitur 9 - U Artist (admin only)."""
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'admin':
        return redirect('core:artist_list')

    artist = art.get_artist_by_id(id)
    if not artist:
        messages.error(request, 'Artist tidak ditemukan.')
        return redirect('core:artist_list')

    artist['id'] = artist['artist_id']

    if request.method == 'POST':
        name = (request.POST.get('name') or '').strip()
        genre = (request.POST.get('genre') or '').strip()
        if not name:
            messages.error(request, 'Nama artist wajib diisi.')
            return render(request, 'artist/artist_update.html', {
                'artist': artist,
                **_artist_context(request, role),
            })
        try:
            with transaction.atomic():
                art.update_artist(id, name, genre or None)
            messages.success(request, f"Artist '{name}' berhasil diperbarui.")
            return redirect('core:artist_list')
        except Exception as e:
            messages.error(request, _clean_db_error(e))

    return render(request, 'artist/artist_update.html', {
        'artist': artist,
        **_artist_context(request, role),
    })


def artist_delete(request, id):
    """Fitur 9 - D Artist (admin only)."""
    user = _session_user(request)
    if not user:
        return redirect('core:login')
    role = auth.get_primary_role(user['user_id'])
    if role != 'admin':
        return redirect('core:artist_list')

    artist = art.get_artist_by_id(id)
    if not artist:
        messages.error(request, 'Artist tidak ditemukan.')
        return redirect('core:artist_list')

    artist['id'] = artist['artist_id']

    if request.method == 'POST':
        try:
            with transaction.atomic():
                art.delete_artist(id)
            messages.success(request, f"Artist '{artist['name']}' berhasil dihapus.")
            return redirect('core:artist_list')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
            return redirect('core:artist_list')

    return render(request, 'artist/artist_delete.html', {
        'artist': artist,
        **_artist_context(request, role),
    })


def checkout(request):
    """Checkout page - order creation/ticket purchase."""
    user = _session_user(request)
    if not user:
        return redirect('core:login')

    role = auth.get_primary_role(user['user_id'])
    if role != 'customer':
        return _redirect_dashboard(role) if role else redirect('core:login')

    profile = auth.get_customer_profile(user['user_id'])
    if not profile:
        messages.error(request, 'Profil customer tidak ditemukan.')
        return redirect('core:login')

    event_id = request.GET.get('event_id') or request.POST.get('event_id')
    event_data = ev.get_event_by_id(event_id) if event_id else None
    if not event_data:
        messages.error(request, 'Event tidak ditemukan.')
        return redirect('core:event_customer')

    venue = vn.get_venue_by_id(event_data['venue_id'])
    event = {
        'event_id': event_data['event_id'],
        'name': event_data['event_title'],
        'date': _format_event_date(_ensure_event_datetime(event_data['event_datetime'])),
        'venue': venue['venue_name'] if venue else 'Unknown Venue',
    }

    ticket_categories = tkt.get_categories_for_event(event_id)
    available_seats = tkt.get_seats_for_venue(event_data['venue_id']) if venue else []
    promotions = promo.get_promotions()
    event_dt = _ensure_event_datetime(event_data['event_datetime'])
    form_data = {
        'selected_category_id': '',
        'quantity': 2,
        'promo_code': '',
        'selected_seat_ids': '',
    }

    def render_checkout():
        return render(request, 'core/checkout.html', {
            'event': event,
            'ticket_categories': ticket_categories,
            'available_seats': available_seats,
            'promotions': promotions,
            'event_date': event_dt.date().isoformat() if event_dt else '',
            'form_data': form_data,
            'user_name': user['username'],
            'user_role': 'Customer',
        })

    if request.method == 'POST':
        action = (request.POST.get('action') or 'checkout').strip()
        category_id = (request.POST.get('category_id') or '').strip()
        quantity_raw = request.POST.get('quantity') or '1'
        promo_code = (request.POST.get('promo_code') or '').strip()
        seat_ids_raw = (request.POST.get('seat_ids') or '').strip()

        form_data['selected_category_id'] = category_id
        form_data['promo_code'] = promo_code
        form_data['selected_seat_ids'] = seat_ids_raw

        try:
            quantity = int(quantity_raw)
            if quantity < 1 or quantity > 10:
                raise ValueError('Jumlah tiket harus berada di antara 1 dan 10.')
            form_data['quantity'] = quantity
        except ValueError:
            messages.error(request, 'Jumlah tiket tidak valid.')
            return render_checkout()

        if not category_id:
            messages.error(request, 'Pilih kategori tiket terlebih dahulu.')
            return render_checkout()

        category = tc_mod.get_ticket_category_by_id(category_id)
        if not category or category['tevent_id'] != event_id:
            messages.error(request, 'Kategori tiket tidak valid untuk event ini.')
            return render_checkout()

        seat_ids = [seat_id for seat_id in seat_ids_raw.split(',') if seat_id.strip()]
        if seat_ids and len(seat_ids) != quantity:
            messages.error(request, 'Jumlah kursi harus sama dengan jumlah tiket.')
            return render_checkout()

        available_seat_ids = {seat['seat_id'] for seat in available_seats}
        invalid_seats = [seat_id for seat_id in seat_ids if seat_id not in available_seat_ids]
        if invalid_seats:
            messages.error(request, 'Beberapa kursi tidak lagi tersedia, silakan pilih ulang.')
            return render_checkout()

        total_amount = category['price'] * quantity

        try:
            with transaction.atomic():
                order_id = od.create_order(profile['customer_id'], total_amount, 'Lunas')
                created_tickets = []
                for _ in range(quantity):
                    created_tickets.append(tkt.create_ticket(order_id, category_id))

                if seat_ids:
                    if len(seat_ids) != len(created_tickets):
                        raise Exception('Jumlah kursi harus sama dengan jumlah tiket.')
                    for ticket_id, seat_id in zip(created_tickets, seat_ids):
                        tkt.assign_seat_to_ticket(ticket_id, seat_id)

                if promo_code:
                    promotion = promo.get_promotion_by_code(promo_code)
                    # If not found in Python, pass the code as the ID to force the SQL trigger
                    # to throw its custom "ID tidak ditemukan" error.
                    promo_id_to_apply = promotion['promotion_id'] if promotion else promo_code
                    od.apply_promotion(order_id, promo_id_to_apply)

            messages.success(request, 'Order berhasil dibuat. Silakan cek My Tickets.')
            return redirect('core:my_tickets')
        except Exception as e:
            messages.error(request, _clean_db_error(e))

    return render_checkout()


def _tc_context(request, role: str) -> dict:
    user = _session_user(request)
    return {
        'role': role,
        'user_name': user['username'] if user else '',
        'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer'}.get(role, 'User'),
        'active': 'ticket_category',
    }


def ticket_category_list(request):
    """
    Fitur 11/12 - CUD + R Ticket Category
    Admin/Organizer: full CRUD via modal. Customer/Guest: read-only.
    URL: /ticket-categories/
    """
    user = _session_user(request)
    role = auth.get_primary_role(user['user_id']) if user else None

    # Customers and guests → redirect to read-only view
    if not user or role not in ('admin', 'organizer'):
        return redirect('core:ticket_category_list_customer')

    search = (request.GET.get('search') or '').strip()
    event_id_filter = (request.GET.get('event_id') or '').strip()

    # ── Handle POST (Create / Update / Delete) ──────────────────────────────
    if request.method == 'POST':
        if role not in ('admin', 'organizer'):
            return redirect('core:login')

        action = request.POST.get('action', '')

        if action == 'create':
            cat_name = (request.POST.get('category_name') or '').strip()
            quota_raw = (request.POST.get('quota') or '').strip()
            price_raw = (request.POST.get('price') or '').strip()
            tevent_id = (request.POST.get('tevent_id') or '').strip()

            # Validation
            error = None
            if not cat_name:
                error = 'Nama kategori wajib diisi.'
            elif not quota_raw or not price_raw or not tevent_id:
                error = 'Semua field wajib diisi.'
            else:
                try:
                    quota = int(quota_raw)
                    price = float(price_raw)
                    if quota <= 0:
                        error = 'Kuota harus bilangan bulat positif (> 0).'
                    elif price < 0:
                        error = 'Harga tidak boleh negatif (>= 0).'
                    elif tc_mod.category_name_exists_in_event(cat_name, tevent_id):
                        error = f"Kategori '{cat_name}' sudah ada pada event ini."
                    else:
                        # Check venue capacity
                        capacity = tc_mod.get_venue_capacity_for_event(tevent_id)
                        current_total = tc_mod.get_total_quota_for_event(tevent_id)
                        if capacity is not None and (current_total + quota) > capacity:
                            error = f'Total kuota melebihi kapasitas venue ({capacity} kursi).'
                except ValueError:
                    error = 'Kuota dan Harga harus berupa angka.'

            if error:
                messages.error(request, error)
            else:
                try:
                    with transaction.atomic():
                        tc_mod.create_ticket_category(cat_name, quota, price, tevent_id)
                    messages.success(request, f"Kategori '{cat_name}' berhasil ditambahkan.")
                except Exception as e:
                    messages.error(request, _clean_db_error(e))

        elif action == 'update':
            category_id = (request.POST.get('category_id') or '').strip()
            cat_name = (request.POST.get('category_name') or '').strip()
            quota_raw = (request.POST.get('quota') or '').strip()
            price_raw = (request.POST.get('price') or '').strip()

            error = None
            if not cat_name:
                error = 'Nama kategori wajib diisi.'
            elif not quota_raw or not price_raw:
                error = 'Semua field wajib diisi.'
            else:
                try:
                    quota = int(quota_raw)
                    price = float(price_raw)
                    if quota <= 0:
                        error = 'Kuota harus bilangan bulat positif (> 0).'
                    elif price < 0:
                        error = 'Harga tidak boleh negatif (>= 0).'
                    else:
                        existing = tc_mod.get_ticket_category_by_id(category_id)
                        if existing:
                            # Check duplicate name (exclude self)
                            if tc_mod.category_name_exists_in_event(
                                cat_name, existing['tevent_id'],
                                exclude_category_id=category_id
                            ):
                                error = f"Kategori '{cat_name}' sudah ada pada event ini."
                            else:
                                capacity = tc_mod.get_venue_capacity_for_event(existing['tevent_id'])
                                current_total = tc_mod.get_total_quota_for_event(
                                    existing['tevent_id'], exclude_category_id=category_id
                                )
                                if capacity is not None and (current_total + quota) > capacity:
                                    error = f'Total kuota melebihi kapasitas venue ({capacity} kursi).'
                except ValueError:
                    error = 'Kuota dan Harga harus berupa angka.'

            if error:
                messages.error(request, error)
            else:
                try:
                    with transaction.atomic():
                        tc_mod.update_ticket_category(category_id, cat_name, quota, price)
                    messages.success(request, f"Kategori '{cat_name}' berhasil diperbarui.")
                except Exception as e:
                    messages.error(request, _clean_db_error(e))

        elif action == 'delete':
            category_id = (request.POST.get('category_id') or '').strip()
            try:
                existing = tc_mod.get_ticket_category_by_id(category_id)
                with transaction.atomic():
                    tc_mod.delete_ticket_category(category_id)
                name = existing['category_name'] if existing else category_id
                messages.success(request, f"Kategori '{name}' berhasil dihapus.")
            except Exception as e:
                messages.error(request, _clean_db_error(e))

        return redirect('core:ticket_category_list')

    # ── GET ──────────────────────────────────────────────────────────────────
    categories = tc_mod.get_all_ticket_categories(search=search, event_id=event_id_filter)
    stats = tc_mod.get_ticket_category_stats()
    events = tkt.get_events_for_dropdown()

    ctx = _tc_context(request, role or 'guest')
    ctx.update({
        'categories': categories,
        'total_found': len(categories),
        'search': search,
        'selected_event': event_id_filter,
        'events': events,
        **stats,
    })
    return render(request, 'ticket_category/ticket_category_list.html', ctx)


def ticket_category_list_customer(request):
    """
    Fitur 12 - R Ticket Category
    Tampilan untuk Customer/Guest - read only, tanpa tombol aksi
    URL: /ticket-categories/customer/
    """
    user = _session_user(request)
    role = auth.get_primary_role(user['user_id']) if user else 'guest'

    # Admin/organizer should use the manage view
    if user and role in ('admin', 'organizer'):
        return redirect('core:ticket_category_list')

    search = (request.GET.get('search') or '').strip()
    event_id_filter = (request.GET.get('event_id') or '').strip()

    categories = tc_mod.get_all_ticket_categories(search=search, event_id=event_id_filter)
    stats = tc_mod.get_ticket_category_stats()
    events = tkt.get_events_for_dropdown()

    ctx = _tc_context(request, role or 'guest')
    ctx.update({
        'categories': categories,
        'total_found': len(categories),
        'search': search,
        'selected_event': event_id_filter,
        'events': events,
        **stats,
    })
    return render(request, 'ticket_category/ticket_category_list_customer.html', ctx)

# =============================================================================
# Features 18-20: Ticket Management
# =============================================================================

def _ticket_role(request) -> str | None:
    """Return role from session, or None if not logged in."""
    user = _session_user(request)
    if not user:
        return None
    return auth.get_primary_role(user['user_id'])


def _ticket_context(request, role: str, active: str) -> dict:
    user = _session_user(request)
    ctx = {
        'role': role,
        'active': active,
        'user_name': user['username'] if user else 'User',
        'user_role': {'admin': 'Administrator', 'organizer': 'Organizer', 'customer': 'Customer'}.get(role, 'User'),
    }
    return ctx


def tickets_admin(request):
    role = _ticket_role(request)
    if role != 'admin':
        return redirect('core:login')

    search = (request.GET.get('search') or '').strip()
    event_id = (request.GET.get('event_id') or '').strip()
    payment_status = (request.GET.get('payment_status') or '').strip()

    ticket_list = tkt.get_all_tickets(search=search, event_id=event_id, payment_status=payment_status)
    events = tkt.get_events_for_dropdown()
    orders = tkt.get_orders_for_dropdown()
    venues = tkt.get_venues_for_dropdown()

    categories_by_event = {}
    seats_by_venue = {}
    event_to_venue = {}
    for event in events:
        cats = tkt.get_categories_for_event(event['event_id'])
        for cat in cats:
            cat['price'] = float(cat['price']) if cat.get('price') is not None else 0
        categories_by_event[str(event['event_id'])] = cats
        event_to_venue[str(event['event_id'])] = str(event['venue_id']) if event.get('venue_id') else ''
    for venue in venues:
        seats_by_venue[str(venue['venue_id'])] = tkt.get_seats_for_venue(venue['venue_id'])

    create_events = [e for e in events if categories_by_event.get(str(e['event_id']))]

    for ticket in ticket_list:
        ticket['event_id'] = ticket.get('event_id', '')
        venue_id = event_to_venue.get(str(ticket['event_id']), '')
        ticket['venue_id'] = venue_id

    ctx = _ticket_context(request, 'admin', 'tickets')
    ctx.update({
        'page_title': 'Manajemen Tiket',
        'page_subtitle': 'Kelola semua tiket dalam sistem',
        'tickets': ticket_list,
        'events': events,
        'create_events': create_events,
        'orders': orders,
        'categories_by_event': json.dumps(categories_by_event),
        'seats_by_venue': json.dumps(seats_by_venue),
        'event_to_venue': json.dumps(event_to_venue),
        'total_tickets': len(ticket_list),
        'search': search,
        'selected_event': event_id,
        'selected_payment_status': payment_status,
    })
    return render(request, 'core/tickets_admin.html', ctx)


def tickets_organizer(request):
    role = _ticket_role(request)
    if role not in ('admin', 'organizer'):
        return redirect('core:login')

    user = _session_user(request)
    search = (request.GET.get('search') or '').strip()
    payment_status = (request.GET.get('payment_status') or '').strip()
    ticket_list = tkt.get_tickets_by_organizer(user['user_id'], search=search, payment_status=payment_status)
    events = tkt.get_events_for_dropdown()
    orders = tkt.get_orders_for_dropdown()
    venues = tkt.get_venues_for_dropdown()

    categories_by_event = {}
    seats_by_venue = {}
    event_to_venue = {}
    for event in events:
        cats = tkt.get_categories_for_event(event['event_id'])
        for cat in cats:
            cat['price'] = float(cat['price']) if cat.get('price') is not None else 0
        categories_by_event[str(event['event_id'])] = cats
        event_to_venue[str(event['event_id'])] = str(event['venue_id']) if event.get('venue_id') else ''
    for venue in venues:
        seats_by_venue[str(venue['venue_id'])] = tkt.get_seats_for_venue(venue['venue_id'])

    create_events = [e for e in events if categories_by_event.get(str(e['event_id']))]

    for ticket in ticket_list:
        ticket['event_id'] = ticket.get('event_id', '')
        venue_id = event_to_venue.get(str(ticket['event_id']), '')
        ticket['venue_id'] = venue_id

    ctx = _ticket_context(request, role, 'tickets')
    ctx.update({
        'page_title': 'Manajemen Tiket',
        'page_subtitle': 'Kelola tiket untuk event Anda',
        'tickets': ticket_list,
        'events': events,
        'create_events': create_events,
        'orders': orders,
        'categories_by_event': json.dumps(categories_by_event),
        'seats_by_venue': json.dumps(seats_by_venue),
        'event_to_venue': json.dumps(event_to_venue),
        'total_tickets': len(ticket_list),
        'search': search,
        'selected_payment_status': payment_status,
    })
    return render(request, 'core/tickets_organizer.html', ctx)


def my_tickets(request):
    role = _ticket_role(request)
    if role != 'customer':
        return redirect('core:login')

    user = _session_user(request)
    search = (request.GET.get('search') or '').strip()
    ticket_list = tkt.get_tickets_by_customer(user['user_id'], search=search)

    ctx = _ticket_context(request, 'customer', 'my_tickets')
    ctx.update({
        'page_title': 'Tiket Saya',
        'page_subtitle': 'Tiket yang Anda miliki',
        'tickets': ticket_list,
        'total_tickets': len(ticket_list),
        'search': search,
    })
    return render(request, 'core/my_tickets.html', ctx)


def ticket_create(request):
    """Create ticket — Admin or Organizer."""
    role = _ticket_role(request)
    if role not in ('admin', 'organizer'):
        return redirect('core:login')

    if request.method == 'POST':
        order_id = (request.POST.get('order_id') or '').strip()
        category_id = (request.POST.get('category_id') or '').strip()
        seat_id = (request.POST.get('seat_id') or '').strip()

        if not order_id or not category_id:
            messages.error(request, 'Order dan Kategori Tiket wajib dipilih.')
            return redirect('core:tickets_admin')

        try:
            with transaction.atomic():
                ticket_id = tkt.create_ticket(order_id, category_id)
                if seat_id:
                    tkt.assign_seat_to_ticket(ticket_id, seat_id)
            messages.success(request, 'Tiket berhasil dibuat.')
        except Exception as e:
            messages.error(request, _clean_db_error(e))

        if role == 'admin':
            return redirect('core:tickets_admin')
        return redirect('core:tickets_organizer')

    # GET — show create form context
    orders = tkt.get_orders_for_dropdown()
    events = tkt.get_events_for_dropdown()

    ctx = _ticket_context(request, role, 'tickets')
    ctx.update({
        'page_title': 'Buat Tiket Baru',
        'orders': orders,
        'events': events,
    })
    template = 'core/tickets_admin.html' if role == 'admin' else 'core/tickets_organizer.html'
    return render(request, template, ctx)


def ticket_update(request, ticket_id):
    role = _ticket_role(request)
    if role != 'admin':
        return redirect('core:login')

    ticket = tkt.get_ticket_by_id(ticket_id)
    if not ticket:
        messages.error(request, 'Tiket tidak ditemukan.')
        return redirect('core:tickets_admin')

    if request.method == 'POST':
        seat_id = (request.POST.get('seat_id') or '').strip()
        try:
            with transaction.atomic():
                tkt.update_ticket_seat(ticket_id, seat_id if seat_id else None)
            messages.success(request, 'Tiket berhasil diperbarui.')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
        return redirect('core:tickets_admin')

    # GET — show update form
    event = tkt.get_event_for_ticket_category(ticket['tcategory_id'])
    seats = tkt.get_seats_for_venue(event['venue_id']) if event else []
    categories = tkt.get_categories_for_event(event['event_id']) if event else []

    ctx = _ticket_context(request, 'admin', 'tickets')
    ctx.update({
        'page_title': 'Update Tiket',
        'ticket': ticket,
        'seats': seats,
        'categories': categories,
    })
    return render(request, 'core/tickets_admin.html', ctx)


def ticket_delete(request, ticket_id):
    role = _ticket_role(request)
    if role != 'admin':
        return redirect('core:login')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                tkt.delete_ticket(ticket_id)
            messages.success(request, 'Tiket berhasil dihapus.')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
        return redirect('core:tickets_admin')

    ticket = tkt.get_ticket_by_id(ticket_id)
    ctx = _ticket_context(request, 'admin', 'tickets')
    ctx['ticket'] = ticket
    return render(request, 'core/tickets_admin.html', ctx)


# =============================================================================
# Features 21-22: Seat Management
# =============================================================================

def seats(request):
    role = _ticket_role(request)
    if not role:
        return redirect('core:login')

    user = _session_user(request)
    if role == 'organizer':
        seat_list = tkt.get_seats_by_organizer(user['user_id'])
    else:
        seat_list = tkt.get_all_seats()

    total = len(seat_list)
    occupied = sum(1 for s in seat_list if s.get('occupied'))
    available = total - occupied

    venues = tkt.get_venues_for_dropdown()
    ctx = _ticket_context(request, role, 'seats')
    ctx.update({
        'page_title': 'Daftar Kursi',
        'page_subtitle': 'Lihat kursi untuk setiap venue',
        'seats': seat_list,
        'total_seats': total,
        'occupied_seats': occupied,
        'available_seats': available,
        'venues': venues,
    })
    if role == 'admin':
        template = 'core/seats_admin.html'
    elif role == 'organizer':
        template = 'core/seats_organizer.html'
    else:
        template = 'core/seats.html'
    return render(request, template, ctx)


def seat_create(request):
    role = _ticket_role(request)
    if role not in ('admin', 'organizer'):
        return redirect('core:login')

    if request.method == 'POST':
        venue_id = (request.POST.get('venue_id') or '').strip()
        section = (request.POST.get('section') or '').strip()
        row_number = (request.POST.get('row_number') or '').strip()
        seat_number = (request.POST.get('seat_number') or '').strip()

        if not all([venue_id, section, row_number, seat_number]):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect('core:seats')

        try:
            with transaction.atomic():
                tkt.create_seat(section, seat_number, row_number, venue_id)
            messages.success(request, 'Kursi berhasil ditambahkan.')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
        return redirect('core:seats')

    venues = tkt.get_venues_for_dropdown()
    ctx = _ticket_context(request, role, 'seats')
    ctx['venues'] = venues
    return render(request, 'core/seats.html', ctx)


def seat_update(request, seat_id):
    role = _ticket_role(request)
    if role not in ('admin', 'organizer'):
        return redirect('core:login')

    seat = tkt.get_seat_by_id(seat_id)
    if not seat:
        messages.error(request, 'Kursi tidak ditemukan.')
        return redirect('core:seats')

    if request.method == 'POST':
        venue_id = (request.POST.get('venue_id') or '').strip()
        section = (request.POST.get('section') or '').strip()
        row_number = (request.POST.get('row_number') or '').strip()
        seat_number = (request.POST.get('seat_number') or '').strip()

        if not all([venue_id, section, row_number, seat_number]):
            messages.error(request, 'Semua field wajib diisi.')
            return redirect('core:seats')

        try:
            with transaction.atomic():
                tkt.update_seat(seat_id, section, seat_number, row_number, venue_id)
            messages.success(request, 'Kursi berhasil diperbarui.')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
        return redirect('core:seats')

    venues = tkt.get_venues_for_dropdown()
    ctx = _ticket_context(request, role, 'seats')
    ctx.update({'seat': seat, 'venues': venues})
    return render(request, 'core/seats.html', ctx)


def seat_delete(request, seat_id):
    role = _ticket_role(request)
    if role not in ('admin', 'organizer'):
        return redirect('core:login')

    if request.method == 'POST':
        try:
            with transaction.atomic():
                tkt.delete_seat(seat_id)
            messages.success(request, 'Kursi berhasil dihapus.')
        except Exception as e:
            messages.error(request, _clean_db_error(e))
        return redirect('core:seats')

    ctx = _ticket_context(request, role, 'seats')
    ctx['seat'] = tkt.get_seat_by_id(seat_id)
    return render(request, 'core/seats.html', ctx)
