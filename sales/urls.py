from django.urls import path
from . import views

app_name = 'sales'

urlpatterns = [
    path('orders/', views.SalesOrderListView.as_view(), name='order_list'),
    path('orders/new/', views.order_create, name='order_create'),
    path('orders/<int:pk>/', views.SalesOrderDetailView.as_view(), name='order_detail'),
    path('orders/<int:pk>/approve/', views.order_approve, name='order_approve'),
    path('orders/<int:pk>/reject/', views.order_reject, name='order_reject'),
    path('orders/<int:pk>/invoice/', views.order_issue_invoice, name='order_issue_invoice'),

    path('invoices/', views.InvoiceListView.as_view(), name='invoice_list'),
    path('invoices/<int:pk>/', views.InvoiceDetailView.as_view(), name='invoice_detail'),
    path('invoices/<int:pk>/print/', views.invoice_print, name='invoice_print'),
]
