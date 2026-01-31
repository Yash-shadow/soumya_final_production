import os
import django
import sys

# Add project root to path
sys.path.append(os.getcwd())

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
try:
    from accounts.views import ROLE_CONFIG
except ImportError:
    ROLE_CONFIG = {}

User = get_user_model()
print(f"AUTH_USER_MODEL: {settings.AUTH_USER_MODEL}")

print("\n--- ROLE CONFIG ---")
for key, val in ROLE_CONFIG.items():
    print(f"{key}: Name='{val.get('name')}', Title='{val.get('title')}'")

print("\n--- EXISTING USERS ---")
for u in User.objects.all():
    role = "N/A"
    try:
        if hasattr(u, 'profile'):
            role = u.profile.role
    except Exception as e:
        role = f"Error: {e}"
    print(f"User: '{u.username}', Role: '{role}'")

print("\n--- VALIDATORS ---")
print(User._meta.get_field('username').validators)
