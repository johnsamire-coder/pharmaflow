from django.contrib import admin
from .models import ProductCategory, ProductFormType, Product


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('category_name', 'company', 'is_active', 'created_at')
    search_fields = ('category_name',)
    list_filter = ('company', 'is_active')


@admin.register(ProductFormType)
class ProductFormTypeAdmin(admin.ModelAdmin):
    list_display = ('form_name', 'company', 'is_active', 'created_at')
    search_fields = ('form_name',)
    list_filter = ('company', 'is_active')


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('product_code', 'product_name', 'company', 'category', 'form', 'selling_price', 'is_active')
    search_fields = ('product_code', 'product_name', 'barcode')
    list_filter = ('company', 'category', 'form', 'is_active')
