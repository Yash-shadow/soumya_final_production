# accounts/models.py 
from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    """Extended user profile with role-based access."""
    
    ROLE_CHOICES = (
        ('HOSPITAL', 'Hospital Admin'),
        ('JPO', 'Junior Personnel Officer'),
        ('PO', 'Personnel Officer'),
        ('AS', 'Asist Sectory'),
        ('GMM', 'General Medical &Personal'),
        ('CGM', 'Chief General Manager '),
        ('JS', 'JOINT SECTROY '),
        ('DIRECTOR','DIRECTOR_HRD'),
        ('CUSTOMER_ADMIN', 'Customer Admin'),
    )
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    designation = models.CharField(max_length=100, blank=True)
    department = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    
    # For Hospital role - link to hospital
    hospital = models.ForeignKey(
        'hospitals.Hospital',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'
    
    def __str__(self):
        return f"{self.user.username} ({self.get_role_display()})"
    
    @property
    def is_hospital_user(self):
        return self.role == 'HOSPITAL'
    
    @property
    def is_approver(self):
        return self.role in ['JPO', 'PO', 'AS', 'GMM', 'CGM', 'JS','DIRECTOR']
    
    @property
    def can_final_approve(self):
        return self.role == 'JS'
    @property
    def can_final_approve(self):
        return self.role == 'DIRECTOR'