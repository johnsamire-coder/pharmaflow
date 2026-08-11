from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    path('', views.CustomerListView.as_view(), name='customer_list'),
    path('new/', views.CustomerCreateView.as_view(), name='customer_create'),
    path('<int:pk>/', views.CustomerDetailView.as_view(), name='customer_detail'),
    path('<int:pk>/edit/', views.CustomerUpdateView.as_view(), name='customer_update'),
    path('<int:pk>/toggle-status/', views.customer_toggle_status, name='customer_toggle_status'),

    path('areas/', views.AreaListView.as_view(), name='area_list'),
    path('areas/new/', views.AreaCreateView.as_view(), name='area_create'),
    path('areas/<int:pk>/edit/', views.AreaUpdateView.as_view(), name='area_update'),
    path('areas/<int:pk>/toggle-status/', views.area_toggle_status, name='area_toggle_status'),

    path('routes/', views.RouteListView.as_view(), name='route_list'),
    path('routes/new/', views.RouteCreateView.as_view(), name='route_create'),
    path('routes/<int:pk>/edit/', views.RouteUpdateView.as_view(), name='route_update'),
    path('routes/<int:pk>/toggle-status/', views.route_toggle_status, name='route_toggle_status'),
]
