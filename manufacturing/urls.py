from django.urls import path
from . import views

app_name = 'manufacturing'

urlpatterns = [
    path('', views.ManufacturingOrderListView.as_view(), name='order_list'),
    path('new/', views.manufacturing_order_create, name='order_create'),
    path('<int:pk>/', views.ManufacturingOrderDetailView.as_view(), name='order_detail'),
    path('<int:pk>/approve/', views.order_approve, name='order_approve'),
    path('<int:pk>/start/', views.order_start_production, name='order_start'),
    path('<int:pk>/quotation/', views.add_quotation, name='add_quotation'),
    path('<int:pk>/payment/', views.add_payment, name='add_payment'),
    path('<int:pk>/material/', views.add_material, name='add_material'),
    path('<int:pk>/expense/', views.add_expense, name='add_expense'),
    path('<int:pk>/receive/', views.receive_batch, name='receive_batch'),

    path('factories/', views.FactoryListView.as_view(), name='factory_list'),
    path('factories/new/', views.factory_create, name='factory_create'),
    path('factories/<int:pk>/edit/', views.factory_update, name='factory_update'),

    path('suppliers/', views.SupplierListView.as_view(), name='supplier_list'),
    path('suppliers/new/', views.supplier_create, name='supplier_create'),
    path('suppliers/<int:pk>/edit/', views.supplier_update, name='supplier_update'),
]
