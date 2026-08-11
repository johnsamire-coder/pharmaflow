from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    Company, Role, Permission, RolePermission, User,
    AuditLog, Notification, Attachment, SystemSetting, CompanyInfo
)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'domain', 'is_active', 'created_at')
    search_fields = ('name', 'slug', 'domain')
    list_filter = ('is_active',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('role_name', 'company', 'created_at')
    search_fields = ('role_name',)
    list_filter = ('company',)


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('permission_key', 'description')
    search_fields = ('permission_key',)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('role', 'permission', 'created_at')
    list_filter = ('role',)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'full_name', 'company', 'role', 'is_staff', 'is_active')
    list_filter = ('company', 'role', 'is_staff', 'is_active')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('PharmaFlow', {'fields': ('full_name', 'phone', 'company', 'role', 'created_by')}),
    )


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'table_name', 'record_id', 'user', 'company', 'created_at')
    list_filter = ('action', 'company', 'created_at')
    search_fields = ('table_name', 'record_id')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'company', 'notification_type', 'is_read', 'created_at')
    list_filter = ('company', 'notification_type', 'is_read')


@admin.register(Attachment)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = ('file_name', 'reference_table', 'reference_id', 'company', 'uploaded_by', 'created_at')


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('company', 'setting_key', 'setting_type', 'updated_at')
    list_filter = ('company', 'setting_type')


@admin.register(CompanyInfo)
class CompanyInfoAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'company', 'phone', 'email')
