from django.db import models
from core.models import TimeStampedModel, Company, User
from products.models import Product
from customers.models import Customer


class BonusRule(TimeStampedModel):
    BONUS_TYPE_CHOICES = [
        ('none', 'بدون بونص'),
        ('quantity', 'كمية على كمية'),
        ('percentage', 'نسبة خصم'),
        ('fixed', 'عدد ثابت'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='bonus_rules')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='bonus_rules')
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPE_CHOICES, default='none')
    buy_quantity = models.IntegerField(default=0)
    free_quantity = models.IntegerField(default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = 'bonus_rules'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.product_name} - {self.get_bonus_type_display()}"


class CustomerBonusRule(TimeStampedModel):
    BONUS_TYPE_CHOICES = [
        ('none', 'بدون بونص'),
        ('quantity', 'كمية على كمية'),
        ('percentage', 'نسبة خصم'),
        ('fixed', 'عدد ثابت'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customer_bonus_rules')
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='bonus_rules')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='customer_bonus_rules')
    bonus_type = models.CharField(max_length=20, choices=BONUS_TYPE_CHOICES, default='none')
    buy_quantity = models.IntegerField(default=0)
    free_quantity = models.IntegerField(default=0)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_bonus_rules')
    approved_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_bonus_rules')

    class Meta:
        db_table = 'customer_bonus_rules'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(fields=['company', 'customer', 'product'], name='uniq_customer_bonus_rule')
        ]

    def __str__(self):
        return f"{self.customer.pharmacy_name} - {self.product.product_name}"
