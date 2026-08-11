from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Return, ReturnItem, CreditNote
from .forms import ReturnForm
from .services import generate_return_number, process_return_receipt
from customers.models import Customer
from products.models import Product
from inventory.models import Batch, Warehouse
from sales.models import Invoice


class ReturnListView(LoginRequiredMixin, ListView):
    model = Return
    template_name = 'returns/return_list.html'
    context_object_name = 'returns'
    paginate_by = 20

    def get_queryset(self):
        qs = Return.objects.filter(
            company=self.request.company
        ).select_related('customer', 'rep')

        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        customer_id = self.request.GET.get('customer', '').strip()
        reason = self.request.GET.get('reason', '').strip()

        if q:
            qs = qs.filter(
                Q(return_number__icontains=q) |
                Q(customer__pharmacy_name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if reason:
            qs = qs.filter(return_reason=reason)

        return qs.order_by('-return_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(
            company=self.request.company, is_active=True
        ).order_by('pharmacy_name')
        context['status_choices'] = Return.STATUS_CHOICES
        context['reason_choices'] = Return.REASON_CHOICES
        return context


@login_required
def return_create(request):
    company = request.company
    customer_id = request.GET.get('customer_id', '')
    selected_customer = None
    customer_invoices = []

    if customer_id:
        try:
            selected_customer = Customer.objects.get(id=customer_id, company=company)
            customer_invoices = Invoice.objects.filter(
                company=company,
                customer=selected_customer
            ).order_by('-invoice_date')
        except Customer.DoesNotExist:
            pass

    products = Product.objects.filter(company=company, is_active=True).order_by('product_name')
    batches = Batch.objects.filter(company=company, status='approved').select_related('product').order_by('product__product_name', 'expiry_date')

    if request.method == 'POST':
        form = ReturnForm(request.POST, company=company)

        if form.is_valid():
            return_order = form.save(commit=False)
            return_order.company = company
            return_order.rep = request.user
            return_order.return_number = generate_return_number(company)
            return_order.created_by = request.user
            return_order.status = 'pending'
            return_order.save()

            product_ids = request.POST.getlist('item_product_id')
            batch_ids = request.POST.getlist('item_batch_id')
            quantities = request.POST.getlist('item_quantity')
            prices = request.POST.getlist('item_price')
            conditions = request.POST.getlist('item_condition')
            dispositions = request.POST.getlist('item_disposition')

            for pid, bid, qty, price, cond, disp in zip(
                product_ids, batch_ids, quantities, prices, conditions, dispositions
            ):
                if not pid or not bid or not qty or int(qty) <= 0:
                    continue
                try:
                    ReturnItem.objects.create(
                        return_order=return_order,
                        product_id=pid,
                        batch_id=bid,
                        quantity=int(qty),
                        unit_price=float(price),
                        item_condition=cond,
                        disposition=disp,
                    )
                except Exception:
                    continue

            return_order.calculate_total()

            messages.success(request, f'تم إنشاء طلب المرتجع {return_order.return_number}')
            return redirect('returns:return_detail', pk=return_order.pk)
    else:
        initial = {}
        if selected_customer:
            initial['customer'] = selected_customer
        form = ReturnForm(company=company, initial=initial)

    customers = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')

    return render(request, 'returns/return_form.html', {
        'form': form,
        'customers': customers,
        'selected_customer': selected_customer,
        'customer_invoices': customer_invoices,
        'products': products,
        'batches': batches,
    })


class ReturnDetailView(LoginRequiredMixin, DetailView):
    model = Return
    template_name = 'returns/return_detail.html'
    context_object_name = 'return_order'

    def get_queryset(self):
        return Return.objects.filter(
            company=self.request.company
        ).select_related('customer', 'rep', 'invoice').prefetch_related('items__product', 'items__batch')


@login_required
def return_approve(request, pk):
    return_order = get_object_or_404(Return, pk=pk, company=request.company)

    if return_order.status != 'pending':
        messages.error(request, 'لا يمكن اعتماد هذا الطلب في حالته الحالية')
        return redirect('returns:return_detail', pk=pk)

    return_order.status = 'approved'
    return_order.approved_by = request.user
    return_order.approved_at = timezone.now()
    return_order.save(update_fields=['status', 'approved_by', 'approved_at', 'updated_at'])

    messages.success(request, f'تم اعتماد المرتجع {return_order.return_number}')
    return redirect('returns:return_detail', pk=pk)


@login_required
def return_reject(request, pk):
    return_order = get_object_or_404(Return, pk=pk, company=request.company)

    if return_order.status not in ['pending']:
        messages.error(request, 'لا يمكن رفض هذا الطلب')
        return redirect('returns:return_detail', pk=pk)

    return_order.status = 'rejected'
    return_order.save(update_fields=['status', 'updated_at'])

    messages.success(request, f'تم رفض المرتجع {return_order.return_number}')
    return redirect('returns:return_list')


@login_required
def return_receive(request, pk):
    return_order = get_object_or_404(Return, pk=pk, company=request.company)

    if return_order.status != 'approved':
        messages.error(request, 'يجب اعتماد المرتجع أولاً')
        return redirect('returns:return_detail', pk=pk)

    warehouses = Warehouse.objects.filter(company=request.company, is_active=True)

    if request.method == 'POST':
        warehouse_id = request.POST.get('warehouse_id')
        if not warehouse_id:
            messages.error(request, 'يجب اختيار المخزن')
            return render(request, 'returns/return_receive.html', {
                'return_order': return_order,
                'warehouses': warehouses,
            })

        warehouse = get_object_or_404(Warehouse, pk=warehouse_id, company=request.company)
        credit_note = process_return_receipt(return_order, warehouse, request.user)

        messages.success(
            request,
            f'تم استلام المرتجع وإصدار إشعار دائن {credit_note.credit_note_number} بمبلغ {credit_note.amount}'
        )
        return redirect('returns:return_detail', pk=pk)

    return render(request, 'returns/return_receive.html', {
        'return_order': return_order,
        'warehouses': warehouses,
    })


class CreditNoteListView(LoginRequiredMixin, ListView):
    model = CreditNote
    template_name = 'returns/credit_note_list.html'
    context_object_name = 'credit_notes'
    paginate_by = 20

    def get_queryset(self):
        return CreditNote.objects.filter(
            company=self.request.company
        ).select_related('customer', 'return_order').order_by('-created_at')
