from django import forms
from django.utils import timezone
from .models import Collection
from customers.models import Customer


class CollectionForm(forms.ModelForm):
    class Meta:
        model = Collection
        fields = [
            'customer', 'collection_date', 'amount',
            'payment_method', 'reference_number', 'bank_name',
            'cheque_number', 'cheque_due_date', 'due_date',
            'attachment', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select', 'id': 'id_customer'}),
            'collection_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_method': forms.Select(attrs={'class': 'form-select', 'id': 'id_payment_method', 'onchange': 'toggleFields()'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bank_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_number': forms.TextInput(attrs={'class': 'form-control'}),
            'cheque_due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
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
            self.fields['collection_date'].initial = timezone.localdate()

        self.fields['reference_number'].required = False
        self.fields['bank_name'].required = False
        self.fields['cheque_number'].required = False
        self.fields['cheque_due_date'].required = False
        self.fields['due_date'].required = False
        self.fields['attachment'].required = False
