from django.db.models import Q
from django.utils import timezone
from inventory.models import Inventory, InventoryMovement
from inventory.services import suggest_batches
from .models import SalesOrder, SalesOrderItem, SalesOrderItemBatch, Invoice, InvoiceItem
from core.models import SystemSetting


def get_setting(company, key, default):
    setting = SystemSetting.objects.filter(company=company, setting_key=key).first()
    return setting.setting_value if setting and setting.setting_value not in [None, ''] else default


def calculate_bonus(company, customer, product, quantity):
    """
    يحسب البونص للصنف بناءً على القواعد
    أولوية:
    1) قاعدة خاصة بالعميل + معتمدة + فعالة + ضمن الفترة
    2) قاعدة عامة فعالة + ضمن الفترة
    """
    from bonuses.models import BonusRule, CustomerBonusRule

    today = timezone.localdate()

    customer_rule = CustomerBonusRule.objects.filter(
        company=company,
        customer=customer,
        product=product,
        is_active=True,
        approved_by__isnull=False
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=today),
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    ).order_by('-id').first()

    if customer_rule:
        if customer_rule.bonus_type == 'none':
            return {'bonus_quantity': 0, 'bonus_source': 'customer_rule', 'rule_id': customer_rule.id}
        if customer_rule.bonus_type == 'quantity' and customer_rule.buy_quantity > 0:
            bonus_qty = (quantity // customer_rule.buy_quantity) * customer_rule.free_quantity
            return {'bonus_quantity': bonus_qty, 'bonus_source': 'customer_rule', 'rule_id': customer_rule.id}

    general_rule = BonusRule.objects.filter(
        company=company,
        product=product,
        is_active=True
    ).filter(
        Q(start_date__isnull=True) | Q(start_date__lte=today),
        Q(end_date__isnull=True) | Q(end_date__gte=today)
    ).order_by('-id').first()

    if general_rule:
        if general_rule.bonus_type == 'none':
            return {'bonus_quantity': 0, 'bonus_source': 'auto', 'rule_id': general_rule.id}
        if general_rule.bonus_type == 'quantity' and general_rule.buy_quantity > 0:
            bonus_qty = (quantity // general_rule.buy_quantity) * general_rule.free_quantity
            return {'bonus_quantity': bonus_qty, 'bonus_source': 'auto', 'rule_id': general_rule.id}

    return {'bonus_quantity': 0, 'bonus_source': 'none', 'rule_id': None}


def _extract_next_number(last_value, default_num=1):
    if not last_value:
        return default_num
    try:
        suffix = ''.join(ch for ch in str(last_value) if ch.isdigit())
        return int(suffix) + 1 if suffix else default_num
    except Exception:
        return default_num


def generate_order_number(company):
    prefix = get_setting(company, 'order_prefix', 'SO-')
    last = SalesOrder.objects.filter(company=company).order_by('-id').first()
    next_num = _extract_next_number(last.order_number if last else None, 1)
    return f"{prefix}{next_num:04d}"


def generate_invoice_number(company):
    prefix = get_setting(company, 'invoice_prefix', 'INV-')
    last = Invoice.objects.filter(company=company).order_by('-id').first()
    next_num = _extract_next_number(last.invoice_number if last else None, 1)
    return f"{prefix}{next_num:04d}"


def issue_invoice(sales_order, user):
    company = sales_order.company
    invoice_number = generate_invoice_number(company)

    from datetime import date, timedelta
    default_payment_days = int(get_setting(company, 'default_payment_days', '30') or 30)
    due_days = sales_order.customer.payment_days or default_payment_days
    due_date = date.today() + timedelta(days=due_days)

    invoice = Invoice.objects.create(
        company=company,
        invoice_number=invoice_number,
        sales_order=sales_order,
        customer=sales_order.customer,
        rep=sales_order.rep,
        invoice_date=date.today(),
        subtotal=sales_order.subtotal,
        tax_amount=sales_order.tax_amount,
        total_amount=sales_order.total_amount,
        amount_paid=0,
        amount_due=sales_order.total_amount,
        due_date=due_date,
        status='issued',
        created_by=user,
    )

    for item in sales_order.items.all():
        suggestion = suggest_batches(company, item.product.id, item.quantity)

        for sg in suggestion['suggestions']:
            inv_row = Inventory.objects.get(id=sg['inventory_id'])
            take_qty = sg['take_quantity']

            inv_row.quantity_available -= take_qty
            inv_row.save()

            InventoryMovement.objects.create(
                company=company,
                warehouse=inv_row.warehouse,
                product=item.product,
                batch=inv_row.batch,
                movement_type='sale',
                quantity=take_qty,
                reference_type='invoice',
                reference_id=str(invoice.id),
                notes=f'فاتورة {invoice_number}',
                created_by=user,
            )

            InvoiceItem.objects.create(
                invoice=invoice,
                product=item.product,
                batch=inv_row.batch,
                quantity=take_qty,
                unit_price=item.unit_price,
                line_total=take_qty * item.unit_price,
                is_bonus=False,
            )

        if item.bonus_quantity > 0:
            bonus_suggestion = suggest_batches(company, item.product.id, item.bonus_quantity)
            for sg in bonus_suggestion['suggestions']:
                inv_row = Inventory.objects.get(id=sg['inventory_id'])
                take_qty = sg['take_quantity']

                inv_row.quantity_available -= take_qty
                inv_row.save()

                InventoryMovement.objects.create(
                    company=company,
                    warehouse=inv_row.warehouse,
                    product=item.product,
                    batch=inv_row.batch,
                    movement_type='bonus',
                    quantity=take_qty,
                    reference_type='invoice',
                    reference_id=str(invoice.id),
                    notes=f'بونص - فاتورة {invoice_number}',
                    created_by=user,
                )

                InvoiceItem.objects.create(
                    invoice=invoice,
                    product=item.product,
                    batch=inv_row.batch,
                    quantity=take_qty,
                    unit_price=item.unit_price,
                    line_total=0,
                    is_bonus=True,
                )

    sales_order.status = 'delivered'
    sales_order.delivered_at = timezone.now()
    sales_order.save()

    return invoice
