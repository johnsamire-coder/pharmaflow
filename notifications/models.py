from core.models import Notification as CoreNotification


class Notification(CoreNotification):
    class Meta:
        proxy = True
        app_label = 'notifications'
        ordering = ['-created_at']
