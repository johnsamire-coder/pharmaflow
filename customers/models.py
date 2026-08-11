from django.db import models
from django.db.models import Sum
from core.models import TimeStampedModel, Company, User


class Area(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='areas')
    area_name = models.CharField(max_length=100)
    city = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'areas'
        ordering = ['area_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'area_name'], name='uniq_area_per_company')
        ]

    def __str__(self):
        return self.area_name


class Route(TimeStampedModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='routes')
    route_name = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    rep = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='routes')
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'routes'
        ordering = ['route_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'route_name'], name='uniq_route_per_company')
        ]

    def __str__(self):
        return self.route_name


class Customer(TimeStampedModel):
    PAYMENT_TYPE_CHOICES = [
        ('cash', 'نقدي'),
        ('credit', 'آجل'),
        ('consignment', 'تحت التصريف'),
    ]

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    customer_code = models.CharField(max_length=20)
    pharmacy_name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    area = models.ForeignKey(Area, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    route = models.ForeignKey(Route, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    rep = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='customers')
    tax_number = models.CharField(max_length=50, blank=True, null=True)
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    payment_days = models.IntegerField(default=0)
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES, default='cash')
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_customers')

    class Meta:
        db_table = 'customers'
        ordering = ['pharmacy_name']
        constraints = [
            models.UniqueConstraint(fields=['company', 'customer_code'], name='uniq_customer_code_per_company')
        ]

    def __str__(self):
        return f"{self.customer_code} - {self.pharmacy_name}"

    def get_balance_summary(self):
        from django.db.models import Sum

        total_invoiced = self.invoices.filter(
            status__in=['issued', 'partially_paid']
        ).aggregate(total=Sum('total_amount'))['total'] or 0

        total_paid = self.invoices.aggregate(
            total=Sum('amount_paid')
        )['total'] or 0

        total_returns = 0
        try:
            total_returns = self.returns.filter(
                status='received'
            ).aggregate(total=Sum('total_value'))['total'] or 0
        except Exception:
            pass

        balance_due = total_invoiced - total_paid - total_returns

        open_consignments = 0
        try:
            open_consignments = self.consignments.filter(
                status__in=['open', 'partially_settled']
            ).aggregate(total=Sum('total_value'))['total'] or 0
        except Exception:
            pass

        return {
            'total_invoiced': total_invoiced,
            'total_paid': total_paid,
            'total_returns': total_returns,
            'balance_due': balance_due,
            'open_consignments': open_consignments,
            'credit_limit': self.credit_limit,
            'credit_available': self.credit_limit - balance_due,
            'credit_exceeded': balance_due > self.credit_limit and self.credit_limit > 0,
        }

    def check_credit_limit(self, new_order_amount=0):
        summary = self.get_balance_summary()
        if self.payment_type == 'cash':
            return {'allowed': True, 'reason': 'عميل نقدي'}
        if self.credit_limit == 0:
            return {'allowed': True, 'reason': 'لا يوجد حد ائتمان محدد'}
        total = summary['balance_due'] + new_order_amount
        if total > self.credit_limit:
            return {
                'allowed': False,
                'reason': f'سيتجاوز حد الائتمان بمبلغ {total - self.credit_limit:.2f}',
                'exceeded_by': total - self.credit_limit,
            }
        return {'allowed': True, 'reason': 'ضمن حد الائتمان'}
