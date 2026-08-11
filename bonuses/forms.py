from django import forms
from .models import BonusRule, CustomerBonusRule
from products.models import Product
from customers.models import Customer


class BonusRuleForm(forms.ModelForm):
    class Meta:
        model = BonusRule
        fields = [
            'product', 'bonus_type', 'buy_quantity', 'free_quantity',
            'discount_percentage', 'start_date', 'end_date', 'is_active'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'bonus_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleBonusFields()'}),
            'buy_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'free_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['product'].queryset = Product.objects.filter(company=company, is_active=True).order_by('product_name')


class CustomerBonusRuleForm(forms.ModelForm):
    class Meta:
        model = CustomerBonusRule
        fields = [
            'customer', 'product', 'bonus_type', 'buy_quantity', 'free_quantity',
            'discount_percentage', 'start_date', 'end_date', 'notes', 'is_active'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
            'product': forms.Select(attrs={'class': 'form-select'}),
            'bonus_type': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleBonusFields()'}),
            'buy_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'free_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'discount_percentage': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': 0}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')
            self.fields['product'].queryset = Product.objects.filter(company=company, is_active=True).order_by('product_name')
