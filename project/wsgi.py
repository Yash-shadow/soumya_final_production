"""
WSGI config for TGNPDCL Monolithic Application.
"""
import os
from django.core.wsgi import get_wsgi_application


import oracledb
import sys

# This creates a "fake" cx_Oracle module using oracledb
oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb

try:
    oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_11_2")
except Exception as e:
    print(f"Warning: Could not initialize Oracle thick mode: {e}")


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
application = get_wsgi_application()





# import os
# import oracledb
# import sys

# # This creates a "fake" cx_Oracle module using oracledb
# oracledb.version = "8.3.0"
# sys.modules["cx_Oracle"] = oracledb

# # Initialize thick mode for Oracle 11g
# try:
#     oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_11_2")
#     print("✓ Oracle thick mode initialized successfully")
# except Exception as e:
#     print(f"Warning: Could not initialize Oracle thick mode: {e}")

# # Monkey-patch Django to bypass Oracle version check
# from django.db.backends.oracle import base
# original_init_connection_state = base.DatabaseWrapper.init_connection_state

# def patched_init_connection_state(self):
#     # Skip the version check
#     try:
#         # Call parent's init_connection_state, but skip check_database_version_supported
#         from django.db.backends.base.base import BaseDatabaseWrapper
#         BaseDatabaseWrapper.init_connection_state(self)
        
#         # Set Oracle-specific connection settings
#         cursor = self.connection.cursor()
        
#         # Set session formats
#         cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
#         cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'")
        
#         if self.timezone_name:
#             cursor.execute(f"ALTER SESSION SET TIME_ZONE = '{self.timezone_name}'")
        
#         cursor.close()
#     except Exception as e:
#         print(f"Warning during connection init: {e}")

# base.DatabaseWrapper.init_connection_state = patched_init_connection_state

# from django.core.wsgi import get_wsgi_application

# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
# application = get_wsgi_application()