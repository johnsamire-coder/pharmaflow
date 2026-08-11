from .models import CompanyInfo, Notification

def company_context(request):
    company_info = None
    if getattr(request, 'company', None):
        company_info = CompanyInfo.objects.filter(company=request.company).first()
    return {
        'current_company': getattr(request, 'company', None),
        'company_info': company_info,
    }

def notifications_context(request):
    unread_notifications = []
    unread_count = 0

    if request.user.is_authenticated:
        unread_notifications = Notification.objects.filter(user=request.user, is_read=False).order_by('-created_at')[:10]
        unread_count = Notification.objects.filter(user=request.user, is_read=False).count()

    return {
        'unread_notifications': unread_notifications,
        'unread_notifications_count': unread_count,
    }
