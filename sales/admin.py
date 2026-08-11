from django.contrib import admin
from .models import SalesOrder, SalesOrderItem, Invoice, InvoiceItem


class SalesOrderItemInline(admin.TabularInline):
    model = SalesOrderItem
    extra = 0


@admin.register(SalesOrder)
class SalesOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer', 'company', 'total_amount', 'status', 'order_date')
    search_fields = ('order_number', 'customer__pharmacy_name')
    list_filter = ('company', 'status', 'payment_method', 'order_type')
    inlines = [SalesOrderItemInline]


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'customer', 'company', 'total_amount', 'amount_due', 'status', 'invoice_date')
    search_fields = ('invoice_number', 'customer__pharmacy_name')
    list_filter = ('company', 'status')
    inlines = [InvoiceItemInline]
