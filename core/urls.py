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
    path('order', views.order, name='order'),
    path('checkout', views.checkout, name='checkout'),
    path('promotion', views.promotion, name='promotion'),
    path('profile/customer/', views.profile_customer, name='profile_customer'),
    path('profile/organizer/', views.profile_organizer, name='profile_organizer'),
    path('profile/admin/', views.profile_admin, name='profile_admin'),
]