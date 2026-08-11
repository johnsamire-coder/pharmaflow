from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from .models import Warehouse, Batch, Inventory, InventoryMovement
from .forms import WarehouseForm, BatchForm


class WarehouseListView(LoginRequiredMixin, ListView):
    model = Warehouse
    template_name = 'inventory/warehouse_list.html'
    context_object_name = 'warehouses'
    paginate_by = 20

    def get_queryset(self):
        qs = Warehouse.objects.filter(company=self.request.company)
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(warehouse_name__icontains=q)

        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)

        return qs.order_by('warehouse_name')


class WarehouseCreateView(LoginRequiredMixin, CreateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse_form.html'
    success_url = reverse_lazy('inventory:warehouse_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.created_by = self.request.user
        self.object.save()
        messages.success(self.request, 'تم إنشاء المخزن بنجاح')
        return redirect(self.get_success_url())


class WarehouseUpdateView(LoginRequiredMixin, UpdateView):
    model = Warehouse
    form_class = WarehouseForm
    template_name = 'inventory/warehouse_form.html'
    success_url = reverse_lazy('inventory:warehouse_list')

    def get_queryset(self):
        return Warehouse.objects.filter(company=self.request.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل المخزن بنجاح')
        return redirect(self.get_success_url())


@require_POST
@login_required
def warehouse_toggle_status(request, pk):
    obj = get_object_or_404(Warehouse, pk=pk, company=request.company)
    obj.is_active = not obj.is_active
    obj.save()
    messages.success(request, 'تم تحديث حالة المخزن')
    return redirect('inventory:warehouse_list')


class BatchListView(LoginRequiredMixin, ListView):
    model = Batch
    template_name = 'inventory/batch_list.html'
    context_object_name = 'batches'
    paginate_by = 20

    def get_queryset(self):
        qs = Batch.objects.filter(company=self.request.company).select_related('product')
        q = self.request.GET.get('q', '').strip()
        product_id = self.request.GET.get('product', '').strip()
        status = self.request.GET.get('status', '').strip()

        if q:
            qs = qs.filter(
                Q(batch_number__icontains=q) |
                Q(product__product_name__icontains=q) |
                Q(product__product_code__icontains=q)
            )

        if product_id:
            qs = qs.filter(product_id=product_id)

        if status:
            qs = qs.filter(status=status)

        return qs.order_by('expiry_date', 'batch_number')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from products.models import Product
        context['products'] = Product.objects.filter(company=self.request.company, is_active=True).order_by('product_name')
        return context


class BatchCreateView(LoginRequiredMixin, CreateView):
    model = Batch
    form_class = BatchForm
    template_name = 'inventory/batch_form.html'
    success_url = reverse_lazy('inventory:batch_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        warehouse = form.cleaned_data['warehouse']

        self.object = form.save(commit=False)
        self.object.company = self.request.company
        self.object.created_by = self.request.user
        self.object.save()

        net_qty = max(0, self.object.quantity_received - self.object.quantity_defective)

        inventory_row, created = Inventory.objects.get_or_create(
            company=self.request.company,
            warehouse=warehouse,
            product=self.object.product,
            batch=self.object,
            defaults={
                'quantity_available': net_qty,
                'quantity_reserved': 0,
                'quantity_on_consignment': 0
            }
        )

        if not created:
            inventory_row.quantity_available += net_qty
            inventory_row.save()

        InventoryMovement.objects.create(
            company=self.request.company,
            warehouse=warehouse,
            product=self.object.product,
            batch=self.object,
            movement_type='receipt',
            quantity=net_qty,
            reference_type='batch',
            reference_id=str(self.object.id),
            notes='استلام تشغيلة جديدة',
            created_by=self.request.user
        )

        messages.success(self.request, 'تم إنشاء التشغيلة وإضافة الرصيد للمخزن')
        return redirect(self.get_success_url())


class BatchUpdateView(LoginRequiredMixin, UpdateView):
    model = Batch
    form_class = BatchForm
    template_name = 'inventory/batch_form.html'

    def get_queryset(self):
        return Batch.objects.filter(company=self.request.company)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['company'] = self.request.company
        return kwargs

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, 'تم تعديل بيانات التشغيلة')
        return redirect('inventory:batch_detail', pk=self.object.pk)


class BatchDetailView(LoginRequiredMixin, DetailView):
    model = Batch
    template_name = 'inventory/batch_detail.html'
    context_object_name = 'batch'

    def get_queryset(self):
        return Batch.objects.filter(company=self.request.company).select_related('product').prefetch_related('inventory_rows__warehouse', 'movements')


class InventoryListView(LoginRequiredMixin, ListView):
    model = Inventory
    template_name = 'inventory/inventory_list.html'
    context_object_name = 'inventory_rows'
    paginate_by = 30

    def get_queryset(self):
        qs = Inventory.objects.filter(company=self.request.company).select_related('warehouse', 'product', 'batch')
        q = self.request.GET.get('q', '').strip()
        warehouse_id = self.request.GET.get('warehouse', '').strip()
        product_id = self.request.GET.get('product', '').strip()
        stock_status = self.request.GET.get('stock_status', '').strip()

        if q:
            qs = qs.filter(
                Q(product__product_name__icontains=q) |
                Q(product__product_code__icontains=q) |
                Q(batch__batch_number__icontains=q)
            )

        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)

        if product_id:
            qs = qs.filter(product_id=product_id)

        if stock_status == 'low':
            qs = [row for row in qs if row.quantity_available <= row.product.min_stock_level]
            return qs

        return qs.order_by('product__product_name', 'batch__expiry_date')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from products.models import Product
        context['warehouses'] = Warehouse.objects.filter(company=self.request.company, is_active=True).order_by('warehouse_name')
        context['products'] = Product.objects.filter(company=self.request.company, is_active=True).order_by('product_name')
        total_qty = Inventory.objects.filter(company=self.request.company).aggregate(total=Sum('quantity_available'))['total'] or 0
        context['total_qty'] = total_qty
        return context


class InventoryMovementListView(LoginRequiredMixin, ListView):
    model = InventoryMovement
    template_name = 'inventory/movement_list.html'
    context_object_name = 'movements'
    paginate_by = 30

    def get_queryset(self):
        qs = InventoryMovement.objects.filter(company=self.request.company).select_related('warehouse', 'product', 'batch')
        q = self.request.GET.get('q', '').strip()
        warehouse_id = self.request.GET.get('warehouse', '').strip()
        movement_type = self.request.GET.get('movement_type', '').strip()

        if q:
            qs = qs.filter(
                Q(product__product_name__icontains=q) |
                Q(product__product_code__icontains=q) |
                Q(batch__batch_number__icontains=q)
            )

        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)

        if movement_type:
            qs = qs.filter(movement_type=movement_type)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['warehouses'] = Warehouse.objects.filter(company=self.request.company, is_active=True).order_by('warehouse_name')
        context['movement_types'] = InventoryMovement.MOVEMENT_TYPES
        return context
