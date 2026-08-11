from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('', views.InventoryListView.as_view(), name='inventory_list'),
    path('movements/', views.InventoryMovementListView.as_view(), name='movement_list'),

    path('warehouses/', views.WarehouseListView.as_view(), name='warehouse_list'),
    path('warehouses/new/', views.WarehouseCreateView.as_view(), name='warehouse_create'),
    path('warehouses/<int:pk>/edit/', views.WarehouseUpdateView.as_view(), name='warehouse_update'),
    path('warehouses/<int:pk>/toggle-status/', views.warehouse_toggle_status, name='warehouse_toggle_status'),

    path('batches/', views.BatchListView.as_view(), name='batch_list'),
    path('batches/new/', views.BatchCreateView.as_view(), name='batch_create'),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name='batch_detail'),
    path('batches/<int:pk>/edit/', views.BatchUpdateView.as_view(), name='batch_update'),
]
