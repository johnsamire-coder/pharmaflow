def company_context(request):
    """
    Context processor متوافق مع الإعدادات القديمة
    """
    company = getattr(request, 'company', None)
    return {
        'company': company,
    }


def notifications_context(request):
    """
    Context processor متوافق مع الإعدادات القديمة
    """
    unread_count = 0

    try:
        if request.user.is_authenticated:
            company = getattr(request, 'company', None)
            if company:
                from notifications.models import Notification
                unread_count = Notification.objects.filter(
                    company=company,
                    user=request.user,
                    is_read=False
                ).count()
    except Exception:
        unread_count = 0

    return {
        'unread_notifications_count': unread_count,
    }



def check_perm(request):
    """
    إضافة دالة has_perm للـ templates
    """
    try:
        from core.roles import user_has_permission
    except Exception:
        def user_has_permission(user, permission):
            return bool(getattr(user, 'is_superuser', False))

    def has_perm(permission):
        try:
            if not request.user.is_authenticated:
                return False
            return user_has_permission(request.user, permission)
        except Exception:
            return False

    return {
        'has_perm': has_perm
    }


def global_context(request):
    """
    Context عام للنظام - يضيف company_info لكل الـ templates
    """
    context = {}

    company = getattr(request, 'company', None)
    context['company'] = company

    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        context['unread_notifications_count'] = 0
        context['user_role'] = 'viewer'
        context['user_role_label'] = 'زائر'
        context['user_role_color'] = 'secondary'
        context['company_info'] = None
        return context

    # Company Info (للطباعة)
    try:
        from core.models import CompanyInfo
        company_info = CompanyInfo.objects.filter(company=company).first()
        context['company_info'] = company_info
    except Exception:
        context['company_info'] = None

    # الإشعارات
    try:
        unread_count = 0
        if company:
            from notifications.models import Notification
            unread_count = Notification.objects.filter(
                company=company,
                user=request.user,
                is_read=False
            ).count()
        context['unread_notifications_count'] = unread_count
    except Exception:
        context['unread_notifications_count'] = 0

    # الدور
    try:
        if request.user.is_superuser:
            context['user_role'] = 'admin'
            context['user_role_label'] = 'مدير النظام'
            context['user_role_color'] = 'danger'
        else:
            profile = request.user.profile
            context['user_role'] = profile.role
            context['user_role_label'] = profile.get_role_display()
            context['user_role_color'] = profile.get_role_color()
    except Exception:
        context['user_role'] = 'viewer'
        context['user_role_label'] = 'مشاهد'
        context['user_role_color'] = 'secondary'

    return context
