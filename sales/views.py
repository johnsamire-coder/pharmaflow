from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DetailView

from .models import SalesOrder, SalesOrderItem, Invoice
from .forms import SalesOrderForm
from .services import (
    generate_order_number,
    calculate_bonus,
    issue_invoice
)
from products.models import Product
from customers.models import Customer


class SalesOrderListView(LoginRequiredMixin, ListView):
    model = SalesOrder
    template_name = 'sales/order_list.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = SalesOrder.objects.filter(company=self.request.company).select_related('customer', 'rep')
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        customer_id = self.request.GET.get('customer', '').strip()

        if q:
            qs = qs.filter(
                Q(order_number__icontains=q) |
                Q(customer__pharmacy_name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        return qs.order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(company=self.request.company, is_active=True).order_by('pharmacy_name')
        context['status_choices'] = SalesOrder.STATUS_CHOICES
        return context


@login_required
def order_create(request):
    company = request.company
    products = Product.objects.filter(company=company, is_active=True).order_by('product_name')

    if request.method == 'POST':
        form = SalesOrderForm(request.POST, company=company)

        if form.is_valid():
            order = form.save(commit=False)
            order.company = company
            order.rep = request.user
            order.order_number = generate_order_number(company)
            order.created_by = request.user
            order.status = 'pending_approval'
            order.save()

            product_ids = request.POST.getlist('product_id')
            quantities = request.POST.getlist('quantity')
            prices = request.POST.getlist('unit_price')

            for pid, qty, price in zip(product_ids, quantities, prices):
                if not pid or not qty or int(qty) <= 0:
                    continue
                try:
                    product = Product.objects.get(id=pid, company=company)
                    qty = int(qty)
                    price = float(price)

                    bonus_data = calculate_bonus(company, order.customer, product, qty)

                    SalesOrderItem.objects.create(
                        sales_order=order,
                        product=product,
                        quantity=qty,
                        unit_price=price,
                        line_total=qty * price,
                        bonus_quantity=bonus_data['bonus_quantity'],
                        bonus_source=bonus_data['bonus_source'],
                    )
                except Exception as e:
                    continue

            order.calculate_totals()
            messages.success(request, f'تم إنشاء الأوردر {order.order_number} بنجاح')
            return redirect('sales:order_detail', pk=order.pk)
    else:
        form = SalesOrderForm(company=company)

    return render(request, 'sales/order_form.html', {
        'form': form,
        'products': products,
    })


class SalesOrderDetailView(LoginRequiredMixin, DetailView):
    model = SalesOrder
    template_name = 'sales/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return SalesOrder.objects.filter(company=self.request.company).select_related('customer', 'rep').prefetch_related('items__product')


@login_required
def order_approve(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk, company=request.company)
    if order.status != 'pending_approval':
        messages.error(request, 'لا يمكن اعتماد هذا الأوردر في حالته الحالية')
        return redirect('sales:order_detail', pk=pk)

    order.status = 'approved'
    order.approved_by = request.user
    order.approved_at = timezone.now()
    order.save()

    try:
        from notifications.services import send_notification
        send_notification(
            company=order.company,
            user=order.created_by or order.rep,
            notification_type='order_pending',
            title=f'تم اعتماد الأوردر {order.order_number}',
            message=f'الأوردر للعميل {order.customer.pharmacy_name} تم اعتماده',
            reference_table='sales_orders',
            reference_id=order.id,
        )
    except Exception:
        pass

    messages.success(request, f'تم اعتماد الأوردر {order.order_number}')
    return redirect('sales:order_detail', pk=pk)


@login_required
def order_reject(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk, company=request.company)
    if order.status not in ['pending_approval', 'approved']:
        messages.error(request, 'لا يمكن رفض هذا الأوردر')
        return redirect('sales:order_detail', pk=pk)

    order.status = 'cancelled'
    order.save()
    messages.success(request, f'تم إلغاء الأوردر {order.order_number}')
    return redirect('sales:order_list')


@login_required
def order_issue_invoice(request, pk):
    order = get_object_or_404(SalesOrder, pk=pk, company=request.company)

    if order.status not in ['approved', 'preparing', 'ready']:
        messages.error(request, 'الأوردر يجب أن يكون معتمداً لإصدار الفاتورة')
        return redirect('sales:order_detail', pk=pk)

    if hasattr(order, 'invoice'):
        messages.warning(request, 'تم إصدار الفاتورة بالفعل')
        return redirect('sales:invoice_detail', pk=order.invoice.pk)

    try:
        invoice = issue_invoice(order, request.user)
        messages.success(request, f'تم إصدار الفاتورة {invoice.invoice_number} بنجاح')
        return redirect('sales:invoice_detail', pk=invoice.pk)
    except Exception as e:
        messages.error(request, f'خطأ في إصدار الفاتورة: {str(e)}')
        return redirect('sales:order_detail', pk=pk)


class InvoiceListView(LoginRequiredMixin, ListView):
    model = Invoice
    template_name = 'sales/invoice_list.html'
    context_object_name = 'invoices'
    paginate_by = 20

    def get_queryset(self):
        qs = Invoice.objects.filter(company=self.request.company).select_related('customer', 'rep')
        q = self.request.GET.get('q', '').strip()
        status = self.request.GET.get('status', '').strip()
        customer_id = self.request.GET.get('customer', '').strip()

        if q:
            qs = qs.filter(
                Q(invoice_number__icontains=q) |
                Q(customer__pharmacy_name__icontains=q)
            )
        if status:
            qs = qs.filter(status=status)
        if customer_id:
            qs = qs.filter(customer_id=customer_id)

        return qs.order_by('-invoice_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(company=self.request.company, is_active=True).order_by('pharmacy_name')
        context['status_choices'] = Invoice.STATUS_CHOICES
        return context


class InvoiceDetailView(LoginRequiredMixin, DetailView):
    model = Invoice
    template_name = 'sales/invoice_detail.html'
    context_object_name = 'invoice'

    def get_queryset(self):
        return Invoice.objects.filter(company=self.request.company).select_related('customer', 'rep', 'sales_order').prefetch_related('items__product', 'items__batch')


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, company=request.company)
    invoice_items = invoice.items.select_related('product', 'batch').order_by('product__product_name', 'is_bonus')

    from core.models import CompanyInfo
    company_info = CompanyInfo.objects.filter(company=request.company).first()

    return render(request, 'sales/invoice_print.html', {
        'invoice': invoice,
        'invoice_items': invoice_items,
        'company_info': company_info,
    })
