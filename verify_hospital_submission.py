
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage

from django.contrib.auth.models import User
from accounts.models import UserProfile
from hospitals.views import submit_bill
from hospitals.models import Hospital, Scheme, BillDocument, Bill, Service, BillItem

def verify_hospital_submission():
    print("Verifying hospital submission with attachment...")
    
    # 1. Setup Data
    user, created = User.objects.get_or_create(username='hospital_user')
    if created:
        user.set_password('password')
        user.save()
        
    hospital, _ = Hospital.objects.get_or_create(name='Test Hosp Sub', code='THSUB', tier='TIER1')
    
    # Ensure profile exists and is linked to hospital
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'HOSPITAL', 'hospital': hospital})
    if profile.hospital != hospital:
        profile.hospital = hospital
        profile.save()
        
    scheme, _ = Scheme.objects.get_or_create(name='Test Scheme', code='TS01')
    service, _ = Service.objects.get_or_create(name='Test Service', code='SERV01', base_rate_tier1=100)
    
    # 2. Mock Request
    factory = RequestFactory()
    
    file_content = b'hospital attachment content'
    uploaded_file = SimpleUploadedFile(
        "hospital_doc.txt",
        file_content,
        content_type="text/plain"
    )
    
    # Form data matching the template/view expectation
    data = {
        'patient_name': 'Test Patient',
        'employee_id': 'EMP999',
        'designation': 'Staff',
        'mobile_number': '1234567890',
        'age': '40',
        'sex': 'Male',
        'employee_type': 'EMPLOYEE',
        'relationship': 'SELF',
        'admission_date': '2026-02-01',
        'disease_details': 'Flu',
        'discharge_date': '2026-02-05',
        'ip_number': 'IP999',
        'credit_card_number': 'CC999',
        'bill_number': 'INV001',
        'bill_date': '2026-02-05',
        'scheme': scheme.id,
        'bill_attachment': uploaded_file,
        
        # Formset data (Management Form)
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        
        # Formset Item 0
        'form-0-service': service.id,
        'form-0-claimed_rate': '100',
        'form-0-claimed_quantity': '1',
        'form-0-claimed_amount': '100',
        'form-0-description': 'Test Remark',
    }
    
    request = factory.post('/hospitals/submit-bill/', data=data)
    request.user = user
    # request.user.profile is accessible
    
    # Add message support
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    # 3. Call View
    try:
        response = submit_bill(request)
        if response.status_code == 302:
            print("View returned redirect (success).")
        else:
            print(f"View returned {response.status_code}")
            # If form error, it might return 200 with errors in context
            if hasattr(response, 'context_data'):
                 if 'bill_form' in response.context_data and response.context_data['bill_form'].errors:
                     print(f"Bill Form Errors: {response.context_data['bill_form'].errors}")
                 if 'formset' in response.context_data and response.context_data['formset'].errors:
                     print(f"Formset Errors: {response.context_data['formset'].errors}")
    except Exception as e:
        print(f"View execution failed: {e}")
        import traceback
        traceback.print_exc()

    # 4. Verify
    # Find the bill created recently
    bill = Bill.objects.filter(hospital=hospital, patient_name='Test Patient').order_by('-created_at').first()
    if bill:
        print(f"SUCCESS: Bill created: {bill}")
        docs = BillDocument.objects.filter(bill=bill, document_type='OTHER')
        if docs.exists():
            doc = docs.first()
            print(f"SUCCESS: BillDocument created: {doc.file.name}")
            if doc.file.read() == file_content:
                 print("SUCCESS: File content matches.")
            else:
                 print("WARNING: File content read mismatch.")
        else:
            print("FAILURE: No BillDocument with type OTHER created.")
    else:
        print("FAILURE: Bill not created.")

if __name__ == '__main__':
    verify_hospital_submission()
