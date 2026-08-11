from decimal import Decimal
from .models import ManufacturingOrder


def generate_order_number(company):
    from core.models import SystemSetting
    setting = SystemSetting.objects.filter(company=company, setting_key='manufacturing_prefix').first()
    prefix = setting.setting_value if setting and setting.setting_value else 'MO-'

    last = ManufacturingOrder.objects.filter(company=company).order_by('-id').first()
    if last:
        try:
            num = int(''.join(ch for ch in str(last.order_number) if ch.isdigit())) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"{prefix}{num:04d}"


def calculate_batch_cost(manufacturing_order, quantity_received, shipping_to_warehouse, tax_rate=14):
    manufacturing_cost = Decimal(str(manufacturing_order.total_manufacturing_cost))
    materials_cost = Decimal(str(manufacturing_order.total_materials_cost))
    additional_expenses = Decimal(str(manufacturing_order.total_expenses))
    shipping_to_warehouse = Decimal(str(shipping_to_warehouse or 0))

    total_before_tax = manufacturing_cost + materials_cost + additional_expenses + shipping_to_warehouse
    tax_amount = total_before_tax * Decimal(str(tax_rate)) / Decimal('100')
    total_cost = total_before_tax + tax_amount

    if quantity_received and quantity_received > 0:
        unit_cost = total_cost / Decimal(str(quantity_received))
    else:
        unit_cost = Decimal('0')

    return {
        'manufacturing_cost': manufacturing_cost,
        'materials_cost': materials_cost,
        'additional_expenses': additional_expenses,
        'shipping_to_warehouse': shipping_to_warehouse,
        'total_before_tax': total_before_tax,
        'tax_amount': tax_amount,
        'total_cost': total_cost,
        'unit_cost': unit_cost,
    }
