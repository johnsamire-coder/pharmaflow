from django import forms
from .models import ProductCategory, ProductFormType, Product


class ProductCategoryForm(forms.ModelForm):
    class Meta:
        model = ProductCategory
        fields = ['category_name', 'description', 'is_active']
        widgets = {
            'category_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductFormTypeForm(forms.ModelForm):
    class Meta:
        model = ProductFormType
        fields = ['form_name', 'description', 'is_active']
        widgets = {
            'form_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class ProductModelForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            'product_code', 'product_name', 'scientific_name', 'description',
            'category', 'form', 'unit', 'units_per_pack', 'barcode',
            'tax_rate', 'selling_price', 'min_stock_level', 'image', 'is_active'
        ]
        widgets = {
            'product_code': forms.TextInput(attrs={'class': 'form-control'}),
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'scientific_name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'form': forms.Select(attrs={'class': 'form-select'}),
            'unit': forms.TextInput(attrs={'class': 'form-control'}),
            'units_per_pack': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'barcode': forms.TextInput(attrs={'class': 'form-control'}),
            'tax_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'min_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)

        if company:
            self.fields['category'].queryset = ProductCategory.objects.filter(company=company).order_by('category_name')
            self.fields['form'].queryset = ProductFormType.objects.filter(company=company).order_by('form_name')
