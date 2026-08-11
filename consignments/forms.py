from django import forms
from django.forms import inlineformset_factory
from .models import Consignment, ConsignmentItem, ConsignmentReturn, ConsignmentReturnItem
from products.models import Product
from customers.models import Customer
from inventory.models import Batch


class ConsignmentForm(forms.ModelForm):
    class Meta:
        model = Consignment
        fields = [
            'customer', 'sent_date', 'expected_return_date', 'notes'
        ]
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select select2'}),
            'sent_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'expected_return_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }

    def __init__(self, company=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['customer'].queryset = Customer.objects.filter(
                company=company, is_active=True
            ).order_by('customer_name')


class ConsignmentItemForm(forms.ModelForm):
    class Meta:
        model = ConsignmentItem
        fields = ['product', 'batch', 'quantity_sent', 'unit_price']
        widgets = {
            'product': forms.Select(
                attrs={'class': 'form-select product-select'}
            ),
            'batch': forms.Select(
                attrs={'class': 'form-select batch-select'}
            ),
            'quantity_sent': forms.NumberInput(
                attrs={'class': 'form-control', 'min': '1'}
            ),
            'unit_price': forms.NumberInput(
                attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}
            ),
        }

    def __init__(self, company=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if company:
            self.fields['product'].queryset = Product.objects.filter(
                company=company, is_active=True
            ).order_by('product_name')
            self.fields['batch'].queryset = Batch.objects.filter(
                company=company, status='available'
            ).order_by('expiry_date')
        self.fields['batch'].required = False


ConsignmentItemFormSet = inlineformset_factory(
    Consignment,
    ConsignmentItem,
    form=ConsignmentItemForm,
    extra=3,
    min_num=1,
    validate_min=True,
    can_delete=True,
)


class ConsignmentReturnForm(forms.ModelForm):
    class Meta:
        model = ConsignmentReturn
        fields = ['return_date', 'notes']
        widgets = {
            'return_date': forms.DateInput(
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'notes': forms.Textarea(
                attrs={'class': 'form-control', 'rows': 3}
            ),
        }


class SettleConsignmentForm(forms.Form):
    """نموذج تسوية أمر التصريف وتحويله لفاتورة"""
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        label='ملاحظات التسوية'
    )
