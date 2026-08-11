from django import forms
from django.utils import timezone
from .models import (
    Factory, Supplier, ManufacturingOrder,
    FactoryQuotation, FactoryPayment,
    ManufacturingMaterial, ManufacturingExpense
)
from products.models import Product


class FactoryForm(forms.ModelForm):
    class Meta:
        model = Factory
        fields = ['factory_name', 'contact_person', 'phone', 'address', 'tax_number', 'notes', 'is_active']
        widgets = {
            'factory_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_name', 'contact_person', 'phone', 'address', 'tax_number', 'notes', 'is_active']
        widgets = {
            'supplier_name': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tax_number': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ManufacturingOrderForm(forms.ModelForm):
    class Meta:
        model = ManufacturingOrder
        fields = ['product', 'factory', 'quantity_requested', 'order_date', 'expected_delivery', 'notes']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select'}),
            'factory': forms.Select(attrs={'class': 'form-select'}),
            'quantity_requested': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'order_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expected_delivery': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['product'].queryset = Product.objects.filter(company=company, is_active=True).order_by('product_name')
            self.fields['factory'].queryset = Factory.objects.filter(company=company, is_active=True).order_by('factory_name')
        if not self.instance.pk:
            self.fields['order_date'].initial = timezone.localdate()


class FactoryQuotationForm(forms.ModelForm):
    class Meta:
        model = FactoryQuotation
        fields = ['quotation_amount', 'quotation_date', 'attachment', 'notes', 'is_accepted']
        widgets = {
            'quotation_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'quotation_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_accepted': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class FactoryPaymentForm(forms.ModelForm):
    class Meta:
        model = FactoryPayment
        fields = ['payment_type', 'amount', 'payment_date', 'payment_method', 'reference_number', 'attachment', 'notes']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'payment_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'payment_method': forms.Select(attrs={'class': 'form-select'}),
            'reference_number': forms.TextInput(attrs={'class': 'form-control'}),
            'attachment': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['payment_date'].initial = timezone.localdate()


class ManufacturingMaterialForm(forms.ModelForm):
    class Meta:
        model = ManufacturingMaterial
        fields = ['material_name', 'quantity', 'cost', 'supplier', 'shipping_cost', 'sent_date', 'is_sent', 'notes']
        widgets = {
            'material_name': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'shipping_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sent_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_sent': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['supplier'].queryset = Supplier.objects.filter(company=company, is_active=True).order_by('supplier_name')
        self.fields['supplier'].required = False
        self.fields['sent_date'].required = False


class ManufacturingExpenseForm(forms.ModelForm):
    class Meta:
        model = ManufacturingExpense
        fields = ['expense_type', 'amount', 'expense_date', 'notes']
        widgets = {
            'expense_type': forms.TextInput(attrs={'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'expense_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['expense_date'].initial = timezone.localdate()


class BatchReceiveForm(forms.Form):
    batch_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='رقم التشغيلة'
    )
    quantity_received = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        label='الكمية المستلمة'
    )
    quantity_defective = forms.IntegerField(
        min_value=0,
        initial=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        label='الفاقد / العجز'
    )
    production_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='تاريخ الإنتاج'
    )
    expiry_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='تاريخ الصلاحية'
    )
    received_date = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label='تاريخ الاستلام'
    )
    shipping_to_warehouse = forms.DecimalField(
        min_value=0,
        initial=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        label='تكلفة النقل للمخزن'
    )
    warehouse = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='المخزن'
    )
    status = forms.ChoiceField(
        choices=[('approved', 'معتمدة للبيع'), ('held', 'محجوزة لفحص الجودة')],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='حالة التشغيلة',
        initial='approved'
    )

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        from inventory.models import Warehouse
        if company:
            self.fields['warehouse'].queryset = Warehouse.objects.filter(company=company, is_active=True).order_by('warehouse_name')
        from django.utils import timezone
        self.fields['received_date'].initial = timezone.localdate()
        self.fields['production_date'].initial = timezone.localdate()

    def clean(self):
        cleaned = super().clean()
        qty = cleaned.get('quantity_received') or 0
        defective = cleaned.get('quantity_defective') or 0
        if defective > qty:
            raise forms.ValidationError('الكمية التالفة لا يمكن أن تكون أكبر من الكمية المستلمة')
        return cleaned
