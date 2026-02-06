# #!/usr/bin/env python
# """
# Check if auth tables exist and are properly created
# """
# import os
# import sys
# import django

# # Initialize Oracle client before Django setup (for Linux)
# try:
#     import oracledb
#     import sys as sys_module
#     oracledb.version = "8.3.0"
#     sys_module.modules["cx_Oracle"] = oracledb
#     try:
#         # Try project-specific path first
#         oracledb.init_oracle_client(lib_dir="/MEDICALAPP/NEEPMEDBILL/soumya_final_production/instantclient_21_12")
#         print("✓ Oracle thick mode initialized successfully (Linux - project path)")
#     except Exception as e1:
#         try:
#             # Fallback to standard Linux path
#             oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_21_12")
#             print("✓ Oracle thick mode initialized successfully (Linux - standard path)")
#         except Exception as e2:
#             try:
#                 # Fallback to Windows path (development)
#                 oracledb.init_oracle_client(lib_dir=r"D:\HR_Ubuntu\MEDICALAPP\NEEPPRODAPP\HR_M\instantclient_21_12")
#                 print("✓ Oracle thick mode initialized successfully (Windows)")
#             except Exception as e3:
#                 print(f"⚠ Warning: Could not initialize Oracle thick mode: {e3}")
#                 print("   Oracle 11g requires thick mode - connection will fail")
#                 raise
# except ImportError:
#     print("⚠ Warning: oracledb not available, will try to continue...")

# sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
# django.setup()

# from django.db import connection

# def check_table_exists(table_name):
#     """Check if a table exists"""
#     try:
#         with connection.cursor() as cursor:
#             cursor.execute("""
#                 SELECT COUNT(*) 
#                 FROM user_tables 
#                 WHERE table_name = :table_name
#             """, {'table_name': table_name.upper()})
#             exists = cursor.fetchone()[0] > 0
#             return exists
#     except Exception as e:
#         print(f"❌ Error checking table {table_name}: {e}")
#         return False

# def check_auth_tables():
#     """Check all auth-related tables"""
#     tables = [
#         'AUTH_USER',
#         'AUTH_GROUP',
#         'AUTH_PERMISSION',
#         'AUTH_USER_GROUPS',
#         'AUTH_USER_USER_PERMISSIONS',
#         'AUTH_GROUP_PERMISSIONS',
#         'DJANGO_SESSION',
#         'DJANGO_MIGRATIONS',
#         'DJANGO_CONTENT_TYPE',
#     ]
    
#     print("🔍 Checking authentication tables...")
#     missing = []
    
#     for table in tables:
#         exists = check_table_exists(table)
#         status = "✅" if exists else "❌"
#         print(f"{status} {table}: {'Exists' if exists else 'MISSING'}")
#         if not exists:
#             missing.append(table)
    
#     if missing:
#         print(f"\n⚠️  Missing tables: {', '.join(missing)}")
#         print("💡 Run: python manage.py migrate")
#     else:
#         print("\n✅ All auth tables exist")

# if __name__ == '__main__':
#     check_auth_tables()
