from django.urls import path
from . import views

app_name = 'consignments'

urlpatterns = [
    # القائمة الرئيسية
    path('', views.ConsignmentListView.as_view(), name='list'),

    # إنشاء جديد
    path('create/', views.ConsignmentCreateView.as_view(), name='create'),

    # تفاصيل
    path('<int:pk>/', views.ConsignmentDetailView.as_view(), name='detail'),

    # تعديل (مسودة فقط)
    path('<int:pk>/edit/', views.ConsignmentUpdateView.as_view(), name='edit'),

    # إرسال (تغيير الحالة لـ sent)
    path('<int:pk>/send/', views.ConsignmentSendView.as_view(), name='send'),

    # تسجيل مرتجع
    path('<int:pk>/return/', views.ConsignmentReturnView.as_view(), name='return'),

    # تسوية وتحويل لفاتورة
    path('<int:pk>/settle/', views.ConsignmentSettleView.as_view(), name='settle'),

    # إلغاء
    path('<int:pk>/cancel/', views.ConsignmentCancelView.as_view(), name='cancel'),

    # طباعة
    path('<int:pk>/print/', views.ConsignmentPrintView.as_view(), name='print'),

    # AJAX: جلب أسعار المنتج
    path('ajax/product-price/', views.ajax_product_price, name='ajax_product_price'),

    # AJAX: جلب دفعات المنتج
    path('ajax/product-batches/', views.ajax_product_batches, name='ajax_product_batches'),
]
