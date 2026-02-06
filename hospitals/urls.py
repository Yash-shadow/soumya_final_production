from django.urls import path
from . import views

app_name = 'hospitals'

urlpatterns = [
    path('', views.hospital_dashboard, name='dashboard'),
    path('submit-bill/', views.submit_bill, name='submit_bill'),
    path('bills/', views.bill_list, name='bill_list'),
    path('bills/<int:bill_id>/', views.bill_detail, name='bill_detail'),
]
