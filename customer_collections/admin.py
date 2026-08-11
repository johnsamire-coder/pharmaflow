from django.contrib import admin
from .models import Collection, CollectionInvoice


class CollectionInvoiceInline(admin.TabularInline):
    model = CollectionInvoice
    extra = 0


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('receipt_number', 'customer', 'amount', 'payment_method', 'status', 'collection_date')
    search_fields = ('receipt_number', 'customer__pharmacy_name', 'reference_number', 'cheque_number')
    list_filter = ('company', 'payment_method', 'status', 'collection_date')
    inlines = [CollectionInvoiceInline]
