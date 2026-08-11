from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import ListView

from .models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    model = Notification
    template_name = 'notifications/list.html'
    context_object_name = 'notifications'
    paginate_by = 20

    def get_queryset(self):
        return Notification.objects.filter(
            company=self.request.company
        ).filter(
            user=self.request.user
        ).order_by('-created_at')

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        unread_count = Notification.objects.filter(
            company=self.request.company,
            user=self.request.user,
            is_read=False
        ).count()
        ctx['unread_count'] = unread_count
        ctx['unread_notifications_count'] = unread_count
        return ctx


@login_required
def mark_read(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        company=request.company,
        user=request.user
    )
    notification.is_read = True
    notification.save(update_fields=['is_read'])

    messages.success(request, '✅ تم تعليم الإشعار كمقروء')
    return redirect('notifications:list')


@login_required
def mark_all_read(request):
    Notification.objects.filter(
        company=request.company,
        user=request.user,
        is_read=False
    ).update(is_read=True)

    messages.success(request, '✅ تم تعليم كل الإشعارات كمقروءة')
    return redirect('notifications:list')
