from django.urls import path
from . import views

urlpatterns = [
    # Login selector (home page)
    path('', views.login_selector, name='login_selector'),
    path('login/', views.login_selector, name='login'),
    
    # 7 Role-specific login pages
    path('login/hospital/', views.hospital_login, name='hospital_login'),
    path('login/jpo/', views.jpo_login, name='jpo_login'),
    path('login/po/', views.PO_login, name='apo_login'),
    path('login/dpo/', views.AS_login, name='dpo_login'),
    path('login/fa-cao/', views.GMM_login, name='fa_cao_login'),
    path('login/de/', views.de_login, name='de_login'),
    path('login/se-cgm/', views.se_cgm_login, name='se_cgm_login'),
    path('login/Director/', views.director_login, name='director_login'),
    path('login/customer-admin/', views.customer_admin_login, name='customer_admin_login'),
    path('register/', views.register, name='register'),
    
    # Dashboard and logout
    path('dashboard/', views.dashboard, name='dashboard'),
    path('logout/', views.logout_view, name='logout'),
]