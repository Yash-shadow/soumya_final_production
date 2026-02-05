import os
import django
import sys

# Setup Django environment
sys.path.append('/home/vboxuser/.gemini/antigravity/scratch/soumya-production')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hospitals.models import Hospital, Bill, Scheme
from django.contrib.auth.models import User

def test_claim_id_generation():
    # 1. Create a dummy hospital
    user, _ = User.objects.get_or_create(username='test_hosp_user')
    hospital, created = Hospital.objects.get_or_create(
        code='TESTHOSP123',
        defaults={
            'name': 'Test Hospital',
            'user': user,
            'tier': 'TIER1',
            'address': 'Test Address'
        }
    )
    
    # Ensure no previous bills interfere (optional, or just observe)
    # Bill.objects.filter(hospital=hospital).delete()

    # 2. Create a Bill
    scheme, _ = Scheme.objects.get_or_create(code='TS01', defaults={'name': 'TestScheme'})
    
    bill = Bill(
        hospital=hospital,
        scheme=scheme,
        patient_name="Test Patient",
        gross_claimed_amount=1000,
        age=30,
        sex='Male',
        designation='Officer',
        employee_id='EMP001',
        employee_type='EMPLOYEE',
        relationship='SELF',
        credit_card_number='1234567890',
        ip_number='IP123',
        mobile_number='9876543210',
        disease_details='Fever',
        admission_date='2023-01-01',
        discharge_date='2023-01-05',
    )
    
    # 3. Save triggers ID generation
    bill.save()
    
    print(f"Hospital Code: {hospital.code}")
    print(f"Generated Claim ID: {bill.claim_id}")
    
    # Expectation: Currently it takes first 3 chars: TES + 001 -> TES001 ?
    # User wants: TESTHOSP123001
    
    # Create another one to check increment
    bill2 = Bill(
        hospital=hospital,
        scheme=scheme,
        patient_name="Test Patient 2",
        gross_claimed_amount=1500,
        age=35,
        sex='Female',
        designation='Staff',
        employee_id='EMP002',
        employee_type='EMPLOYEE',
        relationship='DEPENDENT',
        credit_card_number='0987654321',
        ip_number='IP456',
        mobile_number='9123456780',
        disease_details='Flu',
        admission_date='2023-02-01',
        discharge_date='2023-02-05',
    )
    bill2.save()
    print(f"Generated Claim ID 2: {bill2.claim_id}")

if __name__ == '__main__':
    try:
        test_claim_id_generation()
    except Exception as e:
        print(f"Error: {e}")
