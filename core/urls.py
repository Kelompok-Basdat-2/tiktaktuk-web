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
    path('profile/customer/', views.profile_customer, name='profile_customer'),
    path('profile/organizer/', views.profile_organizer, name='profile_organizer'),
    path('profile/admin/', views.profile_admin, name='profile_admin'),
    
    path('artists/', views.artist_list, name='artist_list'),
    path('artists/create/', views.artist_create, name='artist_create'),
    path("artists/<str:id>/update/", views.artist_update, name="artist_update"),
    path("artists/<str:id>/delete/", views.artist_delete, name="artist_delete"),

    path('ticket-categories/', views.ticket_category_list, name='ticket_category_list'),
    
]