import os
import django
import sys
from django.core.files.base import ContentFile

sys.path.append(os.getcwd())
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from hospitals.models import Bill, BillDocument

def seed_docs():
    bills = Bill.objects.all()
    print(f"Found {bills.count()} bills.")
    
    count = 0
    for bill in bills:
        # Check if doc exists
        if not bill.documents.filter(document_type='FINAL_BILL').exists():
            print(f"Adding Final Bill to Claim {bill.claim_id}...")
            
            # Create a dummy file
            dummy_content = b"This is a test bill document content."
            
            doc = BillDocument(
                bill=bill,
                document_type='FINAL_BILL'
            )
            doc.file.save(f'final_bill_{bill.id}.txt', ContentFile(dummy_content))
            doc.save()
            count += 1
    
    print(f"✅ Added {count} test documents.")

if __name__ == "__main__":
    seed_docs()
