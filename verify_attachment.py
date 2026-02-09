
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.auth.models import User, AnonymousUser
from accounts.models import UserProfile
from workflow.views import process_request
from workflow.models import SanctionRequest, WorkflowStep, ApprovalLog
from hospitals.models import Bill, Hospital, Scheme, BillDocument

def verify_attachment():
    print("Verifying attachment upload...")
    
    # 1. Setup Data
    user, created = User.objects.get_or_create(username='test_approver')
    if created:
        user.set_password('password')
        user.save()
    
    profile, _ = UserProfile.objects.get_or_create(user=user, defaults={'role': 'PO'})
    if profile.role != 'PO':
        profile.role = 'PO'
        profile.save()
    hospital, _ = Hospital.objects.get_or_create(name='Test Hosp', code='TH01', tier='TIER1')
    scheme, _ = Scheme.objects.get_or_create(name='Test Scheme', code='TS01')
    
    bill = Bill.objects.create(
        hospital=hospital,
        scheme=scheme,
        patient_name='Test Patient',
        gross_claimed_amount=1000,
        status='UNDER_REVIEW',
        # Required fields
        age=30,
        sex='Male',
        admission_date='2026-01-01',
        discharge_date='2026-01-05',
        employee_id='EMP001',
        designation='Engineer',
        employee_type='EMPLOYEE',
        relationship='SELF',
        mobile_number='9876543210',
        disease_details='Fever',
        credit_card_number='CC123',
        ip_number='IP123'
    )
    
    step = WorkflowStep.objects.filter(order=1).first()
    if not step:
         step = WorkflowStep.objects.create(name='Test Step', role_name='PO', order=999)
    
    req = SanctionRequest.objects.create(
        bill=bill,
        current_step=step,
        claimed_amount=1000,
        status='IN_PROGRESS'
    )
    
    # 2. Mock Request
    factory = RequestFactory()
    
    # Create mock file
    file_content = b'test file content'
    uploaded_file = SimpleUploadedFile(
        "test_attachment.txt",
        file_content,
        content_type="text/plain"
    )
    
    data = {
        'action': 'FORWARD',
        'comments': 'Test comments',
        'approved_amount': '1000',
        'approval_attachment': uploaded_file
    }
    
    request = factory.post(f'/workflow/request/{req.id}/process/', data=data)
    request.user = user
    # request.user.profile is accessible via ORM now that we created it

    
    # Add message support
    setattr(request, 'session', 'session')
    messages = FallbackStorage(request)
    setattr(request, '_messages', messages)
    
    # 3. Call View
    # Note: process_request has @approver_required and @login_required decorators.
    # We might need to bypass them or ensure user meets criteria.
    # user.profile.role should match step.role_name for @approver_required to pass? 
    # Actually @approver_required checks if user has a profile.
    
    try:
        response = process_request(request, req.id)
        if response.status_code == 302:
            print("View returned redirect (success).")
        else:
            print(f"View returned {response.status_code}")
    except Exception as e:
        print(f"View execution failed: {e}")
        # If it fails due to decorators/permissions, we might need to mock them or adjust user
        import traceback
        traceback.print_exc()

    # 4. Verify
    docs = BillDocument.objects.filter(bill=bill, document_type='OTHER')
    if docs.exists():
        doc = docs.first()
        print(f"SUCCESS: BillDocument created: {doc.file.name}")
        if doc.file.read() == file_content:
             print("SUCCESS: File content matches.")
        else:
             print("WARNING: File content read mismatch (might be stored differently).")
    else:
        print("FAILURE: No BillDocument with type OTHER created.")

if __name__ == '__main__':
    verify_attachment()
