from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.ProductListView.as_view(), name='product_list'),
    path('new/', views.ProductCreateView.as_view(), name='product_create'),
    path('<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_update'),
    path('<int:pk>/toggle-status/', views.product_toggle_status, name='product_toggle_status'),

    path('categories/', views.CategoryListView.as_view(), name='category_list'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    path('categories/<int:pk>/toggle-status/', views.category_toggle_status, name='category_toggle_status'),

    path('forms/', views.ProductFormTypeListView.as_view(), name='formtype_list'),
    path('forms/new/', views.ProductFormTypeCreateView.as_view(), name='formtype_create'),
    path('forms/<int:pk>/edit/', views.ProductFormTypeUpdateView.as_view(), name='formtype_update'),
    path('forms/<int:pk>/toggle-status/', views.formtype_toggle_status, name='formtype_toggle_status'),
]
