from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='reports_home'),
    path('sales/', views.sales_report, name='sales_report'),
    path('collections/', views.collections_report, name='collections_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('aging/', views.aging_report, name='aging_report'),
    path('statement/<int:customer_id>/', views.customer_statement_print, name='customer_statement_print'),
]
