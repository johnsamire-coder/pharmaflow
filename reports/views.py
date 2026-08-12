from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from datetime import date, timedelta

from sales.models import Invoice, InvoiceItem
from customer_collections.models import Collection
from inventory.models import Batch
from customers.models import Customer
from products.models import Product
from returns.models import Return

try:
    from consignments.models import Consignment, ConsignmentItem
    HAS_CONSIGNMENTS = True
except ImportError:
    HAS_CONSIGNMENTS = False

try:
    from manufacturing.models import ManufacturingOrder, Factory
    HAS_MANUFACTURING = True
except ImportError:
    HAS_MANUFACTURING = False


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
    return render(request, 'reports/index.html', {})


# alias
@login_required
def index(request):
    return reports_home(request)


@login_required
def sales_report(request):
    company = request.company
    date_from, date_to = get_date_range(request)

    customer_id = request.GET.get('customer', '').strip()

    invoices = Invoice.objects.filter(
        company=company,
        invoice_date__gte=date_from,
        invoice_date__lte=date_to,
    ).select_related('customer')

    if customer_id:
        invoices = invoices.filter(customer_id=customer_id)

    totals = invoices.aggregate(
        total_sales=Sum('total_amount'),
        total_paid=Sum('paid_amount'),
        total_due=Sum('remaining_amount'),
        count=Count('id'),
    )

    # by customer
    by_customer = invoices.values(
        'customer__customer_name'
    ).annotate(
        total=Sum('total_amount'),
        count=Count('id'),
        paid=Sum('paid_amount'),
        due=Sum('remaining_amount'),
    ).order_by('-total')[:20]

    # by product
    try:
        by_product = InvoiceItem.objects.filter(
            invoice__company=company,
            invoice__invoice_date__gte=date_from,
            invoice__invoice_date__lte=date_to,
        ).values(
            'product__product_name',
        ).annotate(
            total_qty=Sum('quantity'),
            total_value=Sum('line_total'),
        ).order_by('-total_value')[:20]
    except Exception:
        by_product = []

    customers = Customer.objects.filter(
        company=company, is_active=True
    ).order_by('customer_name')

    return render(request, 'reports/sales_report.html', {
        'invoices': invoices.order_by('-invoice_date')[:50],
        'totals': totals,
        'by_customer': by_customer,
        'by_product': by_product,
        'customers': customers,
        'date_from': date_from,
        'date_to': date_to,
        'selected_customer': customer_id,
    })


@login_required
def collections_report(request):
    company = request.company
    date_from, date_to = get_date_range(request)

    customer_id = request.GET.get('customer', '').strip()
    method = request.GET.get('method', '').strip()

    collections = Collection.objects.filter(
        company=company,
        collection_date__gte=date_from,
        collection_date__lte=date_to,
    ).select_related('customer')

    if customer_id:
        collections = collections.filter(customer_id=customer_id)
    if method:
        collections = collections.filter(payment_method=method)

    totals = collections.aggregate(
        total=Sum('amount'),
        count=Count('id'),
    )

    by_method = collections.values('payment_method').annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('-total')

    by_customer = collections.values(
        'customer__customer_name'
    ).annotate(
        total=Sum('amount'),
        count=Count('id'),
    ).order_by('-total')[:20]

    customers = Customer.objects.filter(
        company=company, is_active=True
    ).order_by('customer_name')

    return render(request, 'reports/collections_report.html', {
        'collections': collections.order_by('-collection_date')[:50],
        'totals': totals,
        'by_method': by_method,
        'by_customer': by_customer,
        'customers': customers,
        'date_from': date_from,
        'date_to': date_to,
        'selected_customer': customer_id,
        'selected_method': method,
    })


@login_required
def inventory_report(request):
    company = request.company
    today = timezone.localdate()

    product_id = request.GET.get('product', '').strip()
    stock_filter = request.GET.get('stock_filter', '').strip()

    batches = Batch.objects.filter(
        company=company,
        status='available',
    ).select_related('product').order_by(
        'product__product_name', 'expiry_date'
    )

    if product_id:
        batches = batches.filter(product_id=product_id)

    if stock_filter == 'near_expiry':
        warning_date = today + timedelta(days=30)
        batches = batches.filter(
            expiry_date__gte=today,
            expiry_date__lte=warning_date
        )
    elif stock_filter == 'expired':
        batches = batches.filter(expiry_date__lt=today)

    total_available = batches.aggregate(
        t=Sum('quantity_available')
    )['t'] or 0

    expiring_count = Batch.objects.filter(
        company=company,
        status='available',
        expiry_date__gte=today,
        expiry_date__lte=today + timedelta(days=30)
    ).count()

    expired_count = Batch.objects.filter(
        company=company,
        expiry_date__lt=today
    ).count()

    products = Product.objects.filter(
        company=company, is_active=True
    ).order_by('product_name')

    return render(request, 'reports/inventory_report.html', {
        'batches': batches[:100],
        'total_available': total_available,
        'expiring_count': expiring_count,
        'expired_count': expired_count,
        'products': products,
        'date_today': today,
        'selected_product': product_id,
        'selected_stock_filter': stock_filter,
    })


@login_required
def customer_report(request):
    company = request.company
    today = timezone.localdate()

    search = request.GET.get('search', '').strip()
    area = request.GET.get('area', '').strip()

    customers = Customer.objects.filter(
        company=company,
        is_active=True
    ).order_by('customer_name')

    if search:
        customers = customers.filter(
            Q(customer_name__icontains=search) |
            Q(phone__icontains=search)
        )
    if area:
        customers = customers.filter(area__icontains=area)

    # حساب إجمالي المديونيات
    total_balance = customers.aggregate(
        t=Sum('current_balance')
    )['t'] or 0

    over_limit = customers.filter(
        current_balance__gt=F('credit_limit')
    ).count()

    areas = customers.values_list(
        'area', flat=True
    ).distinct().exclude(area__isnull=True).exclude(area='')

    return render(request, 'reports/customer_report.html', {
        'customers': customers[:100],
        'total_balance': total_balance,
        'over_limit': over_limit,
        'areas': areas,
        'search': search,
        'selected_area': area,
        'today': today,
    })


@login_required
def consignments_report(request):
    if not HAS_CONSIGNMENTS:
        from django.contrib import messages
        messages.warning(request, 'وحدة التصريف غير مفعلة')
        return render(request, 'reports/index.html', {})

    company = request.company
    date_from, date_to = get_date_range(request)

    status_filter = request.GET.get('status', '').strip()
    customer_id = request.GET.get('customer', '').strip()

    consignments = Consignment.objects.filter(
        company=company,
        sent_date__gte=date_from,
        sent_date__lte=date_to,
    ).select_related('customer').prefetch_related('items')

    if status_filter:
        consignments = consignments.filter(status=status_filter)
    if customer_id:
        consignments = consignments.filter(customer_id=customer_id)

    # إحصائيات
    total_sent_value = sum(c.total_sent_value for c in consignments)
    total_sold_value = sum(c.total_sold_value for c in consignments)
    total_returned_value = sum(c.total_returned_value for c in consignments)

    customers = Customer.objects.filter(
        company=company, is_active=True
    ).order_by('customer_name')

    return render(request, 'reports/consignments_report.html', {
        'consignments': consignments,
        'total_sent_value': total_sent_value,
        'total_sold_value': total_sold_value,
        'total_returned_value': total_returned_value,
        'customers': customers,
        'status_choices': Consignment.STATUS_CHOICES,
        'date_from': date_from,
        'date_to': date_to,
        'selected_status': status_filter,
        'selected_customer': customer_id,
    })


@login_required
def manufacturing_report(request):
    if not HAS_MANUFACTURING:
        from django.contrib import messages
        messages.warning(request, 'وحدة التصنيع غير مفعلة')
        return render(request, 'reports/index.html', {})

    company = request.company
    date_from, date_to = get_date_range(request)

    status_filter = request.GET.get('status', '').strip()
    factory_id = request.GET.get('factory', '').strip()

    orders = ManufacturingOrder.objects.filter(
        company=company,
    ).select_related('factory', 'product')

    if status_filter:
        orders = orders.filter(status=status_filter)
    if factory_id:
        orders = orders.filter(factory_id=factory_id)

    # إحصائيات
    total_orders = orders.count()
    completed = orders.filter(status='completed').count()
    in_progress = orders.filter(status='in_progress').count()
    pending = orders.filter(status='pending').count()

    total_cost = orders.aggregate(
        t=Sum('total_cost')
    )['t'] or 0

    factories = Factory.objects.filter(
        company=company
    ).order_by('factory_name')

    status_choices = ManufacturingOrder.STATUS_CHOICES

    return render(request, 'reports/manufacturing_report.html', {
        'orders': orders.order_by('-id')[:100],
        'total_orders': total_orders,
        'completed': completed,
        'in_progress': in_progress,
        'pending': pending,
        'total_cost': total_cost,
        'factories': factories,
        'status_choices': status_choices,
        'date_from': date_from,
        'date_to': date_to,
        'selected_status': status_filter,
        'selected_factory': factory_id,
    })
