from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, TemplateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.utils.text import slugify
import uuid

from .models import Company, User, Role, CompanyInfo, SystemSetting
from dashboard.views import dashboard_view


class HomeView(TemplateView):
    template_name = 'core/home.html'


# ==========================
# Super Admin Views
# ==========================
@login_required
def superadmin_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح لك بالوصول')
        return redirect('dashboard')

    companies = Company.objects.all().order_by('-created_at')
    total_users = User.objects.count()
    total_companies = companies.count()
    active_companies = companies.filter(is_active=True).count()

    return render(request, 'core/superadmin/dashboard.html', {
        'companies': companies,
        'total_users': total_users,
        'total_companies': total_companies,
        'active_companies': active_companies,
    })


@login_required
def company_create(request):
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح لك')
        return redirect('dashboard')

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        admin_username = request.POST.get('admin_username', '').strip()
        admin_password = request.POST.get('admin_password', '').strip()
        admin_fullname = request.POST.get('admin_fullname', '').strip()

        if not name or not admin_username or not admin_password:
            messages.error(request, 'يجب ملء الحقول المطلوبة')
            return render(request, 'core/superadmin/company_form.html', {})

        base_slug = slugify(name) or f"company-{uuid.uuid4().hex[:8]}"
        slug = base_slug
        counter = 1
        while Company.objects.filter(slug=slug).exists():
            slug = f"{base_slug}-{counter}"
            counter += 1

        company = Company.objects.create(
            name=name,
            slug=slug,
            email=email,
            phone=phone,
            is_active=True,
        )

        CompanyInfo.objects.create(
            company=company,
            company_name=name,
            email=email,
            phone=phone,
        )

        roles_data = [
            'مدير النظام', 'الإدارة العليا', 'إدارة التصنيع',
            'المخازن', 'الحسابات', 'مدير المبيعات', 'مندوب'
        ]
        for role_name in roles_data:
            Role.objects.get_or_create(company=company, role_name=role_name)

        admin_role = Role.objects.get(company=company, role_name='مدير النظام')

        if User.objects.filter(username=admin_username).exists():
            messages.error(request, f'اسم المستخدم {admin_username} موجود بالفعل')
            company.delete()
            return render(request, 'core/superadmin/company_form.html', {})

        User.objects.create_user(
            username=admin_username,
            password=admin_password,
            full_name=admin_fullname or admin_username,
            company=company,
            role=admin_role,
            is_staff=True,
        )

        _seed_default_settings(company)

        messages.success(request, f'تم إنشاء شركة {name} بنجاح')
        return redirect('core:superadmin_dashboard')

    return render(request, 'core/superadmin/company_form.html', {})


@login_required
def company_toggle(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'غير مصرح لك')
        return redirect('dashboard')
    company = get_object_or_404(Company, pk=pk)
    company.is_active = not company.is_active
    company.save()
    messages.success(request, f'تم تحديث حالة {company.name}')
    return redirect('core:superadmin_dashboard')


def _seed_default_settings(company):
    defaults = [
        ('tax_rate', '14', 'number', 'نسبة الضريبة'),
        ('expiry_warning_days', '90', 'number', 'أيام التنبيه قبل انتهاء الصلاحية'),
        ('cheque_warning_days', '7', 'number', 'أيام التنبيه للشيكات'),
        ('invoice_prefix', 'INV-', 'string', 'بادئة أرقام الفواتير'),
        ('order_prefix', 'SO-', 'string', 'بادئة أرقام الأوردرات'),
        ('receipt_prefix', 'RV-', 'string', 'بادئة سندات القبض'),
        ('return_prefix', 'RET-', 'string', 'بادئة المرتجعات'),
        ('default_payment_days', '30', 'number', 'أيام السداد الافتراضية'),
    ]
    for key, value, stype, desc in defaults:
        SystemSetting.objects.get_or_create(
            company=company,
            setting_key=key,
            defaults={'setting_value': value, 'setting_type': stype, 'description': desc}
        )


# ==========================
# User Management
# ==========================
@login_required
def user_list(request):
    company = request.company
    users = User.objects.filter(company=company).select_related('role').order_by('full_name', 'username')

    q = request.GET.get('q', '').strip()
    if q:
        users = users.filter(
            Q(username__icontains=q) |
            Q(full_name__icontains=q) |
            Q(email__icontains=q)
        )

    return render(request, 'core/users/user_list.html', {'users': users})


@login_required
def user_create(request):
    company = request.company
    roles = Role.objects.filter(company=company).order_by('role_name')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        password = request.POST.get('password', '').strip()
        role_id = request.POST.get('role_id', '').strip()
        is_active = request.POST.get('is_active') == 'on'

        if not username or not password:
            messages.error(request, 'اسم المستخدم وكلمة المرور مطلوبان')
            return render(request, 'core/users/user_form.html', {'roles': roles})

        if User.objects.filter(username=username).exists():
            messages.error(request, 'اسم المستخدم موجود بالفعل')
            return render(request, 'core/users/user_form.html', {'roles': roles})

        role = None
        if role_id:
            try:
                role = Role.objects.get(id=role_id, company=company)
            except Role.DoesNotExist:
                pass

        user = User.objects.create_user(
            username=username,
            password=password,
            full_name=full_name,
            email=email,
            phone=phone,
            company=company,
            role=role,
            is_active=is_active,
            created_by=request.user,
        )

        messages.success(request, f'تم إنشاء المستخدم {username} بنجاح')
        return redirect('core:user_list')

    return render(request, 'core/users/user_form.html', {'roles': roles})


@login_required
def user_update(request, pk):
    company = request.company
    user_obj = get_object_or_404(User, pk=pk, company=company)
    roles = Role.objects.filter(company=company).order_by('role_name')

    if request.method == 'POST':
        user_obj.full_name = request.POST.get('full_name', '').strip()
        user_obj.email = request.POST.get('email', '').strip()
        user_obj.phone = request.POST.get('phone', '').strip()
        user_obj.is_active = request.POST.get('is_active') == 'on'

        role_id = request.POST.get('role_id', '').strip()
        if role_id:
            try:
                user_obj.role = Role.objects.get(id=role_id, company=company)
            except Role.DoesNotExist:
                pass

        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            user_obj.set_password(new_password)

        user_obj.save()
        messages.success(request, f'تم تعديل بيانات {user_obj.username}')
        return redirect('core:user_list')

    return render(request, 'core/users/user_form.html', {
        'roles': roles,
        'user_obj': user_obj,
        'is_edit': True,
    })


@login_required
def user_toggle(request, pk):
    company = request.company
    user_obj = get_object_or_404(User, pk=pk, company=company)
    if user_obj == request.user:
        messages.error(request, 'لا يمكنك تعطيل حسابك الخاص')
        return redirect('core:user_list')
    user_obj.is_active = not user_obj.is_active
    user_obj.save()
    messages.success(request, 'تم تحديث حالة المستخدم')
    return redirect('core:user_list')


# ==========================
# Company Settings
# ==========================
@login_required
def company_settings(request):
    company = request.company
    company_info = CompanyInfo.objects.filter(company=company).first()

    settings_qs = SystemSetting.objects.filter(company=company)
    settings_dict = {s.setting_key: s.setting_value for s in settings_qs}

    if request.method == 'POST':
        form_type = request.POST.get('form_type', '')

        if form_type == 'company_info':
            if not company_info:
                company_info = CompanyInfo(company=company)
            company_info.company_name = request.POST.get('company_name', '').strip()
            company_info.company_name_en = request.POST.get('company_name_en', '').strip()
            company_info.address = request.POST.get('address', '').strip()
            company_info.phone = request.POST.get('phone', '').strip()
            company_info.fax = request.POST.get('fax', '').strip()
            company_info.email = request.POST.get('email', '').strip()
            company_info.website = request.POST.get('website', '').strip()
            company_info.tax_number = request.POST.get('tax_number', '').strip()
            company_info.commercial_register = request.POST.get('commercial_register', '').strip()
            company_info.invoice_notes = request.POST.get('invoice_notes', '').strip()

            if 'logo' in request.FILES:
                company_info.logo = request.FILES['logo']
            if 'stamp' in request.FILES:
                company_info.stamp = request.FILES['stamp']

            company_info.save()
            messages.success(request, 'تم حفظ بيانات الشركة')

        elif form_type == 'system_settings':
            setting_keys = [
                'tax_rate', 'expiry_warning_days', 'cheque_warning_days',
                'invoice_prefix', 'order_prefix', 'receipt_prefix',
                'return_prefix', 'default_payment_days',
            ]
            for key in setting_keys:
                value = request.POST.get(key, '').strip()
                SystemSetting.objects.update_or_create(
                    company=company,
                    setting_key=key,
                    defaults={'setting_value': value}
                )
            messages.success(request, 'تم حفظ إعدادات النظام')

        return redirect('core:company_settings')

    return render(request, 'core/settings/company_settings.html', {
        'company_info': company_info,
        'settings': settings_dict,
    })
