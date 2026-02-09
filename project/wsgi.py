"""
WSGI config for TGNPDCL Monolithic Application.
"""
import os
from django.core.wsgi import get_wsgi_application

# Apply Oracle 11g patches BEFORE Django loads
try:
    from oracle11g_patch import apply_oracle11g_patches
    apply_oracle11g_patches()
except Exception as e:
    print(f"Warning: Could not apply Oracle 11g patches: {e}")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()

print("=" * 80)
print("✅ Django WSGI application loaded successfully")
print("=" * 80)