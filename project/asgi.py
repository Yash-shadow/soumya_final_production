# """
# ASGI config for TGNPDCL Monolithic Application.

# This file exposes the ASGI callable as a module-level variable named ``application``.

# For more information on this file, see
# https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
# """

# import os
# from django.core.asgi import get_asgi_application

# # Oracle client initialization (same as wsgi.py)
# import oracledb
# import sys

# # This creates a "fake" cx_Oracle module using oracledb
# oracledb.version = "8.3.0"
# sys.modules["cx_Oracle"] = oracledb

# try:
#     # Initialize Oracle client - same path as wsgi.py
#     oracledb.init_oracle_client(lib_dir="/MEDICALAPP/NEEPMEDBILL/soumya_final_production/instantclient_21_12")
#     print("✓ Oracle thick mode initialized successfully")
# except Exception as e:
#     print(f"Warning: Could not initialize Oracle thick mode: {e}")

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

# # Get ASGI application
# application = get_asgi_application()
