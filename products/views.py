from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.db.models import Q

from .models import ProductCategory, ProductFormType, Product


class CategoryListView(LoginRequiredMixin, ListView):
    model = ProductCategory
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    paginate_by = 20

    def get_queryset(self):
        qs = ProductCategory.objects.filter(company=self.request.company)
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(category_name__icontains=q)

        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        return qs.order_by('category_name')


class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = ProductCategory
    fields = ['category_name', 'description', 'is_active']
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        return form

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, 'تم إنشاء التصنيف بنجاح')
        return redirect(self.get_success_url())


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductCategory
    fields = ['category_name', 'description', 'is_active']
    template_name = 'products/category_form.html'
    success_url = reverse_lazy('products:category_list')

    def get_queryset(self):
        return ProductCategory.objects.filter(company=self.request.company)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        return form

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل التصنيف بنجاح')
        return redirect(self.get_success_url())


@require_POST
@login_required
def category_toggle_status(request, pk):
    obj = get_object_or_404(ProductCategory, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة التصنيف')
    return redirect('products:category_list')


class ProductFormTypeListView(LoginRequiredMixin, ListView):
    model = ProductFormType
    template_name = 'products/formtype_list.html'
    context_object_name = 'forms_list'
    paginate_by = 20

    def get_queryset(self):
        qs = ProductFormType.objects.filter(company=self.request.company)
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(form_name__icontains=q)

        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        return qs.order_by('form_name')


class ProductFormTypeCreateView(LoginRequiredMixin, CreateView):
    model = ProductFormType
    fields = ['form_name', 'description', 'is_active']
    template_name = 'products/formtype_form.html'
    success_url = reverse_lazy('products:formtype_list')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        return form

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, 'تم إنشاء شكل المنتج بنجاح')
        return redirect(self.get_success_url())


class ProductFormTypeUpdateView(LoginRequiredMixin, UpdateView):
    model = ProductFormType
    fields = ['form_name', 'description', 'is_active']
    template_name = 'products/formtype_form.html'
    success_url = reverse_lazy('products:formtype_list')

    def get_queryset(self):
        return ProductFormType.objects.filter(company=self.request.company)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if name == 'is_active':
                field.widget.attrs['class'] = 'form-check-input'
            else:
                field.widget.attrs['class'] = 'form-control'
        return form

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل شكل المنتج بنجاح')
        return redirect(self.get_success_url())


@require_POST
@login_required
def formtype_toggle_status(request, pk):
    obj = get_object_or_404(ProductFormType, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة شكل المنتج')
    return redirect('products:formtype_list')


from .forms import ProductModelForm


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.filter(company=self.request.company).select_related('category', 'form')
        q = self.request.GET.get('q', '').strip()
        category_id = self.request.GET.get('category', '').strip()
        form_id = self.request.GET.get('form', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(
                Q(product_code__icontains=q) |
                Q(product_name__icontains=q) |
                Q(barcode__icontains=q)
            )

        if category_id:
            qs = qs.filter(category_id=category_id)

        if form_id:
            qs = qs.filter(form_id=form_id)

        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        return qs.order_by('product_name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = ProductCategory.objects.filter(company=self.request.company).order_by('category_name')
        context['forms_list'] = ProductFormType.objects.filter(company=self.request.company).order_by('form_name')
        return context


class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductModelForm
    template_name = 'products/product_form.html'
    success_url = reverse_lazy('products:product_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, 'تم إنشاء المنتج بنجاح')
        return redirect(self.get_success_url())


class ProductUpdateView(LoginRequiredMixin, UpdateView):
    model = Product
    form_class = ProductModelForm
    template_name = 'products/product_form.html'

    def get_queryset(self):
        return Product.objects.filter(company=self.request.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل المنتج بنجاح')
        return redirect('products:product_detail', pk=self.object.pk)


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'

    def get_queryset(self):
        return Product.objects.filter(company=self.request.company).select_related('category', 'form').prefetch_related('inventory_records__warehouse', 'inventory_records__batch')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        inventory_rows = self.object.inventory_records.select_related('warehouse', 'batch').order_by('batch__expiry_date', 'warehouse__warehouse_name')
        context['inventory_rows'] = inventory_rows
        return context


@require_POST
@login_required
def product_toggle_status(request, pk):
    obj = get_object_or_404(Product, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة المنتج')
    return redirect('products:product_list')
