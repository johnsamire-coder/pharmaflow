from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    domain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Role(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='roles', null=True, blank=True)
    role_name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('company', 'role_name')

    def __str__(self):
        return self.role_name


class Permission(TimeStampedModel):
    permission_key = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.permission_key


class RolePermission(TimeStampedModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='role_permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='permission_roles')

    class Meta:
        unique_together = ('role', 'permission')

    def __str__(self):
        return f"{self.role} -> {self.permission}"


class User(AbstractUser):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='users', null=True, blank=True)
    full_name = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    is_active = models.BooleanField(default=True)
    last_login = models.DateTimeField(blank=True, null=True)
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')

    def save(self, *args, **kwargs):
        if not self.full_name:
            self.full_name = self.get_full_name() or self.username
        super().save(*args, **kwargs)

    def __str__(self):
        return self.username


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('CREATE', 'CREATE'),
        ('UPDATE', 'UPDATE'),
        ('DELETE', 'DELETE'),
        ('APPROVE', 'APPROVE'),
        ('REJECT', 'REJECT'),
        ('LOGIN', 'LOGIN'),
        ('LOGOUT', 'LOGOUT'),
        ('VIEW', 'VIEW'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='audit_logs', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    table_name = models.CharField(max_length=100)
    record_id = models.CharField(max_length=100, blank=True, null=True)
    old_values = models.JSONField(blank=True, null=True)
    new_values = models.JSONField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.action} - {self.table_name}"


class Notification(TimeStampedModel):
    TYPE_CHOICES = [
        ('expiry_warning', 'Expiry Warning'),
        ('low_stock', 'Low Stock'),
        ('credit_exceeded', 'Credit Exceeded'),
        ('cheque_due', 'Cheque Due'),
        ('cheque_bounced', 'Cheque Bounced'),
        ('order_pending', 'Order Pending'),
        ('approval_needed', 'Approval Needed'),
        ('consignment_follow_up', 'Consignment Follow Up'),
        ('target_reminder', 'Target Reminder'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField(blank=True, null=True)
    reference_table = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.title


class Attachment(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='attachments', null=True, blank=True)
    reference_table = models.CharField(max_length=50)
    reference_id = models.CharField(max_length=50)
    file_name = models.CharField(max_length=255)
    file = models.FileField(upload_to='attachments/%Y/%m/')
    file_type = models.CharField(max_length=50, blank=True, null=True)
    file_size = models.IntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.file_name


class SystemSetting(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='settings')
    setting_key = models.CharField(max_length=100)
    setting_value = models.TextField(blank=True, null=True)
    setting_type = models.CharField(max_length=20, default='string')
    description = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        unique_together = ('company', 'setting_key')

    def __str__(self):
        return f"{self.company} - {self.setting_key}"


class CompanyInfo(TimeStampedModel):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name='info')
    company_name = models.CharField(max_length=200)
    company_name_en = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    fax = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    website = models.CharField(max_length=200, blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    commercial_register = models.CharField(max_length=50, blank=True, null=True)
    logo = models.ImageField(upload_to='logos/', blank=True, null=True)
    stamp = models.ImageField(upload_to='stamps/', blank=True, null=True)
    invoice_notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.company_name


# ===========================
# User Profile (Role System)
# ===========================
class UserProfile(TimeStampedModel):
    ROLE_CHOICES = [
        ('admin',         'مدير'),
        ('sales_manager', 'مدير مبيعات'),
        ('sales_rep',     'مندوب مبيعات'),
        ('warehouse',     'أمين مخزن'),
        ('accountant',    'محاسب'),
        ('viewer',        'مشاهد'),
    ]

    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name='user_profiles'
    )
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    role = models.CharField(
        max_length=30,
        choices=ROLE_CHOICES,
        default='sales_rep'
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = [('company', 'user')]

    def __str__(self):
        return f"{self.user.username} - {self.get_role_display()}"

    def get_role_color(self):
        from core.roles import get_role_color
        return get_role_color(self.role)

    def has_permission(self, permission):
        from core.roles import user_has_permission
        return user_has_permission(self.user, permission)
