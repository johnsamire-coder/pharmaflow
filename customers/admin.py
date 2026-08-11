from django.contrib import admin
from .models import Area, Route, Customer


@admin.register(Area)
class AreaAdmin(admin.ModelAdmin):
    list_display = ('area_name', 'city', 'company', 'is_active')
    search_fields = ('area_name', 'city')
    list_filter = ('company', 'is_active')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('route_name', 'area', 'rep', 'company', 'is_active')
    search_fields = ('route_name',)
    list_filter = ('company', 'area', 'is_active')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('customer_code', 'pharmacy_name', 'company', 'area', 'rep', 'payment_type', 'is_active')
    search_fields = ('customer_code', 'pharmacy_name', 'phone')
    list_filter = ('company', 'area', 'payment_type', 'is_active')
