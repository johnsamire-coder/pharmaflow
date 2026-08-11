from django.contrib import admin
from .models import Warehouse, Batch, Inventory, InventoryMovement


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ('warehouse_name', 'company', 'manager', 'is_active')
    search_fields = ('warehouse_name',)
    list_filter = ('company', 'is_active')


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ('batch_number', 'product', 'company', 'quantity_received', 'expiry_date', 'status')
    search_fields = ('batch_number', 'product__product_name', 'product__product_code')
    list_filter = ('company', 'status', 'expiry_date')


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ('product', 'batch', 'warehouse', 'quantity_available', 'quantity_reserved', 'quantity_on_consignment')
    search_fields = ('product__product_name', 'product__product_code', 'batch__batch_number')
    list_filter = ('company', 'warehouse')


@admin.register(InventoryMovement)
class InventoryMovementAdmin(admin.ModelAdmin):
    list_display = ('movement_type', 'product', 'batch', 'warehouse', 'quantity', 'created_at')
    search_fields = ('product__product_name', 'batch__batch_number', 'reference_type', 'reference_id')
    list_filter = ('company', 'movement_type', 'warehouse')
