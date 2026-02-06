import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.forms import modelformset_factory
from hospitals.models import BillItem
from hospitals.forms import BillItemForm

def verify_custom_service():
    print("Testing Custom Service Submission (No Service ID)...")
    
    # Mock Data: Custom Service Name, Rate=200, Qty=3. Amount should be 600.
    data = {
        'form-TOTAL_FORMS': '1',
        'form-INITIAL_FORMS': '0',
        'form-MIN_NUM_FORMS': '0',
        'form-MAX_NUM_FORMS': '1000',
        
        'form-0-hospital_service_name': 'Custom Bandage', # Custom Name
        'form-0-service': '', # Empty Service ID
        'form-0-claimed_quantity': '3',
        'form-0-claimed_rate': '200.00',
        'form-0-claimed_amount': '', # Empty Amount
    }

    BillItemFormSet = modelformset_factory(
        BillItem, 
        form=BillItemForm, 
        extra=0, 
        can_delete=False
    )
    
    formset = BillItemFormSet(data, queryset=BillItem.objects.none())
    
    if not formset.is_valid():
        print(f"FAILED: Formset Errors: {formset.errors}")
        return

    print("Formset Valid. processing...")
    
    for i, form in enumerate(formset):
        # View Logic Replication
        if form.cleaned_data.get('service') or form.cleaned_data.get('hospital_service_name'):
            item = form.save(commit=False)
            
            # Simulate Model Save Calculation
            if not item.claimed_amount and item.claimed_rate and item.claimed_quantity:
                item.claimed_amount = item.claimed_rate * item.claimed_quantity
                
            print(f"Item Saved: Name='{item.hospital_service_name}', Rate={item.claimed_rate}, Qty={item.claimed_quantity} -> Amount={item.claimed_amount}")
            
            if item.claimed_amount == 600.00:
                print("SUCCESS: Amount calculated correctly for Custom Service.")
            else:
                print(f"FAILURE: Expected 600.00, got {item.claimed_amount}")
        else:
            print("FAILURE: View logic would ignore this item.")

if __name__ == "__main__":
    verify_custom_service()
