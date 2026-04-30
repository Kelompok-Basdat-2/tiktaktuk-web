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