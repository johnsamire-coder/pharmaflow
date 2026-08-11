from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from django.utils import timezone
from core.models import TimeStampedModel, Company, User
from products.models import Product


class Warehouse(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='warehouses')
    warehouse_name = models.CharField(max_length=100)
    address = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_warehouses')
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_warehouses')

    class Meta:
        db_table = 'warehouses'
        ordering = ['warehouse_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'warehouse_name'], name='uniq_warehouse_per_company')
        ]

    def __str__(self):
        return self.warehouse_name


class Batch(TimeStampedModel):
    STATUS_CHOICES = [
        ('received', 'مستلمة'),
        ('approved', 'معتمدة للبيع'),
        ('held', 'محجوزة'),
        ('expired', 'منتهية'),
        ('depleted', 'نفدت'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='batches')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=30)
    quantity_received = models.IntegerField(validators=[MinValueValidator(0)])
    quantity_defective = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    production_date = models.DateField()
    expiry_date = models.DateField()
    received_date = models.DateField(default=timezone.now)
    unit_cost = models.DecimalField(max_digits=10, decimal_places=4, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='approved')
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_batches')

    class Meta:
        db_table = 'batches'
        ordering = ['expiry_date', 'batch_number']
        constraints = [
            models.UniqueConstraint(fields=['company', 'batch_number'], name='uniq_batch_number_per_company')
        ]

    def __str__(self):
        return f"{self.batch_number} - {self.product.product_name}"

    @property
    def quantity_available_total(self):
        return self.inventory_rows.aggregate(total=Sum('quantity_available'))['total'] or 0

    @property
    def is_near_expiry(self):
        if not self.expiry_date:
            return False
        return (self.expiry_date - timezone.localdate()).days <= 90


class Inventory(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='inventory_rows')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_records')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='inventory_rows')
    quantity_available = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    quantity_reserved = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    quantity_on_consignment = models.IntegerField(default=0, validators=[MinValueValidator(0)])

    class Meta:
        db_table = 'inventory'
        ordering = ['product__product_name', 'batch__expiry_date']
        constraints = [
            models.UniqueConstraint(fields=['company', 'warehouse', 'product', 'batch'], name='uniq_inventory_row_per_company')
        ]

    def __str__(self):
        return f"{self.product.product_name} - {self.batch.batch_number} - {self.warehouse.warehouse_name}"


class InventoryMovement(TimeStampedModel):
    MOVEMENT_TYPES = [
        ('receipt', 'استلام'),
        ('sale', 'صرف بيع'),
        ('bonus', 'صرف بونص'),
        ('consignment_out', 'صرف عهدة'),
        ('consignment_return', 'مرتجع عهدة'),
        ('customer_return', 'مرتجع عميل'),
        ('damage', 'إتلاف'),
        ('adjustment_in', 'تسوية إضافة'),
        ('adjustment_out', 'تسوية نقص'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='inventory_movements')
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='movements')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='inventory_movements')
    batch = models.ForeignKey(Batch, on_delete=models.CASCADE, related_name='movements')
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='inventory_movements_created')

    class Meta:
        db_table = 'inventory_movements'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_movement_type_display()} - {self.product.product_name} - {self.quantity}"
