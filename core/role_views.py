from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django import forms

from .models import User, UserProfile, Company
from .roles import ROLES, PERMISSIONS, get_role_permissions


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['role', 'phone', 'notes']
        widgets = {
            'role': forms.Select(attrs={'class': 'pf-form-select'}),
            'phone': forms.TextInput(attrs={'class': 'pf-form-control'}),
            'notes': forms.Textarea(attrs={'class': 'pf-form-control', 'rows': 3}),
        }


@login_required
def roles_list(request):
    """قائمة الأدوار والمستخدمين"""
    if not request.user.is_superuser:
        try:
            profile = request.user.profile
            if profile.role != 'admin':
                messages.error(request, '🚫 ليس لديك صلاحية')
                return redirect('/dashboard/')
        except Exception:
            pass

    company = request.company

    profiles = UserProfile.objects.filter(
        company=company
    ).select_related('user').order_by('role', 'user__username')

    # مستخدمين بدون profile
    users_with_profile = profiles.values_list('user_id', flat=True)
    users_without_profile = User.objects.filter(
        company=company
    ).exclude(id__in=users_with_profile)

    return render(request, 'core/roles/list.html', {
        'profiles': profiles,
        'users_without_profile': users_without_profile,
        'roles': ROLES,
        'title': 'إدارة الأدوار والصلاحيات',
    })


@login_required
def assign_role(request, user_id):
    """تعيين دور لمستخدم"""
    if not request.user.is_superuser:
        try:
            profile = request.user.profile
            if profile.role != 'admin':
                messages.error(request, '🚫 ليس لديك صلاحية')
                return redirect('/dashboard/')
        except Exception:
            pass

    company = request.company
    user = get_object_or_404(User, pk=user_id, company=company)

    profile, created = UserProfile.objects.get_or_create(
        company=company,
        user=user,
        defaults={'role': 'sales_rep'}
    )

    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                f'✅ تم تحديث دور {user.get_full_name() or user.username} بنجاح'
            )
            return redirect('/roles/')
    else:
        form = UserProfileForm(instance=profile)

    role_key = profile.role
    role_permissions = get_role_permissions(role_key)

    return render(request, 'core/roles/assign.html', {
        'form': form,
        'target_user': user,
        'profile': profile,
        'roles': ROLES,
        'permissions': PERMISSIONS,
        'role_permissions': role_permissions,
        'title': f'تعيين دور: {user.get_full_name() or user.username}',
    })


@login_required
def role_detail(request, role_key):
    """تفاصيل الدور وصلاحياته"""
    role = ROLES.get(role_key)
    if not role:
        messages.error(request, 'الدور غير موجود')
        return redirect('/roles/')

    company = request.company
    role_permissions = get_role_permissions(role_key)

    users_in_role = UserProfile.objects.filter(
        company=company,
        role=role_key
    ).select_related('user')

    return render(request, 'core/roles/detail.html', {
        'role': role,
        'role_key': role_key,
        'role_permissions': role_permissions,
        'all_permissions': PERMISSIONS,
        'users_in_role': users_in_role,
        'title': f'صلاحيات دور: {role["label"]}',
    })
