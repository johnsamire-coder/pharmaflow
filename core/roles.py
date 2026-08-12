"""
PharmaFlow - Role & Permission System
تعريف الأدوار والصلاحيات
"""

# ===========================
# الصلاحيات المتاحة
# ===========================
PERMISSIONS = {
    # المبيعات
    'sales_view':       'عرض المبيعات',
    'sales_create':     'إنشاء فاتورة',
    'sales_edit':       'تعديل فاتورة',
    'sales_delete':     'حذف فاتورة',
    'sales_print':      'طباعة فاتورة',

    # العملاء
    'customers_view':   'عرض العملاء',
    'customers_create': 'إضافة عميل',
    'customers_edit':   'تعديل عميل',

    # المخزون
    'inventory_view':   'عرض المخزون',
    'inventory_add':    'إضافة مخزون',

    # المنتجات
    'products_view':    'عرض المنتجات',
    'products_create':  'إضافة منتج',
    'products_edit':    'تعديل منتج',

    # التحصيلات
    'collections_view':   'عرض التحصيلات',
    'collections_create': 'إضافة تحصيل',

    # المرتجعات
    'returns_view':     'عرض المرتجعات',
    'returns_create':   'إنشاء مرتجع',

    # البونص
    'bonuses_view':     'عرض البونص',
    'bonuses_manage':   'إدارة البونص',

    # التصريف
    'consignments_view':   'عرض التصريف',
    'consignments_manage': 'إدارة التصريف',

    # التصنيع
    'manufacturing_view':   'عرض التصنيع',
    'manufacturing_manage': 'إدارة التصنيع',

    # التقارير
    'reports_view':     'عرض التقارير',

    # الإدارة
    'users_manage':     'إدارة المستخدمين',
    'settings_manage':  'إدارة الإعدادات',
}

# ===========================
# الأدوار المحددة مسبقاً
# ===========================
ROLES = {
    'admin': {
        'label': 'مدير',
        'description': 'صلاحيات كاملة على كل شيء',
        'color': 'danger',
        'permissions': list(PERMISSIONS.keys()),  # كل الصلاحيات
    },
    'sales_manager': {
        'label': 'مدير مبيعات',
        'description': 'إدارة المبيعات والعملاء والتقارير',
        'color': 'primary',
        'permissions': [
            'sales_view', 'sales_create', 'sales_edit', 'sales_print',
            'customers_view', 'customers_create', 'customers_edit',
            'inventory_view',
            'products_view',
            'collections_view', 'collections_create',
            'returns_view', 'returns_create',
            'bonuses_view', 'bonuses_manage',
            'consignments_view', 'consignments_manage',
            'reports_view',
        ],
    },
    'sales_rep': {
        'label': 'مندوب مبيعات',
        'description': 'إنشاء فواتير وتحصيلات فقط',
        'color': 'success',
        'permissions': [
            'sales_view', 'sales_create', 'sales_print',
            'customers_view',
            'inventory_view',
            'products_view',
            'collections_view', 'collections_create',
            'returns_view', 'returns_create',
            'bonuses_view',
            'consignments_view',
        ],
    },
    'warehouse': {
        'label': 'أمين مخزن',
        'description': 'إدارة المخزون والمنتجات',
        'color': 'warning',
        'permissions': [
            'inventory_view', 'inventory_add',
            'products_view', 'products_create', 'products_edit',
            'manufacturing_view', 'manufacturing_manage',
        ],
    },
    'accountant': {
        'label': 'محاسب',
        'description': 'التحصيلات والتقارير المالية',
        'color': 'info',
        'permissions': [
            'sales_view', 'sales_print',
            'customers_view',
            'collections_view', 'collections_create',
            'returns_view',
            'reports_view',
        ],
    },
    'viewer': {
        'label': 'مشاهد',
        'description': 'عرض فقط بدون تعديل',
        'color': 'secondary',
        'permissions': [
            'sales_view',
            'customers_view',
            'inventory_view',
            'products_view',
            'reports_view',
        ],
    },
}


def get_role_permissions(role_key):
    """إرجاع قائمة صلاحيات الدور"""
    role = ROLES.get(role_key, {})
    return role.get('permissions', [])


def get_role_label(role_key):
    """إرجاع اسم الدور"""
    role = ROLES.get(role_key, {})
    return role.get('label', role_key)


def get_role_color(role_key):
    """إرجاع لون الدور"""
    role = ROLES.get(role_key, {})
    return role.get('color', 'secondary')


def user_has_permission(user, permission):
    """
    تحقق إذا كان المستخدم لديه صلاحية معينة
    - السوبر أدمن: كل الصلاحيات
    - غيره: حسب الدور المحدد في profile
    """
    if user.is_superuser:
        return True

    try:
        profile = user.profile
        role_key = profile.role
        if role_key == 'admin':
            return True
        role_perms = get_role_permissions(role_key)
        return permission in role_perms
    except Exception:
        return False


def check_permission(permission):
    """
    Decorator للـ views
    Usage:
        @check_permission('sales_create')
        def my_view(request): ...
    """
    from functools import wraps
    from django.shortcuts import redirect
    from django.contrib import messages

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('/login/')
            if not user_has_permission(request.user, permission):
                messages.error(request, '🚫 ليس لديك صلاحية للوصول لهذه الصفحة')
                return redirect('/dashboard/')
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
