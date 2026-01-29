import os
import django
import sys

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from hospitals.models import Bill, BillItem

def check_data():
    bill = Bill.objects.first()
    if not bill:
        print("No bills found.")
        return

    print(f"Checking Bill: {bill.id} - {bill.patient_name}")
    for item in bill.items.all():
        print(f"Item: {item.service.name if item.service else item.hospital_service_name}")
        print(f"  Claimed Qty: {item.claimed_quantity}")
        print(f"  Claimed Rate: {item.claimed_rate}")
        print(f"  Claimed Amt: {item.claimed_amount}")
        print(f"  Approved Qty: {item.approved_quantity}")
        print(f"  Approved Rate: {item.approved_rate}")
        print(f"  Support Doc: {item.supporting_document}")
        print("-" * 20)

if __name__ == "__main__":
    check_data()
