# Script to create test users for all 7 roles
import os
import django
import sys

# Initialize Oracle client before Django setup (for Linux)
try:
    import oracledb
    import sys as sys_module
    import os
    oracledb.version = "8.3.0"
    sys_module.modules["cx_Oracle"] = oracledb
    
    # Try multiple common Oracle Instant Client paths on Linux
    oracle_paths = [
        "/MEDICALAPP/NEEPMEDBILL/soumya_final_production/instantclient_21_12",  # Project-specific location
                os.environ.get("ORACLE_HOME", ""),
        os.environ.get("LD_LIBRARY_PATH", "").split(":")[0] if os.environ.get("LD_LIBRARY_PATH") else "",
    ]
    
    # Also try Windows path if running on Windows
    if os.name == 'nt':
        oracle_paths.insert(1, r"D:\HR_Ubuntu\MEDICALAPP\NEEPPRODAPP\HR_M\instantclient_21_12")
    
    oracle_initialized = False
    for lib_dir in oracle_paths:
        if not lib_dir or not os.path.exists(lib_dir):
            continue
        try:
            oracledb.init_oracle_client(lib_dir=lib_dir)
            print(f"✓ Oracle thick mode initialized successfully: {lib_dir}")
            oracle_initialized = True
            break
        except Exception as e:
            continue
    
    if not oracle_initialized:
        # Only raise error if we are expecting to use Oracle
        if os.environ.get('ORACLE_USER'):
            print("⚠ Warning: Could not initialize Oracle thick mode with any known path")
            print("   Searched paths:")
            for path in oracle_paths:
                if path:
                    exists = "✓" if os.path.exists(path) else "✗"
                    print(f"     {exists} {path}")
            print("   Oracle 11g requires thick mode - please install Oracle Instant Client")
            print("   or set ORACLE_HOME environment variable")
            raise Exception("Oracle thick mode initialization failed - Oracle 11g requires thick mode")
        else:
             print("⚠️  Oracle client not found, but ORACLE_USER not set. assuming SQLite fallback.")
        
except ImportError:
    print("⚠ Warning: oracledb not available, will try to continue...")
except Exception as e:
    print(f"❌ Error: {e}")
    if os.environ.get('ORACLE_USER'):
        raise

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
    try:
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
    except Exception as e:
        print(f"❌ Error creating user {username}: {e}")
        import traceback
        traceback.print_exc()
        continue

print("\n🎉 All test users created/updated!")
print("\nLogin credentials:")
print("Usernames: hospital1, jpo1, po1, as1, gmm1, cgm1, js1, director1, customeradmin1")
print("Password: password123")
print("\nVisit: http://localhost:8000")
