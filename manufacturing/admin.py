from django.contrib import admin
from .models import Factory, Supplier, ManufacturingOrder, FactoryQuotation, FactoryPayment, ManufacturingMaterial, ManufacturingExpense


@admin.register(Factory)
class FactoryAdmin(admin.ModelAdmin):
    list_display = ('factory_name', 'company', 'contact_person', 'phone', 'is_active')
    search_fields = ('factory_name',)
    list_filter = ('company', 'is_active')


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ('supplier_name', 'company', 'contact_person', 'phone', 'is_active')
    search_fields = ('supplier_name',)
    list_filter = ('company', 'is_active')


class FactoryPaymentInline(admin.TabularInline):
    model = FactoryPayment
    extra = 0


class ManufacturingMaterialInline(admin.TabularInline):
    model = ManufacturingMaterial
    extra = 0


class ManufacturingExpenseInline(admin.TabularInline):
    model = ManufacturingExpense
    extra = 0


@admin.register(ManufacturingOrder)
class ManufacturingOrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'product', 'factory', 'company', 'quantity_requested', 'status', 'order_date')
    search_fields = ('order_number', 'product__product_name')
    list_filter = ('company', 'status', 'factory')
    inlines = [FactoryPaymentInline, ManufacturingMaterialInline, ManufacturingExpenseInline]
