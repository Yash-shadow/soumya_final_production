# """
# Oracle 11g compatibility patch for Django 3.2+
# Fixes ORA-02000 errors by using sequences instead of IDENTITY columns

# Oracle 11g doesn't fully support IDENTITY columns (introduced in 12c).
# This patch reverts to using sequences, which is compatible with all Oracle 11g versions.
# """
# from django.db.backends.oracle import base
# from django.db.backends.oracle.schema import DatabaseSchemaEditor
# from django.db import models

# # Patch the data_types dictionary to use NUMBER instead of IDENTITY columns
# # This makes Django use sequences (the old way) which works in all Oracle 11g versions
# original_data_types = base.DatabaseWrapper.data_types.copy()

# # Revert to sequence-based auto-increment (compatible with Oracle 11g)
# base.DatabaseWrapper.data_types = {
#     **original_data_types,
#     "AutoField": "NUMBER(11)",
#     "BigAutoField": "NUMBER(19)", 
#     "SmallAutoField": "NUMBER(5)",
# }
        
# # Monkey-patch the schema editor to create sequences and triggers for AutoFields
# _original_create_model = DatabaseSchemaEditor.create_model

# def patched_create_model(self, model):
#     """Create model with sequences for Oracle 11g compatibility"""
#     # Call original create_model
#     _original_create_model(self, model)
    
#     # For each AutoField, create a sequence (Django will handle auto-increment via sequences)
#     # Note: We're NOT creating triggers to avoid SQL syntax issues - Django ORM handles sequences
#     for field in model._meta.local_fields:
#         if isinstance(field, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
#             # Use the same sequence naming convention as Django
#             sequence_name = self.connection.ops._get_no_autofield_sequence_name(model._meta.db_table)
#             sequence_name_quoted = self.quote_name(sequence_name)
            
#             # Create sequence only - Django ORM will use it automatically
#             try:
#                 self.execute(f"""
#                     CREATE SEQUENCE {sequence_name_quoted}
#                     START WITH 1
#                     INCREMENT BY 1
#                     NOCACHE
#                 """)
#             except Exception as e:
#                 # Sequence might already exist, that's okay
#                 error_str = str(e)
#                 if 'ORA-00955' not in error_str:  # Name is already used
#                     # Log but don't fail
#                     pass

# DatabaseSchemaEditor.create_model = patched_create_model

# # Patch _is_identity_column to always return False (Oracle 11g doesn't have identity_column in user_tab_cols)
# _original_is_identity_column = DatabaseSchemaEditor._is_identity_column

# def patched_is_identity_column(self, table_name, column_name):
#     """Always return False since we're using sequences, not IDENTITY columns"""
#     return False

# DatabaseSchemaEditor._is_identity_column = patched_is_identity_column

# # Also patch _drop_identity to do nothing (no IDENTITY columns to drop)
# _original_drop_identity = DatabaseSchemaEditor._drop_identity

# def patched_drop_identity(self, table_name, column_name):
#     """No-op since we don't use IDENTITY columns"""
#     pass

# DatabaseSchemaEditor._drop_identity = patched_drop_identity

# # Patch Oracle operations to use ROWNUM instead of FETCH FIRST for Oracle 11g
# from django.db.backends.oracle import operations

# # Patch limit_offset_sql to use ROWNUM (Oracle 11g compatible) instead of FETCH FIRST (Oracle 12c+)
# _original_limit_offset_sql = operations.DatabaseOperations.limit_offset_sql

# def patched_limit_offset_sql(self, low_mark, high_mark):
#     """Return empty string to force Django to use ROWNUM subquery wrapping (Oracle 11g compatible)"""
#     # Return empty string - Django's query compiler will wrap the query in a ROWNUM subquery
#     # This is the Oracle 11g compatible way (FETCH FIRST is Oracle 12c+)
#     return ""

# operations.DatabaseOperations.limit_offset_sql = patched_limit_offset_sql

# # Patch the query compiler to use ROWNUM subquery wrapping for Oracle 11g
# try:
#     from django.db.backends.oracle.compiler import SQLCompiler
    
#     _original_as_sql = SQLCompiler.as_sql
    
#     def patched_as_sql(self, with_limits=True, with_col_aliases=False):
#         """Wrap queries with ROWNUM subquery for Oracle 11g compatibility"""
#         # Get the base SQL
#         sql, params = _original_as_sql(self, with_limits=False, with_col_aliases=with_col_aliases)
        
#         # If we need limits and have them, wrap in ROWNUM subquery (Oracle 11g style)
#         if with_limits and (self.query.low_mark or self.query.high_mark):
#             low_mark = self.query.low_mark or 0
#             high_mark = self.query.high_mark
            
#             if high_mark is not None:
#                 # Wrap query in ROWNUM subquery
#                 sql = f"SELECT * FROM (SELECT a.*, ROWNUM rnum FROM ({sql}) a WHERE ROWNUM <= {high_mark}) WHERE rnum > {low_mark}"
        
#         return sql, params
    
#     SQLCompiler.as_sql = patched_as_sql
# except Exception as e:
#     # If patching fails, log but continue
#     print(f"⚠️  Warning: Could not patch SQLCompiler: {e}")
#     pass

# _original_execute = None

# def patch_oracle_execute():
#     """Patch Oracle cursor execute to catch and log SQL errors and fix Oracle 11g issues"""
#     try:
#         from django.db.backends.oracle.base import FormatStylePlaceholderCursor
#         original_execute = FormatStylePlaceholderCursor.execute
        
#         def patched_execute(self, query, params=None):
#             try:
#                 # Fix potential Oracle 11g issues before executing
#                 # Remove any trailing semicolons or slashes that might cause issues
#                 if query:
#                     query = query.rstrip(';').rstrip('/')
                
#                 return original_execute(self, query, params)
#             except Exception as e:
#                 error_str = str(e)
#                 if 'ORA-00933' in error_str:
#                     # Log the full problematic query for debugging
#                     print(f"\n⚠️  Oracle SQL Error (ORA-00933):")
#                     print(f"   Full Query:")
#                     print(f"   {query}")
#                     print(f"   Params: {params}")
#                     print(f"   Query length: {len(query)}")
#                     # Try to identify the issue
#                     if query.count('(') != query.count(')'):
#                         print(f"   ⚠️  Mismatched parentheses!")
#                     if query.count('"') % 2 != 0:
#                         print(f"   ⚠️  Odd number of quotes!")
#                 raise
        
#         FormatStylePlaceholderCursor.execute = patched_execute
#     except Exception as e:
#         # If patching fails, continue without it
#         print(f"⚠️  Warning: Could not patch Oracle execute: {e}")
#         pass

# # Apply the execute patch
# patch_oracle_execute()

# # Patch OracleParam to fix isinstance() compatibility issue with oracledb
# try:
#     from django.db.backends.oracle.base import OracleParam, Database
#     import datetime
#     from django.conf import settings
#     from django.utils.encoding import force_str, force_bytes
    
#     _original_oracle_param_init = OracleParam.__init__
    
#     def patched_oracle_param_init(self, param, cursor, strings_only=False):
#         """Fix isinstance() check for oracledb compatibility"""
#         # Handle timezone-aware datetimes
#         if settings.USE_TZ and (
#             isinstance(param, datetime.datetime)
#             and not isinstance(param, getattr(Database, 'Oracle_datetime', type(None)))
#         ):
#             try:
#                 from django.db.backends.oracle.base import Oracle_datetime
#                 param = Oracle_datetime.from_datetime(param)
#             except:
#                 pass
        
#         string_size = 0
#         # Oracle doesn't recognize True and False correctly
#         if param is True:
#             param = 1
#         elif param is False:
#             param = 0
        
#         if hasattr(param, "bind_parameter"):
#             self.force_bytes = param.bind_parameter(cursor)
#         else:
#             # Fix isinstance() check - Database.Binary might not be a type in oracledb
#             is_binary = False
#             is_timedelta = isinstance(param, datetime.timedelta)
            
#             # Check for Binary type safely
#             if hasattr(Database, 'Binary'):
#                 try:
#                     is_binary = isinstance(param, Database.Binary)
#                 except TypeError:
#                     # Database.Binary is not a type, check if param is bytes-like
#                     is_binary = isinstance(param, (bytes, bytearray))
#             else:
#                 # No Database.Binary, check if param is bytes-like
#                 is_binary = isinstance(param, (bytes, bytearray))
            
#             if is_binary or is_timedelta:
#                 self.force_bytes = param
#             else:
#                 # To transmit to the database, we need Unicode if supported
#                 self.force_bytes = force_str(param, cursor.charset, strings_only)
#                 if isinstance(self.force_bytes, str):
#                     string_size = len(force_bytes(param, cursor.charset, strings_only))
        
#         if hasattr(param, "input_size"):
#             self.input_size = param.input_size
#         elif string_size > 4000:
#             self.input_size = Database.CLOB
#         elif isinstance(param, datetime.datetime):
#             self.input_size = Database.TIMESTAMP
#         else:
#             self.input_size = None
    
#     OracleParam.__init__ = patched_oracle_param_init
#     print("✅ OracleParam patched for oracledb compatibility")
# except Exception as e:
#     print(f"⚠️  Warning: Could not patch OracleParam: {e}")
#     import traceback
#     traceback.print_exc()

# print("✅ Oracle 11g compatibility patch applied (using sequences instead of IDENTITY columns)")
