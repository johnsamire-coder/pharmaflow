from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .models import BonusRule, CustomerBonusRule
from .forms import BonusRuleForm, CustomerBonusRuleForm
from customers.models import Customer
from products.models import Product
from sales.models import SalesOrderItem


@login_required
def bonus_rule_list(request):
    company = request.company
    qs = BonusRule.objects.filter(company=company).select_related('product')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        qs = qs.filter(
            Q(product__product_name__icontains=q) |
            Q(product__product_code__icontains=q)
        )

    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    return render(request, 'bonuses/bonus_rule_list.html', {
        'rules': qs.order_by('-created_at'),
    })


@login_required
def bonus_rule_create(request):
    company = request.company

    if request.method == 'POST':
        form = BonusRuleForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.created_by = request.user
            obj.save()
            messages.success(request, 'تم إنشاء قاعدة البونص العامة بنجاح')
            return redirect('bonuses:bonus_rule_list')
    else:
        form = BonusRuleForm(company=company)

    return render(request, 'bonuses/bonus_rule_form.html', {
        'form': form,
        'title': 'قاعدة بونص عامة جديدة',
    })


@login_required
def bonus_rule_update(request, pk):
    company = request.company
    obj = get_object_or_404(BonusRule, pk=pk, company=company)

    if request.method == 'POST':
        form = BonusRuleForm(request.POST, instance=obj, company=company)
        if form.is_valid():
            form.save()
            messages.success(request, 'تم تعديل قاعدة البونص العامة')
            return redirect('bonuses:bonus_rule_list')
    else:
        form = BonusRuleForm(instance=obj, company=company)

    return render(request, 'bonuses/bonus_rule_form.html', {
        'form': form,
        'title': f'تعديل قاعدة: {obj.product.product_name}',
    })


@login_required
def bonus_rule_toggle(request, pk):
    company = request.company
    obj = get_object_or_404(BonusRule, pk=pk, company=company)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, 'تم تحديث حالة قاعدة البونص')
    return redirect('bonuses:bonus_rule_list')


@login_required
def customer_bonus_rule_list(request):
    company = request.company
    qs = CustomerBonusRule.objects.filter(company=company).select_related('customer', 'product', 'approved_by')

    q = request.GET.get('q', '').strip()
    status = request.GET.get('status', '').strip()

    if q:
        qs = qs.filter(
            Q(customer__pharmacy_name__icontains=q) |
            Q(product__product_name__icontains=q) |
            Q(product__product_code__icontains=q)
        )

    if status == 'active':
        qs = qs.filter(is_active=True)
    elif status == 'inactive':
        qs = qs.filter(is_active=False)

    return render(request, 'bonuses/customer_bonus_rule_list.html', {
        'rules': qs.order_by('-created_at'),
    })


@login_required
def customer_bonus_rule_create(request):
    company = request.company

    if request.method == 'POST':
        form = CustomerBonusRuleForm(request.POST, company=company)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.company = company
            obj.created_by = request.user
            obj.approved_by = None
            obj.approved_at = None
            obj.save()
            messages.success(request, 'تم إنشاء قاعدة بونص خاصة بالعميل وتحتاج اعتماد')
            return redirect('bonuses:customer_bonus_rule_list')
    else:
        form = CustomerBonusRuleForm(company=company)

    return render(request, 'bonuses/customer_bonus_rule_form.html', {
        'form': form,
        'title': 'قاعدة بونص خاصة جديدة',
    })


@login_required
def customer_bonus_rule_update(request, pk):
    company = request.company
    obj = get_object_or_404(CustomerBonusRule, pk=pk, company=company)

    if request.method == 'POST':
        form = CustomerBonusRuleForm(request.POST, instance=obj, company=company)
        if form.is_valid():
            updated = form.save(commit=False)
            updated.approved_by = None
            updated.approved_at = None
            updated.save()
            messages.success(request, 'تم تعديل القاعدة الخاصة وتحتاج إعادة اعتماد')
            return redirect('bonuses:customer_bonus_rule_list')
    else:
        form = CustomerBonusRuleForm(instance=obj, company=company)

    return render(request, 'bonuses/customer_bonus_rule_form.html', {
        'form': form,
        'title': f'تعديل قاعدة العميل: {obj.customer.pharmacy_name}',
    })


@login_required
def customer_bonus_rule_toggle(request, pk):
    company = request.company
    obj = get_object_or_404(CustomerBonusRule, pk=pk, company=company)
    obj.is_active = not obj.is_active
    obj.save(update_fields=['is_active', 'updated_at'])
    messages.success(request, 'تم تحديث حالة القاعدة الخاصة')
    return redirect('bonuses:customer_bonus_rule_list')


@login_required
def customer_bonus_rule_approve(request, pk):
    company = request.company
    obj = get_object_or_404(CustomerBonusRule, pk=pk, company=company)
    obj.approved_by = request.user
    obj.approved_at = timezone.now()
    obj.save(update_fields=['approved_by', 'approved_at', 'updated_at'])
    messages.success(request, 'تم اعتماد القاعدة الخاصة')
    return redirect('bonuses:customer_bonus_rule_list')


@login_required
def bonus_report(request):
    company = request.company
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    customer_id = request.GET.get('customer', '').strip()
    product_id = request.GET.get('product', '').strip()

    qs = SalesOrderItem.objects.filter(
        sales_order__company=company,
        sales_order__status__in=['approved', 'delivered']
    ).select_related('sales_order__customer', 'product')

    if date_from:
        qs = qs.filter(sales_order__order_date__gte=date_from)
    if date_to:
        qs = qs.filter(sales_order__order_date__lte=date_to)
    if customer_id:
        qs = qs.filter(sales_order__customer_id=customer_id)
    if product_id:
        qs = qs.filter(product_id=product_id)

    qs = qs.filter(bonus_quantity__gt=0)

    by_product = qs.values(
        'product__product_name',
        'product__product_code',
    ).annotate(
        total_bonus_qty=Sum('bonus_quantity'),
        total_bonus_value=Sum('line_total'),
    ).order_by('-total_bonus_qty')

    by_customer = qs.values(
        'sales_order__customer__pharmacy_name',
    ).annotate(
        total_bonus_qty=Sum('bonus_quantity'),
    ).order_by('-total_bonus_qty')

    customers = Customer.objects.filter(company=company, is_active=True).order_by('pharmacy_name')
    products = Product.objects.filter(company=company, is_active=True).order_by('product_name')

    return render(request, 'bonuses/bonus_report.html', {
        'items': qs.order_by('-sales_order__order_date', '-id')[:100],
        'by_product': by_product,
        'by_customer': by_customer,
        'customers': customers,
        'products': products,
        'date_from': date_from,
        'date_to': date_to,
        'selected_customer': customer_id,
        'selected_product': product_id,
    })
