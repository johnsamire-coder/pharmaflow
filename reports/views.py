from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import date, timedelta

from sales.models import Invoice, InvoiceItem, SalesOrder
from customer_collections.models import Collection
from inventory.models import Inventory, Batch, InventoryMovement
from customers.models import Customer
from products.models import Product
from returns.models import Return


def get_date_range(request):
    today = timezone.localdate()
    date_from = request.GET.get('date_from', today.replace(day=1).isoformat())
    date_to = request.GET.get('date_to', today.isoformat())
    try:
        date_from = date.fromisoformat(date_from)
        date_to = date.fromisoformat(date_to)
    except Exception:
        date_from = today.replace(day=1)
        date_to = today
    return date_from, date_to


@login_required
def reports_home(request):
    return render(request, 'reports/home.html', {})


@login_required
def sales_report(request):
    company = request.company
    date_from, date_to = get_date_range(request)

    customer_id = request.GET.get('customer', '').strip()
    product_id = request.GET.get('product', '').strip()
    rep_id = request.GET.get('rep', '').strip()

    invoices = Invoice.objects.filter(
        company=company,
        invoice_date__gte=date_from,
        invoice_date__lte=date_to,
    ).select_related('customer', 'rep')

    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)
    if rep_id:
        invoices = invoices.filter(rep_id=rep_id)

    totals = invoices.aggregate(
        total_sales=Sum('total_amount'),
        total_tax=Sum('tax_amount'),
        total_paid=Sum('amount_paid'),
        total_due=Sum('amount_due'),
        count=Count('id'),
    )

    by_customer = invoices.values(
        'customer__pharmacy_name'
    ).annotate(
        total=Sum('total_amount'),
        count=Count('id'),
        paid=Sum('amount_paid'),
        due=Sum('amount_due'),
    ).order_by('-total')[:20]

    by_product = InvoiceItem.objects.filter(
        invoice__company=company,
        invoice__invoice_date__gte=date_from,
        invoice__invoice_date__lte=date_to,
        is_bonus=False,
    ).values(
        'product__product_name',
        'product__product_code',
    ).annotate(
        total_qty=Sum('quantity'),
        total_value=Sum('line_total'),
    ).order_by('-total_value')[:20]

    customers = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')
    reps = company.users.filter(is_active=True).order_by('full_name', 'username')

    return render(request, 'reports/sales_report.html', {
        'invoices': invoices.order_by('-invoice_date')[:50],
        'totals': totals,
        'by_customer': by_customer,
        'by_product': by_product,
        'customers': customers,
        'reps': reps,
        'date_from': date_from,
        'date_to': date_to,
        'selected_customer': customer_id,
        'selected_rep': rep_id,
    })


@login_required
def collections_report(request):
    company = request.company
    date_from, date_to = get_date_range(request)

    customer_id = request.GET.get('customer', '').strip()
    method = request.GET.get('method', '').strip()
    status = request.GET.get('status', '').strip()

    collections = Collection.objects.filter(
        company=company,
        collection_date__gte=date_from,
        collection_date__lte=date_to,
    ).select_related('customer', 'collected_by')

    if customer_id:
        collections = collections.filter(customer_id=customer_id)
    if method:
        collections = collections.filter(payment_method=method)
    if status:
        collections = collections.filter(status=status)

    totals = collections.aggregate(
        total=Sum('amount'),
        count=Count('id'),
    )

    confirmed_total = collections.filter(status='confirmed').aggregate(total=Sum('amount'))['total'] or 0
    pending_total = collections.filter(status__in=['pending', 'pending_clearance']).aggregate(total=Sum('amount'))['total'] or 0

    by_method = collections.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('-total')

    by_customer = collections.values(
        'customer__pharmacy_name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('-total')[:20]

    customers = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')

    return render(request, 'reports/collections_report.html', {
        'collections': collections.order_by('-collection_date')[:50],
        'totals': totals,
        'confirmed_total': confirmed_total,
        'pending_total': pending_total,
        'by_method': by_method,
        'by_customer': by_customer,
        'customers': customers,
        'method_choices': Collection.PAYMENT_METHOD_CHOICES,
        'status_choices': Collection.STATUS_CHOICES,
        'date_from': date_from,
        'date_to': date_to,
        'selected_customer': customer_id,
        'selected_method': method,
        'selected_status': status,
    })


@login_required
def inventory_report(request):
    company = request.company

    product_id = request.GET.get('product', '').strip()
    warehouse_id = request.GET.get('warehouse', '').strip()
    stock_filter = request.GET.get('stock_filter', '').strip()

    inventory_rows = Inventory.objects.filter(
        company=company,
    ).select_related('product', 'batch', 'warehouse')

    if product_id:
        inventory_rows = inventory_rows.filter(product_id=product_id)
    if warehouse_id:
        inventory_rows = inventory_rows.filter(warehouse_id=warehouse_id)

    rows_list = list(inventory_rows.order_by('product__product_name', 'batch__expiry_date'))

    if stock_filter == 'low':
        rows_list = [r for r in rows_list if r.quantity_available <= r.product.min_stock_level]
    elif stock_filter == 'near_expiry':
        warning_date = timezone.localdate() + timedelta(days=90)
        rows_list = [r for r in rows_list if r.batch.expiry_date <= warning_date]

    total_available = sum(r.quantity_available for r in rows_list)

    products = Product.objects.filter(company=company, is_active=True).order_by('product_name')
    from inventory.models import Warehouse
    warehouses = Warehouse.objects.filter(company=company, is_active=True).order_by('warehouse_name')

    return render(request, 'reports/inventory_report.html', {
        'rows': rows_list,
        'total_available': total_available,
        'products': products,
        'warehouses': warehouses,
        'date_today': timezone.localdate(),
        'selected_product': product_id,
        'selected_warehouse': warehouse_id,
        'selected_stock_filter': stock_filter,
    })


@login_required
def aging_report(request):
    company = request.company
    today = timezone.localdate()

    invoices = Invoice.objects.filter(
        company=company,
        status__in=['issued', 'partially_paid'],
        amount_due__gt=0,
    ).select_related('customer', 'rep').order_by('customer__pharmacy_name', 'due_date')

    buckets = {
        'current': {'label': 'جاري (لم يستحق)', 'invoices': [], 'total': 0},
        '1_30': {'label': '1 - 30 يوم', 'invoices': [], 'total': 0},
        '31_60': {'label': '31 - 60 يوم', 'invoices': [], 'total': 0},
        '61_90': {'label': '61 - 90 يوم', 'invoices': [], 'total': 0},
        'over_90': {'label': 'أكثر من 90 يوم', 'invoices': [], 'total': 0},
    }

    customer_summary = {}

    for inv in invoices:
        if inv.due_date and inv.due_date < today:
            days_overdue = (today - inv.due_date).days
        else:
            days_overdue = 0

        if days_overdue == 0:
            bucket_key = 'current'
        elif days_overdue <= 30:
            bucket_key = '1_30'
        elif days_overdue <= 60:
            bucket_key = '31_60'
        elif days_overdue <= 90:
            bucket_key = '61_90'
        else:
            bucket_key = 'over_90'

        inv.days_overdue = days_overdue
        inv.bucket_key = bucket_key
        buckets[bucket_key]['invoices'].append(inv)
        buckets[bucket_key]['total'] += float(inv.amount_due)

        cname = inv.customer.pharmacy_name
        if cname not in customer_summary:
            customer_summary[cname] = {
                'customer': inv.customer,
                'current': 0, '1_30': 0, '31_60': 0, '61_90': 0, 'over_90': 0,
                'total': 0,
            }
        customer_summary[cname][bucket_key] += float(inv.amount_due)
        customer_summary[cname]['total'] += float(inv.amount_due)

    grand_total = sum(b['total'] for b in buckets.values())

    return render(request, 'reports/aging_report.html', {
        'buckets': buckets,
        'customer_summary': sorted(customer_summary.values(), key=lambda x: x['total'], reverse=True),
        'grand_total': grand_total,
        'today': today,
    })


@login_required
def customer_statement_print(request, customer_id):
    company = request.company
    customer = get_object_or_404(Customer, pk=customer_id, company=company)
    date_from, date_to = get_date_range(request)

    invoices = Invoice.objects.filter(
        company=company,
        customer=customer,
        invoice_date__gte=date_from,
        invoice_date__lte=date_to,
    ).order_by('invoice_date')

    collections = Collection.objects.filter(
        company=company,
        customer=customer,
        collection_date__gte=date_from,
        collection_date__lte=date_to,
        status__in=['confirmed', 'pending', 'pending_clearance']
    ).order_by('collection_date')

    balance = customer.get_balance_summary()

    from core.models import CompanyInfo
    company_info = CompanyInfo.objects.filter(company=company).first()

    return render(request, 'reports/customer_statement_print.html', {
        'customer': customer,
        'invoices': invoices,
        'collections': collections,
        'balance': balance,
        'company_info': company_info,
        'date_from': date_from,
        'date_to': date_to,
    })
