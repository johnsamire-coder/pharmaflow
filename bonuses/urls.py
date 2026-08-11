from django.urls import path
from . import views

app_name = 'bonuses'

urlpatterns = [
    path('', views.bonus_rule_list, name='bonus_rule_list'),
    path('new/', views.bonus_rule_create, name='bonus_rule_create'),
    path('<int:pk>/edit/', views.bonus_rule_update, name='bonus_rule_update'),
    path('<int:pk>/toggle/', views.bonus_rule_toggle, name='bonus_rule_toggle'),

    path('customer-rules/', views.customer_bonus_rule_list, name='customer_bonus_rule_list'),
    path('customer-rules/new/', views.customer_bonus_rule_create, name='customer_bonus_rule_create'),
    path('customer-rules/<int:pk>/edit/', views.customer_bonus_rule_update, name='customer_bonus_rule_update'),
    path('customer-rules/<int:pk>/toggle/', views.customer_bonus_rule_toggle, name='customer_bonus_rule_toggle'),
    path('customer-rules/<int:pk>/approve/', views.customer_bonus_rule_approve, name='customer_bonus_rule_approve'),

    path('report/', views.bonus_report, name='bonus_report'),
]
