# Script to create test users for all 7 roles
import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.contrib.auth.models import User
from accounts.models import UserProfile
from hospitals.models import Hospital
from workflow.models import WorkflowStep, SanctionLimit

print("Creating test data...")

# Create Workflow Steps
workflow_steps = [
    (1, 'JPO Review', 'JPO'),
    (2, 'APO Review', 'PO'),
    (3, 'DPO Review', 'AS'),
    (4, 'FA & CAO Review', 'GMM'),
    (5, 'DE Technical Review', 'CGM'),
    (6, 'SE Final Review', 'JS'),
    (7, 'Director Verification', 'DIRECTOR'),
]

for order, name, role in workflow_steps:
    can_reject = order >= 6
    can_approve_final = order == 7
    WorkflowStep.objects.update_or_create(
        order=order,
        defaults={
            'name': name, 
            'role_name': role,
            'can_reject': can_reject,
            'can_approve_final': can_approve_final
        }
    )
print("✅ Workflow Steps initialized (7-step process)")

# Create a hospital first
hospital, created = Hospital.objects.get_or_create(
    code="TH001",
    defaults={
        'name': "Test Hospital",
        'tier': "TIER1",
        'address': "123 Test Street, Test City"
    }
)
print(f"✅ Hospital: {hospital.name}")

# Create users for all roles
roles = [
    ('hospital1', 'Hospital', 'Admin', 'HOSPITAL', 'Hospital Administrator', hospital),
    ('jpo1', 'JPO', 'Officer', 'JPO', 'Junior Personnel Officer', None),
    
    # Updated usernames to match requirements
    ('po1', 'APO', 'Officer', 'PO', 'Assistant Personnel Officer', None),
    ('as1', 'Assistant', 'Secretary', 'AS', 'Assistant Secretary', None),
    ('gmm1', 'FA', 'CAO', 'GMM', 'Financial Advisor & CAO', None),
    ('cgm1', 'Chief', 'GM', 'CGM', 'Chief General Manager', None),
    ('js1', 'Joint', 'Secretary', 'JS', 'Joint Secretary', None),
    ('director1', 'Director', 'Officer', 'DIRECTOR', 'Director HRD', None),
    
    ('customeradmin1', 'Customer', 'Admin', 'CUSTOMER_ADMIN', 'TGNPDCL System Administrator', None),
]

for username, first_name, last_name, role, designation, hosp in roles:
    user, created = User.objects.get_or_create(
        username=username,
        defaults={
            'email': f'{username}@tgnpdcl.com',
            'first_name': first_name,
            'last_name': last_name,
        }
    )
    user.set_password('password123')
    user.save()
    
    profile, created = UserProfile.objects.get_or_create(
        user=user,
        defaults={
            'role': role,
            'designation': designation,
            'hospital': hosp
        }
    )
    
    # FORCE UPDATE to ensure existing broken roles are fixed
    if profile.role != role:
        print(f"⚠️ Updating role for {username}: {profile.role} -> {role}")
        profile.role = role
        profile.designation = designation
        profile.save()
        
    print(f"✅ {username} ({designation}) - Role: {profile.role}")

print("\n🎉 All test users created/updated!")
print("\nLogin credentials:")
print("Usernames: hospital1, jpo1, po1, as1, gmm1, cgm1, js1, director1, customeradmin1")
print("Password: password123")
print("\nVisit: http://localhost:8000")
