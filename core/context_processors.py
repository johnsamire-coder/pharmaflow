from django.db.models import Q


def global_context(request):
    context = {}

    if not request.user.is_authenticated:
        return context

    company = getattr(request, 'company', None)
    if not company:
        return context

    # Unread notifications count
    try:
        from notifications.models import Notification
        unread_count = Notification.objects.filter(
            company=company,
            user=request.user,
            is_read=False
        ).count()
        context['unread_notifications_count'] = unread_count
    except Exception:
        context['unread_notifications_count'] = 0

    # User role & permissions
    try:
        profile = request.user.profile
        context['user_role'] = profile.role
        context['user_role_label'] = profile.get_role_display()
        context['user_role_color'] = profile.get_role_color()
    except Exception:
        context['user_role'] = 'admin' if request.user.is_superuser else 'viewer'
        context['user_role_label'] = 'مدير النظام' if request.user.is_superuser else 'مشاهد'
        context['user_role_color'] = 'danger' if request.user.is_superuser else 'secondary'

    return context


def check_perm(request):
    """
    Context processor يضيف دالة has_perm للـ template
    """
    from core.roles import user_has_permission

    def has_perm(permission):
        return user_has_permission(request.user, permission)

    return {'has_perm': has_perm}
