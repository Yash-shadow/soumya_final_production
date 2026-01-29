import os
import django
import sys
from django.db.models import Sum

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from workflow.models import SanctionRequest
from hospitals.models import Bill

def check_amounts():
    req = SanctionRequest.objects.first()
    if not req:
        print("No sanction request.")
        return

    print(f"Sanction Request: {req.id}")
    print(f"Request Claimed Amount: {req.claimed_amount}")
    
    bill = req.bill
    print(f"Bill ID: {bill.id}")
    print(f"Bill Gross Claimed Amount: {bill.gross_claimed_amount}")
    
    item_total = bill.items.aggregate(Sum('claimed_amount'))['claimed_amount__sum']
    print(f"Sum of Items Claimed Amount: {item_total}")

if __name__ == "__main__":
    check_amounts()
