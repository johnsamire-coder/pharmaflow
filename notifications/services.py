from core.models import Notification, User, Company


def send_notification(company, user, notification_type, title, message='',
                      reference_table=None, reference_id=None):
    """
    إرسال إشعار لمستخدم معين
    """
    Notification.objects.create(
        company=company,
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        reference_table=reference_table or '',
        reference_id=str(reference_id) if reference_id else '',
        is_read=False,
    )


def send_notification_to_role(company, role_name, notification_type, title,
                               message='', reference_table=None, reference_id=None):
    """
    إرسال إشعار لكل المستخدمين بدور معين
    """
    users = User.objects.filter(
        company=company,
        role__role_name=role_name,
        is_active=True
    )
    for user in users:
        send_notification(
            company=company,
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_table=reference_table,
            reference_id=reference_id,
        )


def send_notification_to_managers(company, notification_type, title,
                                   message='', reference_table=None, reference_id=None):
    """
    إرسال إشعار لمدير المبيعات ومدير النظام
    """
    users = User.objects.filter(
        company=company,
        role__role_name__in=['مدير النظام', 'مدير المبيعات', 'الإدارة العليا'],
        is_active=True
    )
    for user in users:
        send_notification(
            company=company,
            user=user,
            notification_type=notification_type,
            title=title,
            message=message,
            reference_table=reference_table,
            reference_id=reference_id,
        )


def check_and_notify_expiry(company):
    """
    تفحص التشغيلات القريبة من الانتهاء وترسل إشعارات
    """
    from inventory.models import Batch
    from django.utils import timezone
    from datetime import timedelta
    from core.models import SystemSetting

    setting = SystemSetting.objects.filter(
        company=company, setting_key='expiry_warning_days'
    ).first()

    days = int(setting.setting_value) if setting and setting.setting_value else 90
    warning_date = timezone.localdate() + timedelta(days=days)

    batches = Batch.objects.filter(
        company=company,
        status='approved',
        expiry_date__lte=warning_date,
        expiry_date__gte=timezone.localdate(),
    ).select_related('product')

    notified_count = 0
    for batch in batches:
        existing = Notification.objects.filter(
            company=company,
            notification_type='expiry_warning',
            reference_table='batches',
            reference_id=str(batch.id),
        ).exists()

        if not existing:
            send_notification_to_managers(
                company=company,
                notification_type='expiry_warning',
                title=f'تنبيه: قرب انتهاء صلاحية {batch.product.product_name}',
                message=f'التشغيلة {batch.batch_number} تنتهي في {batch.expiry_date}',
                reference_table='batches',
                reference_id=batch.id,
            )
            notified_count += 1

    return notified_count


def check_and_notify_low_stock(company):
    """
    تفحص الأصناف تحت الحد الأدنى وترسل إشعارات
    """
    from inventory.models import Inventory
    from products.models import Product
    from django.db.models import Sum

    products = Product.objects.filter(company=company, is_active=True, min_stock_level__gt=0)

    notified_count = 0
    for product in products:
        total = Inventory.objects.filter(
            company=company,
            product=product,
            batch__status='approved'
        ).aggregate(total=Sum('quantity_available'))['total'] or 0

        if total <= product.min_stock_level:
            existing = Notification.objects.filter(
                company=company,
                notification_type='low_stock',
                reference_table='products',
                reference_id=str(product.id),
                is_read=False,
            ).exists()

            if not existing:
                send_notification_to_managers(
                    company=company,
                    notification_type='low_stock',
                    title=f'تنبيه: مخزون منخفض - {product.product_name}',
                    message=f'الكمية المتاحة {total} أقل من الحد الأدنى {product.min_stock_level}',
                    reference_table='products',
                    reference_id=product.id,
                )
                notified_count += 1

    return notified_count


def check_and_notify_cheques(company):
    """
    تفحص الشيكات المستحقة خلال أيام محددة
    """
    from customer_collections.models import Collection
    from django.utils import timezone
    from datetime import timedelta
    from core.models import SystemSetting

    setting = SystemSetting.objects.filter(
        company=company, setting_key='cheque_warning_days'
    ).first()

    days = int(setting.setting_value) if setting and setting.setting_value else 7
    warning_date = timezone.localdate() + timedelta(days=days)

    cheques = Collection.objects.filter(
        company=company,
        payment_method='cheque',
        status='pending_clearance',
        cheque_due_date__lte=warning_date,
        cheque_due_date__gte=timezone.localdate(),
    ).select_related('customer')

    notified_count = 0
    for cheque in cheques:
        existing = Notification.objects.filter(
            company=company,
            notification_type='cheque_due',
            reference_table='collections',
            reference_id=str(cheque.id),
            is_read=False,
        ).exists()

        if not existing:
            send_notification_to_managers(
                company=company,
                notification_type='cheque_due',
                title=f'شيك مستحق - {cheque.customer.pharmacy_name}',
                message=f'شيك رقم {cheque.cheque_number} بمبلغ {cheque.amount} مستحق في {cheque.cheque_due_date}',
                reference_table='collections',
                reference_id=cheque.id,
            )
            notified_count += 1

    return notified_count


def run_all_checks(company):
    results = {
        'expiry': check_and_notify_expiry(company),
        'low_stock': check_and_notify_low_stock(company),
        'cheques': check_and_notify_cheques(company),
    }
    return results
