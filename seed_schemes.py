import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hospitals.models import Scheme

def seed_schemes():
    schemes = [
        {'name': 'Employees Health Scheme', 'code': 'EHS', 'description': 'Health scheme for working employees of TGNPDCL.'},
        {'name': 'Pensioners Health Scheme', 'code': 'PHS', 'description': 'Health scheme for retired employees (pensioners) and their dependents.'},
        {'name': 'General/Emergency Scheme', 'code': 'GEN', 'description': 'Non-EHS emergency cases and general reimbursement.'},
    ]

    for scheme_data in schemes:
        scheme, created = Scheme.objects.get_or_create(
            code=scheme_data['code'],
            defaults={
                'name': scheme_data['name'],
                'description': scheme_data['description']
            }
        )
        if created:
            print(f"Created scheme: {scheme.name}")
        else:
            # Update existing if needed
            if scheme.name != scheme_data['name']:
                scheme.name = scheme_data['name']
                scheme.description = scheme_data['description']
                scheme.save()
                print(f"Updated scheme: {scheme.name}")
            else:
                print(f"Scheme already exists: {scheme.name}")

if __name__ == '__main__':
    seed_schemes()
