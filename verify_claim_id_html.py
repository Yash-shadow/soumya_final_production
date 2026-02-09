import os
import django
from django.conf import settings
from django.template.loader import render_to_string
from unittest.mock import MagicMock

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.template.loader import render_to_string
from django.contrib.auth.models import User
from workflow.models import SanctionRequest, WorkflowStep
from hospitals.models import Bill, Hospital

def verify_approval_queue():
    print("Verifying approval_queue.html...")
class MockUser:
    username = "testuser"
    def get_full_name(self): return "Test User"

class MockBill:
    claim_id = "TEST-CLAIM-001"
    employee_id = "EMP001"
    def __init__(self):
        self.items = MagicMock()
        self.items.all.return_value = []
        self.id_card_file = None
        self.cc_card_file = None
        self.discharge_summary_file = None
        self.admission_date = "2023-01-01"
        self.discharge_date = "2023-01-05"
        self.mobile_number = "1234567890"
        self.get_employee_type_display = "Employee"
        self.get_relationship_display = "Self"

class MockStep:
    name = "JPO"
    order = 1

class MockRequest:
    id = 123
    hospital_name = "Test Hospital"
    patient_name = "Test Patient"
    claimed_amount = 1000
    status = "PENDING"
    created_at = "2023-01-01"
    
    def __init__(self):
        self.bill = MockBill()
        self.current_step = MockStep()
        self.assigned_to = MockUser()
        
    def get_status_display(self):
        return "Pending"

def verify_approval_queue():
    print("Verifying approval_queue.html...")
    req = MockRequest()
    
    # Mock request context
    mock_request = MagicMock()
    mock_request.user = MockUser()

    context = {'pending_requests': [req], 'request': mock_request}
    rendered = render_to_string('workflow/approval_queue.html', context)
    
    if "<th>Claim ID</th>" in rendered:
        print("PASS: found '<th>Claim ID</th>'")
    else:
        print("FAIL: '<th>Claim ID</th>' not found")
        
    if "TEST-CLAIM-001" in rendered:
        print("PASS: found 'TEST-CLAIM-001'")
    else:
        print("FAIL: 'TEST-CLAIM-001' not found")
        
    if "SR-123" not in rendered:
         print("PASS: 'SR-123' NOT found (as expected)")
    else:
         print("FAIL: 'SR-123' found (should be removed/replaced)")

def verify_request_detail():
    print("\nVerifying request_detail.html...")
    req = MockRequest()
    
    # Mock request context
    mock_request = MagicMock()
    mock_request.user = MockUser()
    
    context = {'sanction_request': req, 'logs': [], 'total_claimed_amount': 1000, 'request': mock_request}
    rendered = render_to_string('workflow/request_detail.html', context)
    
    if "Review Request: TEST-CLAIM-001" in rendered:
        print("PASS: found 'Review Request: TEST-CLAIM-001'")
    else:
        print("FAIL: 'Review Request: TEST-CLAIM-001' not found in header")
        
    if "Review Request TEST-CLAIM-001 - NPDCL" in rendered:
        print("PASS: found 'Review Request TEST-CLAIM-001 - NPDCL' in title")
    else:
         print("FAIL: Title update not found")

if __name__ == "__main__":
    verify_approval_queue()
    verify_request_detail()
