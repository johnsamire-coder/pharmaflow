from django.contrib import admin
from .models import Return, ReturnItem, CreditNote


class ReturnItemInline(admin.TabularInline):
    model = ReturnItem
    extra = 0


@admin.register(Return)
class ReturnAdmin(admin.ModelAdmin):
    list_display = ('return_number', 'customer', 'company', 'total_value', 'status', 'return_date')
    search_fields = ('return_number', 'customer__pharmacy_name')
    list_filter = ('company', 'status', 'return_reason')
    inlines = [ReturnItemInline]


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display = ('credit_note_number', 'customer', 'company', 'amount', 'status')
    search_fields = ('credit_note_number', 'customer__pharmacy_name')
    list_filter = ('company', 'status')
