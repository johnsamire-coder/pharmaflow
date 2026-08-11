from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .models import Collection
from .forms import CollectionForm
from .services import (
    generate_receipt_number,
    save_collection_links,
    confirm_collection,
    recalculate_invoice,
    get_collection_default_status,
)
from customers.models import Customer
from sales.models import Invoice


def get_customer_pending_invoices(company, customer, current_collection=None):
    qs = Invoice.objects.filter(company=company, customer=customer)

    if current_collection:
        qs = qs.filter(
            Q(status__in=['issued', 'partially_paid']) |
            Q(collection_links__collection=current_collection)
        ).distinct()
    else:
        qs = qs.filter(status__in=['issued', 'partially_paid'])

    return qs.order_by('invoice_date', 'id')


class CollectionListView(LoginRequiredMixin, ListView):
    model = Collection
    template_name = 'customer_collections/collection_list.html'
    context_object_name = 'collections'
    paginate_by = 20

    def get_queryset(self):
        qs = Collection.objects.filter(
            company=self.request.company
        ).select_related('customer', 'collected_by')

        q = self.request.GET.get('q', '').strip()
        customer_id = self.request.GET.get('customer', '').strip()
        status = self.request.GET.get('status', '').strip()
        method = self.request.GET.get('method', '').strip()

        if q:
            qs = qs.filter(
                Q(receipt_number__icontains=q) |
                Q(customer__pharmacy_name__icontains=q) |
                Q(reference_number__icontains=q) |
                Q(cheque_number__icontains=q)
            )
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        if status:
            qs = qs.filter(status=status)
        if method:
            qs = qs.filter(payment_method=method)

        return qs.order_by('-collection_date', '-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['customers'] = Customer.objects.filter(
            company=self.request.company, is_active=True
        ).order_by('pharmacy_name')
        context['status_choices'] = Collection.STATUS_CHOICES
        context['method_choices'] = Collection.PAYMENT_METHOD_CHOICES
        total = Collection.objects.filter(
            company=self.request.company,
            status='confirmed'
        ).aggregate(total=Sum('amount'))['total'] or 0
        context['total_confirmed'] = total
        return context


@login_required
def collection_create(request):
    company = request.company

    customer_id = request.GET.get('customer_id', '')
    selected_customer = None
    pending_invoices = []
    current_allocations = {}

    if customer_id:
        try:
            selected_customer = Customer.objects.get(id=customer_id, company=company)
            pending_invoices = get_customer_pending_invoices(company, selected_customer)
        except Customer.DoesNotExist:
            pass

    if request.method == 'POST':
        form = CollectionForm(request.POST, request.FILES, company=company)

        if form.is_valid():
            collection = form.save(commit=False)
            collection.company = company
            collection.collected_by = request.user
            collection.receipt_number = generate_receipt_number(company)
            collection.created_by = request.user
            collection.status = get_collection_default_status(form.cleaned_data['payment_method'])
            collection.save()

            invoice_ids = request.POST.getlist('invoice_id')
            invoice_amounts = request.POST.getlist('invoice_amount')

            invoice_data = []
            for inv_id, amt in zip(invoice_ids, invoice_amounts):
                invoice_data.append({'invoice_id': inv_id, 'amount': amt})

            save_collection_links(collection, invoice_data)

            if collection.status == 'confirmed':
                collection.confirmed_by = request.user
                collection.confirmed_at = timezone.now()
                collection.save(update_fields=['confirmed_by', 'confirmed_at'])

            messages.success(request, f'تم تسجيل سند القبض {collection.receipt_number} بنجاح')
            return redirect('collections:collection_detail', pk=collection.pk)
    else:
        initial = {}
        if selected_customer:
            initial['customer'] = selected_customer
        form = CollectionForm(company=company, initial=initial)

    customers = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')

    return render(request, 'customer_collections/collection_form.html', {
        'form': form,
        'customers': customers,
        'selected_customer': selected_customer,
        'pending_invoices': pending_invoices,
        'current_allocations': current_allocations,
        'is_edit': False,
    })


@login_required
def collection_update(request, pk):
    company = request.company
    collection = get_object_or_404(Collection, pk=pk, company=company)

    if collection.status in ['bounced', 'cancelled']:
        messages.error(request, 'لا يمكن تعديل سند قبض مرتجع أو ملغي')
        return redirect('collections:collection_detail', pk=collection.pk)

    selected_customer = collection.customer
    pending_invoices = get_customer_pending_invoices(company, selected_customer, current_collection=collection)
    current_allocations = {
        link.invoice_id: link.amount_applied
        for link in collection.invoice_links.all()
    }

    if request.method == 'POST':
        form = CollectionForm(request.POST, request.FILES, instance=collection, company=company)

        if form.is_valid():
            updated = form.save(commit=False)
            updated.company = company

            if collection.status not in ['confirmed', 'bounced', 'cancelled']:
                updated.status = get_collection_default_status(form.cleaned_data['payment_method'])

            updated.save()

            invoice_ids = request.POST.getlist('invoice_id')
            invoice_amounts = request.POST.getlist('invoice_amount')

            invoice_data = []
            for inv_id, amt in zip(invoice_ids, invoice_amounts):
                invoice_data.append({'invoice_id': inv_id, 'amount': amt})

            save_collection_links(updated, invoice_data)

            messages.success(request, f'تم تعديل سند القبض {updated.receipt_number} بنجاح')
            return redirect('collections:collection_detail', pk=updated.pk)
    else:
        form = CollectionForm(instance=collection, company=company)

    customers = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')

    return render(request, 'customer_collections/collection_form.html', {
        'form': form,
        'customers': customers,
        'selected_customer': selected_customer,
        'pending_invoices': pending_invoices,
        'current_allocations': current_allocations,
        'is_edit': True,
        'collection_obj': collection,
    })


class CollectionDetailView(LoginRequiredMixin, DetailView):
    model = Collection
    template_name = 'customer_collections/collection_detail.html'
    context_object_name = 'collection'

    def get_queryset(self):
        return Collection.objects.filter(
            company=self.request.company
        ).select_related('customer', 'collected_by').prefetch_related('invoice_links__invoice')


@login_required
def collection_print(request, pk):
    collection = get_object_or_404(Collection, pk=pk, company=request.company)
    from core.models import CompanyInfo
    company_info = CompanyInfo.objects.filter(company=request.company).first()
    return render(request, 'customer_collections/receipt_print.html', {
        'collection': collection,
        'company_info': company_info,
        'invoice_links': collection.invoice_links.select_related('invoice'),
    })


@login_required
def collection_confirm(request, pk):
    collection = get_object_or_404(Collection, pk=pk, company=request.company)

    if collection.status not in ['pending', 'pending_clearance']:
        messages.warning(request, 'هذا السند ليس في حالة تحتاج تأكيد')
        return redirect('collections:collection_detail', pk=pk)

    confirm_collection(collection, request.user)
    messages.success(request, f'تم تأكيد سند القبض {collection.receipt_number}')
    return redirect('collections:collection_detail', pk=pk)


@login_required
def cheque_list(request):
    company = request.company
    qs = Collection.objects.filter(
        company=company,
        payment_method='cheque'
    ).select_related('customer').order_by('cheque_due_date')

    status = request.GET.get('status', '').strip()
    if status:
        qs = qs.filter(status=status)

    return render(request, 'customer_collections/cheque_list.html', {
        'cheques': qs,
        'status_choices': Collection.STATUS_CHOICES,
    })


@login_required
def cheque_update_status(request, pk):
    cheque = get_object_or_404(Collection, pk=pk, company=request.company, payment_method='cheque')
    new_status = request.POST.get('status')

    if new_status == 'confirmed':
        confirm_collection(cheque, request.user)
        messages.success(request, f'تم تأكيد تحصيل الشيك {cheque.cheque_number}')

    elif new_status == 'bounced':
        cheque.status = 'bounced'
        cheque.save(update_fields=['status', 'updated_at'])

        for link in cheque.invoice_links.all():
            recalculate_invoice(link.invoice)

        messages.warning(request, f'تم تسجيل الشيك {cheque.cheque_number} كمرتجع وإعادة المديونية')

    return redirect('collections:cheque_list')


@login_required
def customer_statement(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id, company=request.company)
    invoices = Invoice.objects.filter(
        company=request.company,
        customer=customer
    ).order_by('invoice_date')

    collections = Collection.objects.filter(
        company=request.company,
        customer=customer
    ).order_by('collection_date')

    balance = customer.get_balance_summary()

    return render(request, 'customer_collections/customer_statement.html', {
        'customer': customer,
        'invoices': invoices,
        'collections': collections,
        'balance': balance,
    })
