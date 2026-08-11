from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Factory, Supplier, ManufacturingOrder, FactoryQuotation, FactoryPayment, ManufacturingMaterial, ManufacturingExpense
from .forms import (
    FactoryForm, SupplierForm, ManufacturingOrderForm,
    FactoryQuotationForm, FactoryPaymentForm,
    ManufacturingMaterialForm, ManufacturingExpenseForm,
    BatchReceiveForm
)
from .services import generate_order_number, calculate_batch_cost


# ============================
# Factory
# ============================
class FactoryListView(LoginRequiredMixin, ListView):
    model = Factory
    template_name = 'manufacturing/factory_list.html'
    context_object_name = 'factories'
    paginate_by = 20

    def get_queryset(self):
        qs = Factory.objects.filter(company=self.request.company)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(factory_name__icontains=q)
        return qs.order_by('factory_name')


@login_required
def factory_create(request):
    company = request.company
    if request.method == 'POST':
        form = FactoryForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إنشاء المصنع بنجاح')
            return redirect('manufacturing:factory_list')
    else:
        form = FactoryForm()
    return render(request, 'manufacturing/factory_form.html', {'form': form, 'title': 'مصنع جديد'})


@login_required
def factory_update(request, pk):
    company = request.company
    obj = get_object_or_404(Factory, pk=pk, company=company)
    if request.method == 'POST':
        form = FactoryForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل المصنع')
            return redirect('manufacturing:factory_list')
    else:
        form = FactoryForm(instance=obj)
    return render(request, 'manufacturing/factory_form.html', {'form': form, 'title': f'تعديل: {obj.factory_name}'})


# ============================
# Supplier
# ============================
class SupplierListView(LoginRequiredMixin, ListView):
    model = Supplier
    template_name = 'manufacturing/supplier_list.html'
    context_object_name = 'suppliers'
    paginate_by = 20

    def get_queryset(self):
        qs = Supplier.objects.filter(company=self.request.company)
        q = self.request.GET.get('q', '').strip()
        if q:
            qs = qs.filter(supplier_name__icontains=q)
        return qs.order_by('supplier_name')


@login_required
def supplier_create(request):
    company = request.company
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إنشاء المورد بنجاح')
            return redirect('manufacturing:supplier_list')
    else:
        form = SupplierForm()
    return render(request, 'manufacturing/supplier_form.html', {'form': form, 'title': 'مورد جديد'})


@login_required
def supplier_update(request, pk):
    company = request.company
    obj = get_object_or_404(Supplier, pk=pk, company=company)
    if request.method == 'POST':
        form = SupplierForm(request.POST, instance=obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل المورد')
            return redirect('manufacturing:supplier_list')
    else:
        form = SupplierForm(instance=obj)
    return render(request, 'manufacturing/supplier_form.html', {'form': form, 'title': f'تعديل: {obj.supplier_name}'})


# ============================
# Manufacturing Order
# ============================
class ManufacturingOrderListView(LoginRequiredMixin, ListView):
    model = ManufacturingOrder
    template_name = 'manufacturing/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = ManufacturingOrder.objects.filter(company=self.request.company).select_related('product', 'factory')
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        if q:
            qs = qs.filter(Q(order_number__icontains=q) | Q(product__product_name__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs.order_by('-order_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = ManufacturingOrder.STATUS_CHOICES
        return context


@login_required
def manufacturing_order_create(request):
    company = request.company
    if request.method == 'POST':
        form = ManufacturingOrderForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.created_by = request.user
            obj.order_number = generate_order_number(company)
            obj.status = 'draft'
            obj.save()
            messages.success(request, f'تم إنشاء أمر التصنيع {obj.order_number}')
            return redirect('manufacturing:order_detail', pk=obj.pk)
    else:
        form = ManufacturingOrderForm(company=company)
    return render(request, 'manufacturing/order_form.html', {'form': form})


class ManufacturingOrderDetailView(LoginRequiredMixin, DetailView):
    model = ManufacturingOrder
    template_name = 'manufacturing/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return ManufacturingOrder.objects.filter(
            company=self.request.company
        ).select_related('product', 'factory').prefetch_related(
            'quotations', 'payments', 'materials__supplier', 'expenses'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order = self.object
        context['quotation_form'] = FactoryQuotationForm()
        context['payment_form'] = FactoryPaymentForm()
        context['material_form'] = ManufacturingMaterialForm(company=self.request.company)
        context['expense_form'] = ManufacturingExpenseForm()
        context['batch_form'] = BatchReceiveForm(company=self.request.company)

        cost = calculate_batch_cost(order, order.quantity_requested, 0)
        context['estimated_cost'] = cost
        return context


@login_required
def order_approve(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)
    if order.status != 'draft':
        messages.error(request, 'لا يمكن اعتماد هذا الأمر في حالته الحالية')
        return redirect('manufacturing:order_detail', pk=pk)
    order.status = 'approved'
    order.approved_by = request.user
    order.approved_at = timezone.now()
    order.save()
    messages.success(request, f'تم اعتماد أمر التصنيع {order.order_number}')
    return redirect('manufacturing:order_detail', pk=pk)


@login_required
def order_start_production(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)
    if order.status != 'approved':
        messages.error(request, 'يجب اعتماد الأمر أولاً')
        return redirect('manufacturing:order_detail', pk=pk)
    order.status = 'in_production'
    order.save()
    messages.success(request, 'تم تغيير الحالة إلى جاري التصنيع')
    return redirect('manufacturing:order_detail', pk=pk)


@login_required
def add_quotation(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)
    if request.method == 'POST':
        form = FactoryQuotationForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.manufacturing_order = order
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إضافة عرض السعر')
    return redirect('manufacturing:order_detail', pk=pk)


@login_required
def add_payment(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)
    if request.method == 'POST':
        form = FactoryPaymentForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.manufacturing_order = order
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إضافة الدفعة')
    return redirect('manufacturing:order_detail', pk=pk)


@login_required
def add_material(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)
    if request.method == 'POST':
        form = ManufacturingMaterialForm(request.POST, company=request.company)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.manufacturing_order = order
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إضافة المادة')
    return redirect('manufacturing:order_detail', pk=pk)


@login_required
def add_expense(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)
    if request.method == 'POST':
        form = ManufacturingExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.manufacturing_order = order
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إضافة المصروف')
    return redirect('manufacturing:order_detail', pk=pk)


@login_required
def receive_batch(request, pk):
    order = get_object_or_404(ManufacturingOrder, pk=pk, company=request.company)

    if order.status not in ['in_production', 'approved']:
        messages.error(request, 'الأمر يجب أن يكون جاري التصنيع أو معتمداً')
        return redirect('manufacturing:order_detail', pk=pk)

    if request.method == 'POST':
        form = BatchReceiveForm(request.POST, company=request.company)
        if form.is_valid():
            data = form.cleaned_data
            company = request.company

            cost_data = calculate_batch_cost(
                order,
                data['quantity_received'],
                data['shipping_to_warehouse'],
                tax_rate=14
            )

            from inventory.models import Batch, Inventory, InventoryMovement

            if Batch.objects.filter(company=company, batch_number=data['batch_number']).exists():
                messages.error(request, f"رقم التشغيلة {data['batch_number']} موجود بالفعل")
                return redirect('manufacturing:order_detail', pk=pk)

            batch = Batch.objects.create(
                company=company,
                product=order.product,
                batch_number=data['batch_number'],
                quantity_received=data['quantity_received'],
                quantity_defective=data['quantity_defective'],
                production_date=data['production_date'],
                expiry_date=data['expiry_date'],
                received_date=data['received_date'],
                unit_cost=cost_data['unit_cost'],
                status=data['status'],
                created_by=request.user,
            )

            net_qty = max(0, data['quantity_received'] - data['quantity_defective'])
            warehouse = data['warehouse']

            inv_row, _ = Inventory.objects.get_or_create(
                company=company,
                warehouse=warehouse,
                product=order.product,
                batch=batch,
                defaults={
                    'quantity_available': net_qty,
                    'quantity_reserved': 0,
                    'quantity_on_consignment': 0,
                }
            )

            InventoryMovement.objects.create(
                company=company,
                warehouse=warehouse,
                product=order.product,
                batch=batch,
                movement_type='receipt',
                quantity=net_qty,
                reference_type='manufacturing_orders',
                reference_id=str(order.id),
                notes=f'استلام من أمر التصنيع {order.order_number}',
                created_by=request.user,
            )

            order.status = 'completed'
            order.save(update_fields=['status', 'updated_at'])

            try:
                from notifications.services import send_notification_to_managers
                send_notification_to_managers(
                    company=company,
                    notification_type='approval_needed',
                    title=f'تم استلام تشغيلة {batch.batch_number}',
                    message=f'منتج: {order.product.product_name} - كمية: {net_qty} - تكلفة الوحدة: {cost_data["unit_cost"]:.4f}',
                    reference_table='batches',
                    reference_id=batch.id,
                )
            except Exception:
                pass

            messages.success(
                request,
                f'تم استلام التشغيلة {batch.batch_number} بنجاح. تكلفة الوحدة: {cost_data["unit_cost"]:.4f} جنيه'
            )
            return redirect('manufacturing:order_detail', pk=pk)

    return redirect('manufacturing:order_detail', pk=pk)
