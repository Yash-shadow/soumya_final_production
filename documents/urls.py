from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.document_list, name='document_list'),
    path('<uuid:doc_id>/', views.document_detail, name='document_detail'),
    path('<uuid:doc_id>/view/', views.document_view, name='document_view'),
]
