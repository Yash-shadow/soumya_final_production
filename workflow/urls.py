from django.urls import path
from . import views

app_name = 'workflow'

urlpatterns = [
    path('queue/', views.approval_queue, name='approval_queue'),
    path('allocation/', views.customer_admin_allocation, name='customer_admin_allocation'),
    path('allocate/<int:request_id>/', views.allocate_task, name='allocate_task'),
    path('request/<int:request_id>/', views.request_detail, name='request_detail'),
    path('request/<int:request_id>/process/', views.process_request, name='process_request'),
]
