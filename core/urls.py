from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    path('dashboard/organizer/', views.dashboard_organizer, name='dashboard_organizer'),
    path('dashboard/customer/', views.dashboard_customer, name='dashboard_customer'),
    path('venue/admin/', views.venue_admin, name='venue_admin'),
    path('venue/organizer/', views.venue_organizer, name='venue_organizer'),
    path('venue/customer/', views.venue_customer, name='venue_customer'),
    path('event/admin/', views.event_admin, name='event_admin'),
    path('event/organizer/', views.event_organizer, name='event_organizer'),
    path('event/customer/', views.event_customer, name='event_customer'),
    path('profile/customer/', views.profile_customer, name='profile_customer'),
    path('profile/organizer/', views.profile_organizer, name='profile_organizer'),
    path('profile/admin/', views.profile_admin, name='profile_admin'),
    # Tickets (Features 18-20)
    path('tickets/', views.tickets_admin, name='tickets_admin'),
    path('tickets/organizer/', views.tickets_organizer, name='tickets_organizer'),
    path('my-tickets/', views.my_tickets, name='my_tickets'),
    path('tickets/create/admin/', views.ticket_create_admin, name='ticket_create_admin'),
    path('tickets/create/organizer/', views.ticket_create_organizer, name='ticket_create_organizer'),
    path('tickets/<uuid:ticket_id>/update/', views.ticket_update, name='ticket_update'),
    path('tickets/<uuid:ticket_id>/delete/', views.ticket_delete, name='ticket_delete'),
    # Seats (Features 21-22)
    path('seats/', views.seats, name='seats'),
    path('seats/admin/', views.seats_admin, name='seats_admin'),
    path('seats/organizer/', views.seats_organizer, name='seats_organizer'),
    path('seats/create/', views.seat_create, name='seat_create'),
    path('seats/<uuid:seat_id>/update/', views.seat_update, name='seat_update'),
    path('seats/<uuid:seat_id>/delete/', views.seat_delete, name='seat_delete'),
]