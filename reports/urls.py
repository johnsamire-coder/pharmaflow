from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_home, name='index'),

    # التقارير الأساسية
    path('sales/', views.sales_report, name='sales_report'),
    path('collections/', views.collections_report, name='collections_report'),
    path('inventory/', views.inventory_report, name='inventory_report'),
    path('customers/', views.customer_report, name='customer_report'),
    path('consignments/', views.consignments_report, name='consignments_report'),
    path('manufacturing/', views.manufacturing_report, name='manufacturing_report'),

    # تقارير جديدة
    path('customer-statement/', views.customer_statement, name='customer_statement'),
    path('gross-profit/', views.gross_profit_report, name='gross_profit'),

    # تصدير Excel
    path('export/sales/', views.export_sales_excel, name='export_sales'),
    path('export/collections/', views.export_collections_excel, name='export_collections'),
    path('export/inventory/', views.export_inventory_excel, name='export_inventory'),
    path('export/customers/', views.export_customers_excel, name='export_customers'),
    path('export/customer-statement/', views.export_customer_statement_excel, name='export_customer_statement'),
    path('export/gross-profit/', views.export_gross_profit_excel, name='export_gross_profit'),
]
