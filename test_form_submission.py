import os
import django
import sys
from decimal import Decimal

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.forms import modelformset_factory
from hospitals.models import BillItem, Service, Bill, Hospital
from hospitals.forms import BillItemForm
from workflow.models import SanctionRequest

def test_submission():
    # Setup Data
    service = Service.objects.first()
    if not service:
        print("No services found. Creating one.")
        service = Service.objects.create(name="Test Service", base_rate_tier1=100)
    
    print(f"Using Service: {service.name} (ID: {service.id})")

    # Mock POST Data for FormSet
    # Simulating 1 row: Qty=5, Rate=100, Amount=0 (expecting calc)
    data = {
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        
        'form-0-service': service.id,
        'form-0-claimed_quantity': '5',
        'form-0-claimed_rate': '100.00',
        'form-0-claimed_amount': '0.00', # Simulating user left it blank or JS set it to 0 but we want calc
        'form-0-description': 'Test Description',
    }

    BillItemFormSet = modelformset_factory(
        BillItem, 
        form=BillItemForm, 
        extra=0, 
        can_delete=False
    )
    
    formset = BillItemFormSet(data, queryset=BillItem.objects.none())
    
    print(f"Formset Valid? {formset.is_valid()}")
    if not formset.is_valid():
        print(f"Errors: {formset.errors}")
        return

    # Simulate View Logic
    total_amount = 0
    for i, form in enumerate(formset):
        print(f"Processing Form {i}")
        if form.cleaned_data.get('service'):
            item = form.save(commit=False)
            
            print(f"Pre-Save: Rate={item.claimed_rate}, Qty={item.claimed_quantity}, Amount={item.claimed_amount}")
            
            # This is the logic in views.py
            # item.save()
            # But item.save() needs a bill. We mock it or just call the logic directly.
            
            # Replicating save() logic manually to test:
            if not item.claimed_amount:
                item.claimed_amount = item.claimed_rate * item.claimed_quantity
            
            print(f"Post-Calc: Amount={item.claimed_amount}")
            total_amount += item.claimed_amount

    print(f"Total Amount: {total_amount}")

if __name__ == "__main__":
    test_submission()
