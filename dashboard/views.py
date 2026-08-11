from datetime import timedelta
import json

from django.apps import apps
from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.utils import timezone


def get_model(app_label, *model_names):
    for model_name in model_names:
        try:
            return apps.get_model(app_label, model_name)
        except LookupError:
            continue
    return None


def safe_sum(qs, field_name):
    try:
        return qs.aggregate(total=Sum(field_name)).get('total') or 0
    except Exception:
        return 0


@login_required
def dashboard_view(request):
    company = request.company
    today = timezone.now().date()
    month_start = today.replace(day=1)

    Invoice = get_model('sales', 'Invoice')
    Customer = get_model('customers', 'Customer')
    Product = get_model('products', 'Product')
    Batch = get_model('inventory', 'Batch')
    Collection = get_model('customer_collections', 'Collection', 'CustomerCollection')
    Return = get_model('returns', 'Return', 'SalesReturn')
    Notification = get_model('notifications', 'Notification')
    Consignment = get_model('consignments', 'Consignment')

    today_sales = 0
    today_sales_amount = 0
    today_collections = 0
    today_collections_amount = 0
    total_products = 0
    low_stock = 0
    total_stock = 0
    expiring_soon = 0
    total_customers = 0
    active_customers = 0
    month_returns = 0
    month_returns_amount = 0
    active_consignments = 0
    recent_invoices = []
    recent_notifications = []
    chart_labels = []
    chart_data = []
    stock_available = 0
    stock_low = 0
    stock_expired = 0

    day_names = {
        0: 'الإثنين',
        1: 'الثلاثاء',
        2: 'الأربعاء',
        3: 'الخميس',
        4: 'الجمعة',
        5: 'السبت',
        6: 'الأحد',
    }

    if Invoice:
        try:
            today_invoices = Invoice.objects.filter(
                company=company,
                invoice_date=today
            )
            today_sales = today_invoices.count()
            today_sales_amount = safe_sum(today_invoices, 'total_amount')

            recent_invoices = Invoice.objects.filter(
                company=company
            ).select_related('customer').order_by('-invoice_date', '-id')[:8]

            for i in range(6, -1, -1):
                day = today - timedelta(days=i)
                amt = safe_sum(
                    Invoice.objects.filter(company=company, invoice_date=day),
                    'total_amount'
                )
                chart_labels.append(day_names[day.weekday()])
                chart_data.append(float(amt))
        except Exception:
            pass

    if Collection:
        try:
            today_colls = Collection.objects.filter(
                company=company,
                collection_date=today
            )
            today_collections = today_colls.count()
            today_collections_amount = safe_sum(today_colls, 'amount')
        except Exception:
            pass

    if Product:
        try:
            total_products = Product.objects.filter(
                company=company,
                is_active=True
            ).count()

            low_stock = Product.objects.filter(
                company=company,
                is_active=True
            ).count()
        except Exception:
            pass

    if Batch:
        try:
            total_stock = safe_sum(
                Batch.objects.filter(company=company, status='available'),
                'quantity_available'
            )

            expiring_soon = Batch.objects.filter(
                company=company,
                status='available',
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=30)
            ).count()

            stock_available = Batch.objects.filter(
                company=company,
                status='available',
                expiry_date__gt=today + timedelta(days=30)
            ).count()

            stock_low = Batch.objects.filter(
                company=company,
                status='available',
                expiry_date__gte=today,
                expiry_date__lte=today + timedelta(days=30)
            ).count()

            stock_expired = Batch.objects.filter(
                company=company,
                expiry_date__lt=today
            ).count()
        except Exception:
            pass

    if Customer:
        try:
            total_customers = Customer.objects.filter(
                company=company
            ).count()

            active_customers = Customer.objects.filter(
                company=company,
                is_active=True
            ).count()
        except Exception:
            pass

    if Return:
        try:
            month_returns_qs = Return.objects.filter(
                company=company,
                return_date__gte=month_start
            )
            month_returns = month_returns_qs.count()
            month_returns_amount = safe_sum(month_returns_qs, 'total_amount')
        except Exception:
            pass

    if Consignment:
        try:
            active_consignments = Consignment.objects.filter(
                company=company,
                status__in=['sent', 'partial_returned']
            ).count()
        except Exception:
            pass

    if Notification:
        try:
            recent_notifications = Notification.objects.filter(
                company=company,
                user=request.user
            ).order_by('-created_at')[:6]
        except Exception:
            pass

    context = {
        'today_sales': today_sales,
        'today_sales_amount': f"{today_sales_amount:,.2f}",
        'today_collections': today_collections,
        'today_collections_amount': f"{today_collections_amount:,.2f}",
        'total_products': total_products,
        'low_stock': low_stock,
        'total_stock': f"{total_stock:,}",
        'expiring_soon': expiring_soon,
        'total_customers': total_customers,
        'active_customers': active_customers,
        'month_returns': month_returns,
        'month_returns_amount': f"{month_returns_amount:,.2f}",
        'active_consignments': active_consignments,
        'chart_labels': json.dumps(chart_labels, ensure_ascii=False),
        'chart_data': json.dumps(chart_data),
        'stock_available': stock_available,
        'stock_low': stock_low,
        'stock_expired': stock_expired,
        'recent_invoices': recent_invoices,
        'recent_notifications': recent_notifications,
    }

    return render(request, 'dashboard/index.html', context)


dashboard_index = dashboard_view
