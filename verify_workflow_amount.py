import os
import django
import sys
from decimal import Decimal

# Setup Django
sys.path.append('/home/vboxuser/.gemini/antigravity/scratch/soumya-production')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.contrib.auth.models import User
from hospitals.models import Bill, Hospital, Scheme
from workflow.models import SanctionRequest, WorkflowStep, ApprovalLog

def verify_workflow_fix():
    print("--- Starting Verification of Workflow Amount Logic ---")
    
    # 1. Setup Data
    # Ensure we have steps
    steps = WorkflowStep.objects.all().order_by('order')
    if not steps.exists():
        print("Error: No workflow steps found. Please seed data.")
        return

    # Create dummy users for steps if they don't exist
    users = []
    for i, step in enumerate(steps):
        user, _ = User.objects.get_or_create(username=f'approver_{step.order}', defaults={'email': f'approver{step.order}@test.com'})
        users.append(user)
    
    # Create Hospital/Bill/Request
    hospital, _ = Hospital.objects.get_or_create(code="TEST001", defaults={'name': "Test Hospital", 'tier': 'TIER1'})
    scheme, _ = Scheme.objects.get_or_create(code="S001", defaults={'name': "Test Scheme"})
    
    # Check if Bill model has 'claimed_amount' field directly or just 'gross_claimed_amount'
    # Based on previous file reads, it has 'gross_claimed_amount'. 'BillItem' has 'claimed_amount'.
    # We'll use gross_claimed_amount for the Bill creation.
    
    bill = Bill.objects.create(
        hospital=hospital,
        scheme=scheme,
        patient_name="Test Patient",
        gross_claimed_amount=10000.00,
        status='SUBMITTED',
        
        # Mandatory fields based on models.py read earlier
        designation="Test Desig",
        employee_id="EMP001",
        employee_type="EMPLOYEE",
        relationship="SELF",
        credit_card_number="1234",
        ip_number="IP123",
        mobile_number="9999999999",
        age=30,
        sex="Male",
        disease_details="Test",
        admission_date="2023-01-01",
        discharge_date="2023-01-05"
    )
    
    # Create Sanction Request
    req = SanctionRequest.objects.create(
        bill=bill,
        hospital_name=hospital.name,
        patient_name="Test Patient",
        claimed_amount=10000.00,
        current_step=steps[0],
        status='PENDING'
    )
    
    print(f"Created Request {req.id} with Claimed Amount: {req.claimed_amount}")
    
    # 2. Simulate Workflow
    
    for i, step in enumerate(steps):
        print(f"\n--- Processing Step {step.order}: {step.name} ---")
        
        # LOGIC CHECK: This mimics the 'request_detail' view logic
        suggested_amount = req.claimed_amount
        latest_approval = ApprovalLog.objects.filter(
            request=req,
            approved_amount_at_stage__isnull=False
        ).order_by('-timestamp').first()
        
        if latest_approval:
            suggested_amount = latest_approval.approved_amount_at_stage
            print(f"   [Logic Check] Found previous approval from {latest_approval.step.name}: {suggested_amount}")
        else:
            print(f"   [Logic Check] No previous approval found. Defaulting to Claimed: {suggested_amount}")
        
        # Validation
        if i == 0:
            if suggested_amount != 10000.00:
                print(f"FAIL: Step 1 should see 10000.00, saw {suggested_amount}")
        else:
            # For subsequent steps, we expect to see the amount reduced by the previous step
            expected = Decimal("10000.00") - (Decimal("100") * i) # We will reduce by 100 each step
            if suggested_amount != expected:
                 print(f"FAIL: Step {step.order} should see {expected}, saw {suggested_amount}")
            else:
                 print(f"PASS: Step {step.order} correctly sees {suggested_amount} (inherited from previous)")

        # ACT: Approve with a reduced amount
        new_approved_amount = Decimal("10000.00") - (Decimal("100") * (i + 1))
        
        ApprovalLog.objects.create(
            request=req,
            step=step,
            user=users[i],
            action='FORWARD' if i < len(steps)-1 else 'APPROVE',
            comments=f"Approved at step {step.order}",
            approved_amount_at_stage=new_approved_amount
        )
        print(f"   [Action] Approver {step.role_name} approved for: {new_approved_amount}")
        
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    try:
        verify_workflow_fix()
    except Exception as e:
        print(f"Error: {e}")
