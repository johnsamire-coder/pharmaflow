from django.urls import path
from . import views

app_name = 'collections'

urlpatterns = [
    path('', views.CollectionListView.as_view(), name='collection_list'),
    path('new/', views.collection_create, name='collection_create'),
    path('<int:pk>/', views.CollectionDetailView.as_view(), name='collection_detail'),
    path('<int:pk>/edit/', views.collection_update, name='collection_update'),
    path('<int:pk>/confirm/', views.collection_confirm, name='collection_confirm'),
    path('<int:pk>/print/', views.collection_print, name='collection_print'),

    path('cheques/', views.cheque_list, name='cheque_list'),
    path('cheques/<int:pk>/status/', views.cheque_update_status, name='cheque_update_status'),

    path('statement/<int:customer_id>/', views.customer_statement, name='customer_statement'),
]
