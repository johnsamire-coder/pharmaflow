from django import forms
from .models import Warehouse, Batch
from products.models import Product


class WarehouseForm(forms.ModelForm):
    class Meta:
        model = Warehouse
        fields = ['warehouse_name', 'address', 'manager', 'is_active']
        widgets = {
            'warehouse_name': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager': forms.Select(attrs={'class': 'form-select'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['manager'].queryset = company.users.filter(is_active=True).order_by('full_name', 'username')
        self.fields['manager'].required = False


class BatchForm(forms.ModelForm):
    warehouse = forms.ModelChoiceField(
        queryset=Warehouse.objects.none(),
        required=True,
        label='المخزن',
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Batch
        fields = [
            'product', 'batch_number', 'quantity_received', 'quantity_defective',
            'production_date', 'expiry_date', 'received_date',
            'unit_cost', 'status', 'notes'
        ]
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity_received': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'quantity_defective': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'production_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'received_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'unit_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.0001'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['product'].queryset = Product.objects.filter(company=company, is_active=True).order_by('product_name')
            self.fields['warehouse'].queryset = Warehouse.objects.filter(company=company, is_active=True).order_by('warehouse_name')

        if self.instance and self.instance.pk:
            self.fields['warehouse'].required = False
            self.fields['warehouse'].help_text = 'لن يتم تغيير الرصيد الحالي من هنا عند التعديل.'

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get('quantity_received') or 0
        defective = cleaned.get('quantity_defective') or 0
        if defective > qty:
            raise forms.ValidationError('الكمية التالفة لا يمكن أن تكون أكبر من الكمية المستلمة.')
        return cleaned
