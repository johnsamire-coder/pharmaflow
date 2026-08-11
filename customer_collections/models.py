from django.db import models
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel, Company, User
from customers.models import Customer
from sales.models import Invoice


class Collection(TimeStampedModel):
    PAYMENT_METHOD_CHOICES = [
        ('cash_immediate', 'نقدي فوري'),
        ('cash_end_month', 'نقدي آخر الشهر'),
        ('instapay_immediate', 'إنستا باي فوري'),
        ('instapay_end_month', 'إنستا باي آخر الشهر'),
        ('fawry_immediate', 'محفظة فوري فوري'),
        ('fawry_end_month', 'محفظة فوري آخر الشهر'),
        ('bank_transfer', 'تحويل بنكي'),
        ('cheque', 'شيك'),
    ]

    STATUS_CHOICES = [
        ('confirmed', 'مؤكد'),
        ('pending', 'معلق'),
        ('pending_clearance', 'تحت التحصيل'),
        ('bounced', 'مرتجع'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='collections')
    receipt_number = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='collections')
    collected_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='collections')
    collection_date = models.DateField()
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0.01)])
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    bank_name = models.CharField(max_length=100, blank=True, null=True)
    cheque_number = models.CharField(max_length=50, blank=True, null=True)
    cheque_due_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    attachment = models.FileField(upload_to='collections/%Y/%m/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    notes = models.TextField(blank=True, null=True)
    confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_collections')
    confirmed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_collections')

    class Meta:
        db_table = 'collections'
        ordering = ['-collection_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'receipt_number'], name='uniq_receipt_number_per_company')
        ]

    def __str__(self):
        return f"{self.receipt_number} - {self.customer.pharmacy_name} - {self.amount}"


class CollectionInvoice(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name='invoice_links')
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='collection_links')
    amount_applied = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = 'collection_invoices'

    def __str__(self):
        return f"{self.collection.receipt_number} → {self.invoice.invoice_number} = {self.amount_applied}"
