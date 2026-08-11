from django import forms
from .models import Area, Route, Customer
from core.models import User


class AreaForm(forms.ModelForm):
    class Meta:
        model = Area
        fields = ['area_name', 'city', 'is_active']
        widgets = {
            'area_name': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class RouteForm(forms.ModelForm):
    class Meta:
        model = Route
        fields = ['route_name', 'area', 'rep', 'is_active']
        widgets = {
            'route_name': forms.TextInput(attrs={'class': 'form-control'}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'rep': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['area'].queryset = Area.objects.filter(company=company, is_active=True).order_by('area_name')
            self.fields['rep'].queryset = company.users.filter(is_active=True).order_by('full_name', 'username')
        self.fields['area'].required = False
        self.fields['rep'].required = False


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            'customer_code', 'pharmacy_name', 'contact_person', 'phone', 'whatsapp',
            'address', 'area', 'route', 'rep', 'tax_number',
            'credit_limit', 'payment_days', 'payment_type', 'notes', 'is_active'
        ]
        widgets = {
            'customer_code': forms.TextInput(attrs={'class': 'form-control'}),
            'pharmacy_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'area': forms.Select(attrs={'class': 'form-select'}),
            'route': forms.Select(attrs={'class': 'form-select'}),
            'rep': forms.Select(attrs={'class': 'form-select'}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control'}),
            'credit_limit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['area'].queryset = Area.objects.filter(company=company, is_active=True).order_by('area_name')
            self.fields['route'].queryset = Route.objects.filter(company=company, is_active=True).order_by('route_name')
            self.fields['rep'].queryset = company.users.filter(is_active=True).order_by('full_name', 'username')
        self.fields['area'].required = False
        self.fields['route'].required = False
        self.fields['rep'].required = False
