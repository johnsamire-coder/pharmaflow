from django import forms
from django.utils import timezone
from .models import Return, ReturnItem
from customers.models import Customer
from sales.models import Invoice


class ReturnForm(forms.ModelForm):
    class Meta:
        model = Return
        fields = ['customer', 'invoice', 'return_date', 'return_reason', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select', 'id': 'id_customer'}),
            'invoice': forms.Select(attrs={'class': 'form-select', 'id': 'id_invoice'}),
            'return_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'return_reason': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = Customer.objects.filter(
                company=company, is_active=True
            ).order_by('pharmacy_name')
            self.fields['invoice'].queryset = Invoice.objects.filter(
                company=company
            ).order_by('-invoice_date')
        self.fields['invoice'].required = False
        if not self.instance.pk:
            self.fields['return_date'].initial = timezone.localdate()
