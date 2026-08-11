from .models import AuditLog

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.company = None

        if request.user.is_authenticated:
            request.company = getattr(request.user, 'company', None)

        response = self.get_response(request)
        return response


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        try:
            if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                AuditLog.objects.create(
                    company=getattr(request.user, 'company', None),
                    user=request.user,
                    action=request.method,
                    table_name=request.path,
                    record_id='',
                    old_values=None,
                    new_values=None,
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
        except Exception:
            pass

        return response

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
