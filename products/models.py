from django.db import models
from django.db.models import Sum
from django.core.validators import MinValueValidator
from core.models import TimeStampedModel, Company, User


class ProductCategory(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_categories')
    category_name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'product_categories'
        ordering = ['category_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'category_name'], name='uniq_category_per_company')
        ]

    def __str__(self):
        return self.category_name


class ProductFormType(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='product_forms')
    form_name = models.CharField(max_length=50)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'product_forms'
        ordering = ['form_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'form_name'], name='uniq_form_per_company')
        ]

    def __str__(self):
        return self.form_name


class Product(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='products')
    product_code = models.CharField(max_length=20)
    product_name = models.CharField(max_length=100)
    scientific_name = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    category = models.ForeignKey(ProductCategory, on_delete=models.PROTECT, related_name='products')
    form = models.ForeignKey(ProductFormType, on_delete=models.PROTECT, related_name='products')
    unit = models.CharField(max_length=30, default='علبة')
    units_per_pack = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    barcode = models.CharField(max_length=50, blank=True, null=True)
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=14.00)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    min_stock_level = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    image = models.ImageField(upload_to='products/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'products'
        ordering = ['product_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'product_code'], name='uniq_product_code_per_company')
        ]

    def __str__(self):
        return f"{self.product_code} - {self.product_name}"

    @property
    def current_stock(self):
        try:
            return self.inventory_records.aggregate(total=Sum('quantity_available'))['total'] or 0
        except Exception:
            return 0
