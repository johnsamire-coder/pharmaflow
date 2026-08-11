from .models import Inventory

def suggest_batches(company, product_id, quantity, warehouse_id=None):
    qs = Inventory.objects.filter(
        company=company,
        product_id=product_id,
        batch__status='approved',
        quantity_available__gt=0
    ).select_related('batch', 'warehouse').order_by('batch__expiry_date', 'batch__batch_number')

    if warehouse_id:
        qs = qs.filter(warehouse_id=warehouse_id)

    remaining = quantity
    suggestions = []

    for row in qs:
        if remaining <= 0:
            break

        take_qty = min(row.quantity_available, remaining)
        suggestions.append({
            'inventory_id': row.id,
            'warehouse': row.warehouse.warehouse_name,
            'batch_id': row.batch.id,
            'batch_number': row.batch.batch_number,
            'expiry_date': row.batch.expiry_date,
            'available': row.quantity_available,
            'take_quantity': take_qty,
        })
        remaining -= take_qty

    return {
        'requested_quantity': quantity,
        'fulfilled_quantity': quantity - remaining,
        'remaining_quantity': remaining,
        'is_fully_available': remaining == 0,
        'suggestions': suggestions,
    }
