from django.db import models
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel, Company, User
from customers.models import Customer
from products.models import Product
from inventory.models import Warehouse, Batch


class SalesOrder(TimeStampedModel):
    ORDER_TYPE_CHOICES = [
        ('regular', 'بيع عادي'),
        ('consignment', 'تحت التصريف'),
    ]

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
        ('draft', 'مسودة'),
        ('pending_approval', 'في انتظار الاعتماد'),
        ('approved', 'معتمد'),
        ('preparing', 'جاري التجهيز'),
        ('ready', 'جاهز'),
        ('delivered', 'تم التسليم'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_orders')
    order_number = models.CharField(max_length=20)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='sales_orders')
    rep = models.ForeignKey(User, on_delete=models.PROTECT, related_name='sales_orders')
    order_date = models.DateField()
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='regular')
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES, default='cash_immediate')
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    bonus_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_orders')
    approved_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_orders')

    class Meta:
        db_table = 'sales_orders'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'order_number'], name='uniq_order_number_per_company')
        ]

    def __str__(self):
        return f"{self.order_number} - {self.customer.pharmacy_name}"

    def calculate_totals(self):
        items = self.items.all()
        subtotal = sum(item.line_total for item in items)
        bonus_value = sum(
            item.bonus_quantity * item.unit_price for item in items
        )
        tax_rate = 14
        tax_amount = subtotal * tax_rate / 100
        total = subtotal + tax_amount
        self.subtotal = subtotal
        self.tax_amount = tax_amount
        self.total_amount = total
        self.bonus_value = bonus_value
        self.save(update_fields=['subtotal', 'tax_amount', 'total_amount', 'bonus_value'])


class SalesOrderItem(TimeStampedModel):
    BONUS_SOURCE_CHOICES = [
        ('none', 'لا يوجد'),
        ('auto', 'تلقائي'),
        ('manual', 'يدوي'),
        ('customer_rule', 'قاعدة العميل'),
    ]

    sales_order = models.ForeignKey(SalesOrder, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='sales_order_items')
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    bonus_quantity = models.IntegerField(default=0)
    bonus_source = models.CharField(max_length=20, choices=BONUS_SOURCE_CHOICES, default='none')
    manual_bonus_reason = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'sales_order_items'

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"

    def save(self, *args, **kwargs):
        self.line_total = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class SalesOrderItemBatch(models.Model):
    sales_order_item = models.ForeignKey(SalesOrderItem, on_delete=models.CASCADE, related_name='batch_allocations')
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT, related_name='order_allocations')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name='order_allocations')
    quantity = models.IntegerField()
    is_bonus = models.BooleanField(default=False)

    class Meta:
        db_table = 'sales_order_item_batches'

    def __str__(self):
        return f"{self.batch.batch_number} x {self.quantity}"


class Invoice(TimeStampedModel):
    STATUS_CHOICES = [
        ('issued', 'صادرة'),
        ('partially_paid', 'مدفوعة جزئياً'),
        ('paid', 'مدفوعة'),
        ('cancelled', 'ملغاة'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=20)
    sales_order = models.OneToOneField(SalesOrder, on_delete=models.PROTECT, related_name='invoice')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    rep = models.ForeignKey(User, on_delete=models.PROTECT, related_name='invoices')
    invoice_date = models.DateField()
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=12, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='issued')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_invoices')

    class Meta:
        db_table = 'invoices'
        ordering = ['-invoice_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'invoice_number'], name='uniq_invoice_number_per_company')
        ]

    def __str__(self):
        return f"{self.invoice_number} - {self.customer.pharmacy_name}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    batch = models.ForeignKey(Batch, on_delete=models.PROTECT)
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)
    is_bonus = models.BooleanField(default=False)

    class Meta:
        db_table = 'invoice_items'

    def __str__(self):
        return f"{self.product.product_name} x {self.quantity}"
