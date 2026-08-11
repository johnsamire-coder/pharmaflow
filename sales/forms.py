from django import forms
from django.utils import timezone
from .models import SalesOrder, SalesOrderItem
from customers.models import Customer
from products.models import Product


class SalesOrderForm(forms.ModelForm):
    class Meta:
        model = SalesOrder
        fields = ['customer', 'order_date', 'order_type', 'payment_method', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'order_type': forms.Select(attrs={'class': 'form-select'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = Customer.objects.filter(
                company=company, is_active=True
            ).order_by('pharmacy_name')
        if not self.instance.pk:
            self.fields['order_date'].initial = timezone.localdate()
