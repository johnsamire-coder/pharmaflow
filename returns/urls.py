from django.urls import path
from . import views

app_name = 'returns'

urlpatterns = [
    path('', views.ReturnListView.as_view(), name='return_list'),
    path('new/', views.return_create, name='return_create'),
    path('<int:pk>/', views.ReturnDetailView.as_view(), name='return_detail'),
    path('<int:pk>/approve/', views.return_approve, name='return_approve'),
    path('<int:pk>/reject/', views.return_reject, name='return_reject'),
    path('<int:pk>/receive/', views.return_receive, name='return_receive'),
    path('credit-notes/', views.CreditNoteListView.as_view(), name='credit_note_list'),
]
