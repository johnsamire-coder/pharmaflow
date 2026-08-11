from django.db import models
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel, Company, User
from products.models import Product


class Factory(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='factories')
    factory_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'factories'
        ordering = ['factory_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'factory_name'], name='uniq_factory_per_company')
        ]

    def __str__(self):
        return self.factory_name


class Supplier(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='suppliers')
    supplier_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_suppliers')

    class Meta:
        db_table = 'suppliers'
        ordering = ['supplier_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'supplier_name'], name='uniq_supplier_per_company')
        ]

    def __str__(self):
        return self.supplier_name


class ManufacturingOrder(TimeStampedModel):
    STATUS_CHOICES = [
        ('draft', 'مسودة'),
        ('approved', 'معتمد'),
        ('in_production', 'جاري التصنيع'),
        ('completed', 'مكتمل'),
        ('cancelled', 'ملغي'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='manufacturing_orders')
    order_number = models.CharField(max_length=20)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='manufacturing_orders')
    factory = models.ForeignKey(Factory, on_delete=models.PROTECT, related_name='manufacturing_orders')
    quantity_requested = models.IntegerField(validators=[MinValueValidator(1)])
    order_date = models.DateField()
    expected_delivery = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_manufacturing_orders')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_manufacturing_orders')

    class Meta:
        db_table = 'manufacturing_orders'
        ordering = ['-order_date', '-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'order_number'], name='uniq_manufacturing_order_per_company')
        ]

    def __str__(self):
        return f"{self.order_number} - {self.product.product_name}"

    @property
    def total_manufacturing_cost(self):
        return sum(p.amount for p in self.payments.all())

    @property
    def total_materials_cost(self):
        return sum((m.cost or 0) + (m.shipping_cost or 0) for m in self.materials.all())

    @property
    def total_expenses(self):
        return sum(e.amount for e in self.expenses.all())


class FactoryQuotation(TimeStampedModel):
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='quotations')
    quotation_amount = models.DecimalField(max_digits=12, decimal_places=2)
    quotation_date = models.DateField()
    attachment = models.FileField(upload_to='quotations/%Y/%m/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    is_accepted = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'factory_quotations'
        ordering = ['-quotation_date']

    def __str__(self):
        return f"{self.manufacturing_order.order_number} - {self.quotation_amount}"


class FactoryPayment(TimeStampedModel):
    PAYMENT_TYPE_CHOICES = [
        ('deposit', 'عربون'),
        ('installment', 'دفعة'),
        ('final_payment', 'سداد نهائي'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'نقدي'),
        ('bank_transfer', 'تحويل بنكي'),
        ('cheque', 'شيك'),
        ('instapay', 'إنستا باي'),
    ]

    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='payments')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHOD_CHOICES)
    reference_number = models.CharField(max_length=100, blank=True, null=True)
    attachment = models.FileField(upload_to='factory_payments/%Y/%m/', blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'factory_payments'
        ordering = ['payment_date']

    def __str__(self):
        return f"{self.get_payment_type_display()} - {self.amount}"


class ManufacturingMaterial(TimeStampedModel):
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='materials')
    material_name = models.CharField(max_length=100)
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name='materials')
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    sent_date = models.DateField(null=True, blank=True)
    is_sent = models.BooleanField(default=False)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'manufacturing_materials'
        ordering = ['material_name']

    def __str__(self):
        return f"{self.material_name} - {self.quantity}"


class ManufacturingExpense(TimeStampedModel):
    manufacturing_order = models.ForeignKey(ManufacturingOrder, on_delete=models.CASCADE, related_name='expenses')
    expense_type = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)
    attachment = models.FileField(upload_to='manufacturing_expenses/%Y/%m/', blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'manufacturing_expenses'
        ordering = ['expense_date']

    def __str__(self):
        return f"{self.expense_type} - {self.amount}"
