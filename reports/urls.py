from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='index'),
    path('sales/', views.sales_report, name='sales_report'),
    path('collections/', views.collections_report, name='collections_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('customers/', views.customer_report, name='customer_report'),
    path('consignments/', views.consignments_report, name='consignments_report'),
    path('manufacturing/', views.manufacturing_report, name='manufacturing_report'),

    # Excel Exports
    path('export/sales/', views.export_sales_excel, name='export_sales'),
    path('export/collections/', views.export_collections_excel, name='export_collections'),
    path('export/inventory/', views.export_inventory_excel, name='export_inventory'),
    path('export/customers/', views.export_customers_excel, name='export_customers'),
]
