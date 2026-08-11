from django.urls import path
from django.contrib.auth import views as auth_views
from dashboard.views import dashboard_view
from core.views import (
    HomeView,
    superadmin_dashboard, company_create, company_toggle,
    user_list, user_create, user_update, user_toggle,
    company_settings,
)
from core.forms import LoginForm

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('login/', auth_views.LoginView.as_view(
        template_name='core/login.html',
        authentication_form=LoginForm
    ), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),

    # Super Admin
    path('superadmin/', superadmin_dashboard, name='superadmin_dashboard'),
    path('superadmin/companies/new/', company_create, name='company_create'),
    path('superadmin/companies/<int:pk>/toggle/', company_toggle, name='company_toggle'),

    # Users
    path('users/', user_list, name='user_list'),
    path('users/new/', user_create, name='user_create'),
    path('users/<int:pk>/edit/', user_update, name='user_update'),
    path('users/<int:pk>/toggle/', user_toggle, name='user_toggle'),

    # Settings
    path('settings/', company_settings, name='company_settings'),
]
