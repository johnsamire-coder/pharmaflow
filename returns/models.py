from django.db import models
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel, Company, User
from customers.models import Customer
from sales.models import Invoice
from products.models import Product
from inventory.models import Batch, Warehouse


class Return(TimeStampedModel):
    REASON_CHOICES = [
        ('near_expiry', 'قرب انتهاء صلاحية'),
        ('damaged', 'منتج تالف'),
        ('wrong_delivery', 'خطأ في التوريد'),
        ('customer_request', 'طلب العميل'),
        ('batch_recall', 'سحب تشغيلة'),
        ('other', 'أخرى'),
    ]

    STATUS_CHOICES = [
        ('pending', 'في الانتظار'),
        ('approved', 'معتمد'),
        ('received', 'مستلم بالمخزن'),
        ('rejected', 'مرفوض'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='returns')
    return_number = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='returns')
    invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='returns')
    rep = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_returns')
    return_date = models.DateField()
    return_reason = models.CharField(max_length=30, choices=REASON_CHOICES)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_returns')
    approved_at = models.DateTimeField(null=True, blank=True)
    received_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='received_returns')
    received_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='user_created_returns')

    class Meta:
        db_table = 'returns'
        ordering = ['-return_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'return_number'], name='uniq_return_number_per_company')
        ]

    def __str__(self):
        return f"{self.return_number} - {self.customer.pharmacy_name}"

    def calculate_total(self):
        total = sum(item.line_total for item in self.items.all())
        self.total_value = total
        self.save(update_fields=['total_value'])


class ReturnItem(models.Model):
    CONDITION_CHOICES = [
        ('good', 'صالح للبيع'),
        ('damaged', 'تالف'),
        ('expired', 'منتهي الصلاحية'),
    ]

    DISPOSITION_CHOICES = [
        ('return_to_stock', 'إعادة للمخزن'),
        ('destroy', 'إتلاف'),
        ('quarantine', 'حجر صحي'),
    ]

    return_order = models.ForeignKey(Return, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    item_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    disposition = models.CharField(max_length=20, choices=DISPOSITION_CHOICES, default='return_to_stock')

    class Meta:
        db_table = 'return_items'

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"


class CreditNote(TimeStampedModel):
    STATUS_CHOICES = [
        ('issued', 'صادر'),
        ('applied', 'مطبق'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='credit_notes')
    credit_note_number = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='credit_notes')
    return_order = models.OneToOneField(Return, on_delete=models.CASCADE, related_name='credit_note', null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    applied_to_invoice = models.ForeignKey(Invoice, on_delete=models.SET_NULL, null=True, blank=True, related_name='applied_credit_notes')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'credit_notes'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'credit_note_number'], name='uniq_credit_note_per_company')
        ]

    def __str__(self):
        return f"{self.credit_note_number} - {self.customer.pharmacy_name}"
