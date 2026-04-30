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


def profile_customer(request):
    """Customer profile page - frontend only."""
    return render(request, 'core/profile_customer.html', {})


def profile_organizer(request):
    """Organizer profile page - frontend only."""
    return render(request, 'core/profile_organizer.html', {})


def profile_admin(request):
    """Admin profile page - frontend only."""
    return render(request, 'core/profile_admin.html', {})