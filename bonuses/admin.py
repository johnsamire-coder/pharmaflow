from django.contrib import admin
from .models import BonusRule, CustomerBonusRule


@admin.register(BonusRule)
class BonusRuleAdmin(admin.ModelAdmin):
    list_display = ('product', 'company', 'bonus_type', 'buy_quantity', 'free_quantity', 'is_active')
    list_filter = ('company', 'bonus_type', 'is_active')
    search_fields = ('product__product_name', 'product__product_code')


@admin.register(CustomerBonusRule)
class CustomerBonusRuleAdmin(admin.ModelAdmin):
    list_display = ('customer', 'product', 'company', 'bonus_type', 'buy_quantity', 'free_quantity', 'is_active', 'approved_by')
    list_filter = ('company', 'bonus_type', 'is_active')
    search_fields = ('customer__pharmacy_name', 'product__product_name')
