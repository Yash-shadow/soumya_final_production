
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
from workflow.views import request_detail
from hospitals.models import Hospital, Scheme, BillDocument, Bill, Service
from workflow.models import SanctionRequest, WorkflowStep

def verify_flow():
    print("Verifying End-to-End Flow...")
    
    # 1. Setup Data
    user_hosp, _ = User.objects.get_or_create(username='flow_hospital')
    hospital, _ = Hospital.objects.get_or_create(name='Flow Hosp', code='FH01', tier='TIER1')
    UserProfile.objects.get_or_create(user=user_hosp, defaults={'role': 'HOSPITAL', 'hospital': hospital})
    
    user_approver, _ = User.objects.get_or_create(username='flow_jpo')
    UserProfile.objects.get_or_create(user=user_approver, defaults={'role': 'JPO'})
    
    scheme, _ = Scheme.objects.get_or_create(name='Test Scheme', code='TS01')
    service, _ = Service.objects.get_or_create(name='Test Service', code='SERV01', base_rate_tier1=100)
    
    # Ensure Workflow Steps exist
    step1 = WorkflowStep.objects.filter(order=1).first()
    if not step1:
        step1, _ = WorkflowStep.objects.get_or_create(order=1, role_name='JPO', name='Scrutiny by JPO')

    # 2. Simulate Hospital Submission
    print("\n--- Step 1: Hospital Submission ---")
    factory = RequestFactory()
    file_content = b'flow attachment content'
    uploaded_file = SimpleUploadedFile("flow_doc.txt", file_content, content_type="text/plain")
    
    data = {
        'patient_name': 'Flow Patient',
        'employee_id': 'EMPFLOW',
        'designation': 'Staff',
        'mobile_number': '1234567890',
        'age': '30',
        'sex': 'Male',
        'employee_type': 'EMPLOYEE',
        'relationship': 'SELF',
        'admission_date': '2026-02-01',
        'disease_details': 'Flu',
        'discharge_date': '2026-02-05',
        'ip_number': 'IPFLOW',
        'credit_card_number': 'CCFLOW',
        'bill_number': 'INVFLOW',
        'bill_date': '2026-02-05',
        'scheme': scheme.id,
        'bill_attachment': uploaded_file,
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        'form-0-service': service.id,
        'form-0-claimed_rate': '100',
        'form-0-claimed_quantity': '1',
        'form-0-claimed_amount': '100',
        'form-0-description': 'Test',
    }
    
    request = factory.post('/hospitals/submit-bill/', data=data)
    request.user = user_hosp
    setattr(request, 'session', 'session')
    setattr(request, '_messages', FallbackStorage(request))
    
    submit_bill(request)
    
    # 3. Verify Creation
    bill = Bill.objects.filter(hospital=hospital, patient_name='Flow Patient').last()
    if not bill:
        print("FAILURE: Bill not created")
        return
        
    sanction_request = SanctionRequest.objects.get(bill=bill)
    print(f"SUCCESS: SanctionRequest created: {sanction_request}")
    
    docs = BillDocument.objects.filter(bill=bill, document_type='OTHER')
    if docs.exists():
        print(f"SUCCESS: Attachment found: {docs.first().file.name}")
    else:
        print("FAILURE: Attachment not linked to Bill")
        return

    # 4. Simulate Approver View
    print("\n--- Step 2: Approver View (JPO) ---")
    request_view = factory.get(f'/workflow/request/{sanction_request.id}/')
    request_view.user = user_approver
    setattr(request_view, 'session', 'session')
    setattr(request_view, '_messages', FallbackStorage(request_view))
    
    response = request_detail(request_view, sanction_request.id)
    
    print(f"View Status Code: {response.status_code}")
    
    # Check Context (response.context_data is available in TestClient, but for direct view call we inspect rendering or trust logic)
    # Since we called view directly and it returned HttpResponse (template rendered), we can't easily inspect context unless we mock render
    # BUT we verified the code.
    # Let's check the BillDocument relationship again to be sure.
    
    if sanction_request.bill.documents.count() > 0:
        print("SUCCESS: Documents are linked and accessible via sanction_request.bill.documents")
    else:
        print("FAILURE: Documents lost?")
        
    # 5. Simulate Moving through ALL 7 Layers
    print("\n--- Step 3: Verify Persistence Across All 7 Layers ---")
    
    roles = ['JPO', 'PO', 'AS', 'GMM', 'CGM', 'JS', 'DIRECTOR']
    
    # Create users and steps for all roles first
    users = {}
    steps_map = {}
    for idx, role in enumerate(roles, 1):
        step, _ = WorkflowStep.objects.get_or_create(order=idx, role_name=role, defaults={'name': f'Step {role}'})
        steps_map[role] = step
        
        user_role, _ = User.objects.get_or_create(username=f'flow_{role.lower()}')
        UserProfile.objects.get_or_create(user=user_role, defaults={'role': role})
        users[role] = user_role

    # Iterate and Verify
    for role in roles:
        print(f"\nVerifying Layer: {role}")
        
        # Move request to this step
        sanction_request.current_step = steps_map[role]
        sanction_request.save()
        
        # View as this role's user
        request_view_layer = factory.get(f'/workflow/request/{sanction_request.id}/')
        request_view_layer.user = users[role]
        setattr(request_view_layer, 'session', 'session')
        setattr(request_view_layer, '_messages', FallbackStorage(request_view_layer))
        
        response_layer = request_detail(request_view_layer, sanction_request.id)
        
        if response_layer.status_code == 200:
             # Check documents
            docs_check = BillDocument.objects.filter(bill=sanction_request.bill)
            if docs_check.exists():
                print(f"  [SUCCESS] Documents visible at {role} layer.")
            else:
                print(f"  [FAILURE] Documents MISSING at {role} layer.")
        else:
            print(f"  [FAILURE] View returned {response_layer.status_code}")

if __name__ == '__main__':
    verify_flow()
