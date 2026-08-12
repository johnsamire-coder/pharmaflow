from django.urls import path
from . import role_views

urlpatterns = [
    path('', role_views.roles_list, name='roles_list'),
    path('<str:role_key>/', role_views.role_detail, name='role_detail'),
    path('assign/<int:user_id>/', role_views.assign_role, name='assign_role'),
]
