from django.db.models import Sum
from django.utils import timezone
from .models import Collection, CollectionInvoice
from sales.models import Invoice


def generate_receipt_number(company):
    last = Collection.objects.filter(company=company).order_by('-id').first()
    if last:
        try:
            num = int(last.receipt_number.split('-')[-1]) + 1
        except Exception:
            num = 1
    else:
        num = 1
    return f"RV-{num:04d}"


def get_collection_default_status(payment_method):
    if payment_method in ['cash_immediate', 'instapay_immediate', 'fawry_immediate', 'bank_transfer']:
        return 'confirmed'
    if payment_method == 'cheque':
        return 'pending_clearance'
    return 'pending'


def recalculate_invoice(invoice):
    total_confirmed = CollectionInvoice.objects.filter(
        invoice=invoice,
        collection__status='confirmed'
    ).aggregate(total=Sum('amount_applied'))['total'] or 0

    invoice.amount_paid = total_confirmed
    invoice.amount_due = invoice.total_amount - total_confirmed

    if invoice.amount_due <= 0:
        invoice.amount_due = 0
        invoice.status = 'paid'
    elif total_confirmed > 0:
        invoice.status = 'partially_paid'
    else:
        invoice.status = 'issued'

    invoice.save(update_fields=['amount_paid', 'amount_due', 'status'])


def save_collection_links(collection, invoice_amounts):
    old_invoice_ids = list(collection.invoice_links.values_list('invoice_id', flat=True))

    collection.invoice_links.all().delete()

    affected_invoice_ids = set(old_invoice_ids)

    for item in invoice_amounts:
        invoice_id = item.get('invoice_id')
        amount = item.get('amount', 0)

        if not invoice_id:
            continue

        try:
            amount = float(amount)
        except Exception:
            continue

        if amount <= 0:
            continue

        try:
            invoice = Invoice.objects.get(
                id=invoice_id,
                company=collection.company,
                customer=collection.customer,
            )
        except Invoice.DoesNotExist:
            continue

        other_confirmed = CollectionInvoice.objects.filter(
            invoice=invoice,
            collection__status='confirmed'
        ).exclude(collection=collection).aggregate(total=Sum('amount_applied'))['total'] or 0

        max_allowed = float(invoice.total_amount) - float(other_confirmed)
        if max_allowed <= 0:
            continue

        if amount > max_allowed:
            amount = max_allowed

        CollectionInvoice.objects.create(
            collection=collection,
            invoice=invoice,
            amount_applied=amount,
        )

        affected_invoice_ids.add(invoice.id)

    for invoice_id in affected_invoice_ids:
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            recalculate_invoice(invoice)
        except Invoice.DoesNotExist:
            continue


def confirm_collection(collection, user):
    collection.status = 'confirmed'
    collection.confirmed_by = user
    collection.confirmed_at = timezone.now()
    collection.save(update_fields=['status', 'confirmed_by', 'confirmed_at', 'updated_at'])

    for invoice_id in collection.invoice_links.values_list('invoice_id', flat=True):
        try:
            invoice = Invoice.objects.get(id=invoice_id)
            recalculate_invoice(invoice)
        except Invoice.DoesNotExist:
            continue
