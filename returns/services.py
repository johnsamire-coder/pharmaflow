from django.utils import timezone
from .models import Return, CreditNote
from inventory.models import Inventory, InventoryMovement


def generate_return_number(company):
    last = Return.objects.filter(company=company).order_by('-id').first()
    if last:
        try:
            num = int(last.return_number.split('-')[-1]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"RET-{num:04d}"


def generate_credit_note_number(company):
    last = CreditNote.objects.filter(company=company).order_by('-id').first()
    if last:
        try:
            num = int(last.credit_note_number.split('-')[-1]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"CN-{num:04d}"


def process_return_receipt(return_order, warehouse, user):
    company = return_order.company

    for item in return_order.items.all():
        if item.disposition == 'return_to_stock':
            inv_row, created = Inventory.objects.get_or_create(
                company=company,
                warehouse=warehouse,
                product=item.product,
                batch=item.batch,
                defaults={
                    'quantity_available': 0,
                    'quantity_reserved': 0,
                    'quantity_on_consignment': 0,
                }
            )
            inv_row.quantity_available += item.quantity
            inv_row.save()

            InventoryMovement.objects.create(
                company=company,
                warehouse=warehouse,
                product=item.product,
                batch=item.batch,
                movement_type='customer_return',
                quantity=item.quantity,
                reference_type='return',
                reference_id=str(return_order.id),
                notes=f'مرتجع {return_order.return_number} - صالح للبيع',
                created_by=user,
            )

        elif item.disposition in ['destroy', 'quarantine']:
            InventoryMovement.objects.create(
                company=company,
                warehouse=warehouse,
                product=item.product,
                batch=item.batch,
                movement_type='damage',
                quantity=item.quantity,
                reference_type='return',
                reference_id=str(return_order.id),
                notes=f'مرتجع {return_order.return_number} - {item.get_disposition_display()}',
                created_by=user,
            )

    return_order.status = 'received'
    return_order.received_by = user
    return_order.received_at = timezone.now()
    return_order.save(update_fields=['status', 'received_by', 'received_at', 'updated_at'])

    cn_number = generate_credit_note_number(company)
    credit_note = CreditNote.objects.create(
        company=company,
        credit_note_number=cn_number,
        customer=return_order.customer,
        return_order=return_order,
        amount=return_order.total_value,
        status='issued',
        created_by=user,
    )

    return credit_note
