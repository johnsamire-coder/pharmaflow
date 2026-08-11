from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
from core.models import TimeStampedModel, Company, User
from products.models import Product
from customers.models import Customer
from inventory.models import Batch


class Consignment(TimeStampedModel):
    """
    أمر إرسال بضاعة تحت التصريف
    """
    STATUS_DRAFT = 'draft'
    STATUS_SENT = 'sent'
    STATUS_PARTIAL = 'partial_returned'
    STATUS_SETTLED = 'settled'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'مسودة'),
        (STATUS_SENT, 'مرسلة'),
        (STATUS_PARTIAL, 'مرتجع جزئي'),
        (STATUS_SETTLED, 'تمت التسوية'),
        (STATUS_CANCELLED, 'ملغية'),
    ]

    company = models.ForeignKey(
        Company, on_delete=models.CASCADE, related_name='consignments'
    )
    consignment_number = models.CharField(max_length=30)
    customer = models.ForeignKey(
        Customer, on_delete=models.PROTECT, related_name='consignments'
    )
    sent_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='sent_consignments'
    )
    sent_date = models.DateField(default=timezone.now)
    expected_return_date = models.DateField(null=True, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT
    )
    notes = models.TextField(blank=True, null=True)

    # التسوية
    settled_date = models.DateField(null=True, blank=True)
    sale = models.ForeignKey(
        'sales.Invoice', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='consignments'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'consignment_number'],
                name='uniq_consignment_per_company'
            )
        ]
        ordering = ['-sent_date', '-id']

    def __str__(self):
        return f"{self.consignment_number} - {self.customer.customer_name}"

    @property
    def total_sent_value(self):
        return sum(
            item.quantity_sent * item.unit_price
            for item in self.items.all()
        )

    @property
    def total_returned_value(self):
        return sum(
            item.quantity_returned * item.unit_price
            for item in self.items.all()
        )

    @property
    def total_sold_value(self):
        return sum(
            item.quantity_sold * item.unit_price
            for item in self.items.all()
        )

    @property
    def total_sold_quantity(self):
        return sum(item.quantity_sold for item in self.items.all())

    def get_status_badge(self):
        badges = {
            'draft': 'secondary',
            'sent': 'primary',
            'partial_returned': 'warning',
            'settled': 'success',
            'cancelled': 'danger',
        }
        return badges.get(self.status, 'secondary')


class ConsignmentItem(TimeStampedModel):
    """
    بنود أمر التصريف
    """
    consignment = models.ForeignKey(
        Consignment, on_delete=models.CASCADE, related_name='items'
    )
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name='consignment_items'
    )
    batch = models.ForeignKey(
        Batch, on_delete=models.PROTECT,
        null=True, blank=True, related_name='consignment_items'
    )
    quantity_sent = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )
    quantity_returned = models.PositiveIntegerField(default=0)
    quantity_sold = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(
        max_digits=12, decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.consignment.consignment_number} - {self.product.product_name}"

    @property
    def quantity_remaining(self):
        return self.quantity_sent - self.quantity_returned - self.quantity_sold

    @property
    def line_total_sent(self):
        return self.quantity_sent * self.unit_price

    @property
    def line_total_sold(self):
        return self.quantity_sold * self.unit_price

    def save(self, *args, **kwargs):
        # تأكد أن المجموع لا يتجاوز المرسل
        if (self.quantity_returned + self.quantity_sold) > self.quantity_sent:
            raise ValueError("المرتجع + المباع لا يمكن أن يتجاوز المرسل")
        super().save(*args, **kwargs)


class ConsignmentReturn(TimeStampedModel):
    """
    سجل مرتجعات أمر التصريف
    """
    consignment = models.ForeignKey(
        Consignment, on_delete=models.CASCADE, related_name='returns'
    )
    return_date = models.DateField(default=timezone.now)
    notes = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='received_consignment_returns'
    )

    class Meta:
        ordering = ['-return_date', '-id']

    def __str__(self):
        return f"مرتجع: {self.consignment.consignment_number} - {self.return_date}"


class ConsignmentReturnItem(TimeStampedModel):
    """
    بنود المرتجع
    """
    consignment_return = models.ForeignKey(
        ConsignmentReturn, on_delete=models.CASCADE, related_name='items'
    )
    consignment_item = models.ForeignKey(
        ConsignmentItem, on_delete=models.PROTECT, related_name='return_items'
    )
    quantity_returned = models.PositiveIntegerField(
        validators=[MinValueValidator(1)]
    )

    def __str__(self):
        return f"{self.consignment_return} - {self.consignment_item.product.product_name}"
