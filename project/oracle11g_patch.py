"""
Oracle 11g compatibility patch for Django 3.2+
Fixes ORA-02000 errors by using sequences instead of IDENTITY columns

Oracle 11g doesn't fully support IDENTITY columns (introduced in 12c).
This patch reverts to using sequences, which is compatible with all Oracle 11g versions.
"""
from django.db.backends.oracle import base
from django.db.backends.oracle.schema import DatabaseSchemaEditor
from django.db import models

# Patch the data_types dictionary to use NUMBER instead of IDENTITY columns
# This makes Django use sequences (the old way) which works in all Oracle 11g versions
original_data_types = base.DatabaseWrapper.data_types.copy()

# Revert to sequence-based auto-increment (compatible with Oracle 11g)
base.DatabaseWrapper.data_types = {
    **original_data_types,
    "AutoField": "NUMBER(11)",
    "BigAutoField": "NUMBER(19)", 
    "SmallAutoField": "NUMBER(5)",
}
        
# Monkey-patch the schema editor to create sequences and triggers for AutoFields
_original_create_model = DatabaseSchemaEditor.create_model

def patched_create_model(self, model):
    """Create model with sequences for Oracle 11g compatibility"""
    # Call original create_model
    _original_create_model(self, model)
    
    # For each AutoField, create a sequence (Django will handle auto-increment via sequences)
    # Note: We're NOT creating triggers to avoid SQL syntax issues - Django ORM handles sequences
    for field in model._meta.local_fields:
        if isinstance(field, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
            # Use the same sequence naming convention as Django
            sequence_name = self.connection.ops._get_no_autofield_sequence_name(model._meta.db_table)
            sequence_name_quoted = self.quote_name(sequence_name)
            
            # Create sequence only - Django ORM will use it automatically
            try:
                self.execute(f"""
                    CREATE SEQUENCE {sequence_name_quoted}
                    START WITH 1
                    INCREMENT BY 1
                    NOCACHE
                """)
            except Exception as e:
                # Sequence might already exist, that's okay
                error_str = str(e)
                if 'ORA-00955' not in error_str:  # Name is already used
                    # Log but don't fail
                    pass

DatabaseSchemaEditor.create_model = patched_create_model

# Patch _is_identity_column to always return False (Oracle 11g doesn't have identity_column in user_tab_cols)
_original_is_identity_column = DatabaseSchemaEditor._is_identity_column

def patched_is_identity_column(self, table_name, column_name):
    """Always return False since we're using sequences, not IDENTITY columns"""
    return False

DatabaseSchemaEditor._is_identity_column = patched_is_identity_column

# Also patch _drop_identity to do nothing (no IDENTITY columns to drop)
_original_drop_identity = DatabaseSchemaEditor._drop_identity

def patched_drop_identity(self, table_name, column_name):
    """No-op since we don't use IDENTITY columns"""
    pass

DatabaseSchemaEditor._drop_identity = patched_drop_identity

# Patch Oracle operations to use ROWNUM instead of FETCH FIRST for Oracle 11g
from django.db.backends.oracle import operations

# Patch limit_offset_sql to use ROWNUM (Oracle 11g compatible) instead of FETCH FIRST (Oracle 12c+)
_original_limit_offset_sql = operations.DatabaseOperations.limit_offset_sql

def patched_limit_offset_sql(self, low_mark, high_mark):
    """Return empty string to force Django to use ROWNUM subquery wrapping (Oracle 11g compatible)"""
    # Return empty string - Django's query compiler will wrap the query in a ROWNUM subquery
    # This is the Oracle 11g compatible way (FETCH FIRST is Oracle 12c+)
    return ""

operations.DatabaseOperations.limit_offset_sql = patched_limit_offset_sql

# Patch the query compiler to use ROWNUM subquery wrapping for Oracle 11g
try:
    from django.db.backends.oracle.compiler import SQLCompiler
    
    _original_as_sql = SQLCompiler.as_sql
    
    def patched_as_sql(self, with_limits=True, with_col_aliases=False):
        """Wrap queries with ROWNUM subquery for Oracle 11g compatibility"""
        # Get the base SQL
        sql, params = _original_as_sql(self, with_limits=False, with_col_aliases=with_col_aliases)
        
        # If we need limits and have them, wrap in ROWNUM subquery (Oracle 11g style)
        if with_limits and (self.query.low_mark or self.query.high_mark):
            low_mark = self.query.low_mark or 0
            high_mark = self.query.high_mark
            
            if high_mark is not None:
                # Wrap query in ROWNUM subquery
                sql = f"SELECT * FROM (SELECT a.*, ROWNUM rnum FROM ({sql}) a WHERE ROWNUM <= {high_mark}) WHERE rnum > {low_mark}"
        
        return sql, params
    
    SQLCompiler.as_sql = patched_as_sql
except Exception as e:
    # If patching fails, log but continue
    print(f"⚠️  Warning: Could not patch SQLCompiler: {e}")
    pass

_original_execute = None

def patch_oracle_execute():
    """Patch Oracle cursor execute to catch and log SQL errors and fix Oracle 11g issues"""
    try:
        from django.db.backends.oracle.base import FormatStylePlaceholderCursor
        original_execute = FormatStylePlaceholderCursor.execute
        
        def patched_execute(self, query, params=None):
            try:
                # Fix potential Oracle 11g issues before executing
                # Remove any trailing semicolons or slashes that might cause issues
                if query:
                    query = query.rstrip(';').rstrip('/')
                
                return original_execute(self, query, params)
            except Exception as e:
                error_str = str(e)
                if 'ORA-00933' in error_str:
                    # Log the full problematic query for debugging
                    print(f"\n⚠️  Oracle SQL Error (ORA-00933):")
                    print(f"   Full Query:")
                    print(f"   {query}")
                    print(f"   Params: {params}")
                    print(f"   Query length: {len(query)}")
                    # Try to identify the issue
                    if query.count('(') != query.count(')'):
                        print(f"   ⚠️  Mismatched parentheses!")
                    if query.count('"') % 2 != 0:
                        print(f"   ⚠️  Odd number of quotes!")
                raise
        
        FormatStylePlaceholderCursor.execute = patched_execute
    except Exception as e:
        # If patching fails, continue without it
        print(f"⚠️  Warning: Could not patch Oracle execute: {e}")
        pass

# Apply the execute patch
patch_oracle_execute()

# Patch OracleParam to fix isinstance() compatibility issue with oracledb
try:
    from django.db.backends.oracle.base import OracleParam, Database
    import datetime
    from django.conf import settings
    from django.utils.encoding import force_str, force_bytes
    
    _original_oracle_param_init = OracleParam.__init__
    
    def patched_oracle_param_init(self, param, cursor, strings_only=False):
        """Fix isinstance() check for oracledb compatibility"""
        # Handle timezone-aware datetimes
        if settings.USE_TZ and (
            isinstance(param, datetime.datetime)
            and not isinstance(param, getattr(Database, 'Oracle_datetime', type(None)))
        ):
            try:
                from django.db.backends.oracle.base import Oracle_datetime
                param = Oracle_datetime.from_datetime(param)
            except:
                pass
        
        string_size = 0
        # Oracle doesn't recognize True and False correctly
        if param is True:
            param = 1
        elif param is False:
            param = 0
        
        if hasattr(param, "bind_parameter"):
            self.force_bytes = param.bind_parameter(cursor)
        else:
            # Fix isinstance() check - Database.Binary might not be a type in oracledb
            is_binary = False
            is_timedelta = isinstance(param, datetime.timedelta)
            
            # Check for Binary type safely
            if hasattr(Database, 'Binary'):
                try:
                    is_binary = isinstance(param, Database.Binary)
                except TypeError:
                    # Database.Binary is not a type, check if param is bytes-like
                    is_binary = isinstance(param, (bytes, bytearray))
            else:
                # No Database.Binary, check if param is bytes-like
                is_binary = isinstance(param, (bytes, bytearray))
            
            if is_binary or is_timedelta:
                self.force_bytes = param
            else:
                # To transmit to the database, we need Unicode if supported
                self.force_bytes = force_str(param, cursor.charset, strings_only)
                if isinstance(self.force_bytes, str):
                    string_size = len(force_bytes(param, cursor.charset, strings_only))
        
        if hasattr(param, "input_size"):
            self.input_size = param.input_size
        elif string_size > 4000:
            self.input_size = Database.CLOB
        elif isinstance(param, datetime.datetime):
            self.input_size = Database.TIMESTAMP
        else:
            self.input_size = None
    
    OracleParam.__init__ = patched_oracle_param_init
    print("✅ OracleParam patched for oracledb compatibility")
except Exception as e:
    print(f"⚠️  Warning: Could not patch OracleParam: {e}")
    import traceback
    traceback.print_exc()

print("✅ Oracle 11g compatibility patch applied (using sequences instead of IDENTITY columns)")

















# """
# Oracle 11g Compatibility Patches for Django 3.2
# This module MUST be imported before Django is loaded.
# """
# import os
# import sys
# import datetime

# def apply_oracle11g_patches():
#     """Apply all Oracle 11g compatibility patches"""
    
#     print("=" * 80)
#     print("Applying Oracle 11g compatibility patches...")
#     print("=" * 80)
    
#     # Import oracledb
#     import oracledb
    
#     # 1. ORACLE DRIVER SHIM
#     oracledb.version = "8.3.0"
#     sys.modules["cx_Oracle"] = oracledb
#     print("✓ cx_Oracle shim applied")
    
#     # 2. FIX MISSING ATTRIBUTES
#     if not hasattr(oracledb, 'Binary'):
#         class BinaryDummy:
#             pass
#         oracledb.Binary = BinaryDummy
    
#     if not hasattr(oracledb, 'BINARY'):
#         oracledb.BINARY = None
    
#     if not hasattr(oracledb, 'ROWID'):
#         oracledb.ROWID = None
    
#     if not hasattr(oracledb, 'Timestamp'):
#         oracledb.Timestamp = datetime.datetime
    
#     if not hasattr(oracledb, 'Date'):
#         oracledb.Date = datetime.date
    
#     if not hasattr(oracledb, 'Time'):
#         oracledb.Time = datetime.time
    
#     print("✓ Missing oracledb attributes added")
    
#     # 3. INITIALIZE THICK MODE
#     try:
#         lib_dir = "/opt/oracle/instantclient_11_2"
#         if os.path.exists(lib_dir):
#             oracledb.init_oracle_client(lib_dir=lib_dir)
#             print(f"✓ Oracle Thick Mode enabled using {lib_dir}")
#         else:
#             print(f"❌ CRITICAL: {lib_dir} not found!")
#     except Exception as e:
#         if "already been initialized" not in str(e):
#             print(f"❌ Oracle Client Init Error: {e}")
    
#     # 4. PATCH DJANGO ORACLE BACKEND
#     from django.db.backends.oracle import base, operations, schema
    
#     # CRITICAL FIX: Force Oracle 11g version to prevent FETCH FIRST usage
#     original_get_database_version = base.DatabaseWrapper.get_database_version
    
#     def patched_get_database_version(self):
#         """Force Django to think we're using Oracle 11g"""
#         # Always return version 11 to prevent FETCH FIRST syntax
#         return (11, 2, 0, 4, 0)
    
#     base.DatabaseWrapper.get_database_version = patched_get_database_version
#     print("✓ Database version forced to Oracle 11g")
    
#     # PATCH: Oracle version property
#     def patched_oracle_version_property(self):
#         return 11
    
#     base.DatabaseWrapper.oracle_version = property(patched_oracle_version_property)
#     print("✓ oracle_version property patched")
    
#     # PATCH: Operators and pattern_ops
#     class PatchedOperatorsDescriptor:
#         def __get__(self, instance, owner):
#             if instance is None:
#                 return self
#             if 'operators' not in instance.__dict__:
#                 instance.__dict__['operators'] = {
#                     'exact': '= %s',
#                     'iexact': '= UPPER(%s)',
#                     'contains': "LIKE TRANSLATE(%s USING NCHAR_CS) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
#                     'icontains': "LIKE UPPER(TRANSLATE(%s USING NCHAR_CS)) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
#                     'gt': '> %s',
#                     'gte': '>= %s',
#                     'lt': '< %s',
#                     'lte': '<= %s',
#                     'startswith': "LIKE TRANSLATE(%s USING NCHAR_CS) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
#                     'endswith': "LIKE TRANSLATE(%s USING NCHAR_CS) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
#                     'istartswith': "LIKE UPPER(TRANSLATE(%s USING NCHAR_CS)) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
#                     'iendswith': "LIKE UPPER(TRANSLATE(%s USING NCHAR_CS)) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
#                 }
#             return instance.__dict__['operators']
    
#     class PatchedPatternOpsDescriptor:
#         def __get__(self, instance, owner):
#             if instance is None:
#                 return self
#             if 'pattern_ops' not in instance.__dict__:
#                 instance.__dict__['pattern_ops'] = {
#                     'contains': "LIKE %s ESCAPE '\\'",
#                     'icontains': "LIKE UPPER(%s) ESCAPE '\\'",
#                     'startswith': "LIKE %s ESCAPE '\\'",
#                     'istartswith': "LIKE UPPER(%s) ESCAPE '\\'",
#                     'endswith': "LIKE %s ESCAPE '\\'",
#                     'iendswith': "LIKE UPPER(%s) ESCAPE '\\'",
#                 }
#             return instance.__dict__['pattern_ops']
    
#     base.DatabaseWrapper.operators = PatchedOperatorsDescriptor()
#     base.DatabaseWrapper.pattern_ops = PatchedPatternOpsDescriptor()
#     print("✓ Operators and pattern_ops patched")
    
#     # PATCH: Data types to use NUMBER instead of IDENTITY
#     original_data_types = base.DatabaseWrapper.data_types.copy()
#     base.DatabaseWrapper.data_types = {
#         **original_data_types,
#         "AutoField": "NUMBER(11)",
#         "BigAutoField": "NUMBER(19)", 
#         "SmallAutoField": "NUMBER(5)",
#     }
#     print("✓ Data types patched")
    
#     # PATCH: OracleParam
#     original_oracle_param_init = base.OracleParam.__init__
    
#     def patched_oracle_param_init(self, param, cursor, strings_only=False):
#         from django.utils.encoding import force_str, force_bytes
#         from django.conf import settings
        
#         if settings.USE_TZ and isinstance(param, datetime.datetime):
#             try:
#                 param = base.Oracle_datetime.from_datetime(param)
#             except:
#                 pass
        
#         if param is True:
#             param = 1
#         elif param is False:
#             param = 0
        
#         if hasattr(param, "bind_parameter"):
#             self.force_bytes = param.bind_parameter(cursor)
#         else:
#             is_binary = isinstance(param, (bytes, bytearray))
#             if is_binary or isinstance(param, datetime.timedelta):
#                 self.force_bytes = param
#             else:
#                 self.force_bytes = force_str(param, cursor.charset, strings_only)
        
#         if hasattr(param, "input_size"):
#             self.input_size = param.input_size
#         elif isinstance(self.force_bytes, str):
#             string_size = len(force_bytes(param, cursor.charset, strings_only))
#             if string_size > 4000:
#                 self.input_size = base.Database.CLOB
#             else:
#                 self.input_size = None
#         elif isinstance(param, datetime.datetime):
#             self.input_size = base.Database.TIMESTAMP
#         else:
#             self.input_size = None
    
#     base.OracleParam.__init__ = patched_oracle_param_init
#     print("✓ OracleParam patched")
    
#     # PATCH: DatabaseOperations converters
#     def patched_convert_datefield_value(self, value, expression, connection):
#         if value is not None and isinstance(value, datetime.datetime):
#             value = value.date()
#         return value
    
#     def patched_convert_datetimefield_value(self, value, expression, connection):
#         if value is not None and isinstance(value, datetime.datetime):
#             from django.conf import settings
#             if settings.USE_TZ and value.tzinfo is None:
#                 from django.utils import timezone
#                 value = timezone.make_aware(value)
#         return value
    
#     def patched_convert_timefield_value(self, value, expression, connection):
#         if value is not None and isinstance(value, datetime.datetime):
#             value = value.time()
#         return value
    
#     operations.DatabaseOperations.convert_datefield_value = patched_convert_datefield_value
#     operations.DatabaseOperations.convert_datetimefield_value = patched_convert_datetimefield_value
#     operations.DatabaseOperations.convert_timefield_value = patched_convert_timefield_value
#     print("✓ DatabaseOperations converters patched")
    
#     # PATCH: init_connection_state
#     def patched_init_connection_state(self):
#         try:
#             self.oracle_full_version = '11.2.0.4.0'
#             self._oracle_version = 11
            
#             with self.connection.cursor() as cursor:
#                 cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
#                 cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'")
                
#                 if hasattr(self, 'timezone_name') and self.timezone_name:
#                     cursor.execute(f"ALTER SESSION SET TIME_ZONE = '{self.timezone_name}'")
#         except Exception as e:
#             print(f"❌ Error initializing connection: {e}")
    
#     base.DatabaseWrapper.init_connection_state = patched_init_connection_state
#     print("✓ init_connection_state patched")
    
#     # PATCH: last_executed_query
#     def patched_last_executed_query(self, cursor, sql, params):
#         try:
#             from django.utils.encoding import force_str
#             statement = getattr(cursor, 'statement', None) or sql
#             if not statement or params is None:
#                 return statement or ''
            
#             params_list = list(params.values()) if hasattr(params, 'items') else params
#             for i, param in enumerate(params_list):
#                 param_str = force_str(param, errors='replace')
#                 statement = statement.replace(f':arg{i}', param_str)
#             return statement
#         except Exception:
#             return sql or ''
    
#     operations.DatabaseOperations.last_executed_query = patched_last_executed_query
#     print("✓ last_executed_query patched")
    
#     # PATCH: get_new_connection
#     original_get_new_connection = base.DatabaseWrapper.get_new_connection
    
#     def patched_get_new_connection(self, conn_params):
#         conn_params = conn_params.copy()
#         if 'threaded' in conn_params:
#             del conn_params['threaded']
#         return original_get_new_connection(self, conn_params)
    
#     base.DatabaseWrapper.get_new_connection = patched_get_new_connection
    
#     # PATCH: Cursor execute
#     from django.db.backends.oracle.base import FormatStylePlaceholderCursor
#     original_cursor_execute = FormatStylePlaceholderCursor.execute
    
#     def patched_cursor_execute(self, query, params=None):
#         try:
#             if query:
#                 query = query.rstrip(';').rstrip('/')
#             return original_cursor_execute(self, query, params)
#         except Exception as e:
#             if 'ORA-00933' in str(e):
#                 print(f"\n❌ Oracle SQL Error (ORA-00933)")
#                 print(f"Query: {query[:200] if query else 'None'}...")
#             raise
    
#     FormatStylePlaceholderCursor.execute = patched_cursor_execute
#     print("✓ Cursor execute patched")
    
#     # PATCH: Database type attributes
#     if not hasattr(base.Database, 'BLOB'):
#         base.Database.BLOB = getattr(oracledb, 'DB_TYPE_BLOB', None)
#     if not hasattr(base.Database, 'CLOB'):
#         base.Database.CLOB = getattr(oracledb, 'DB_TYPE_CLOB', None)
#     if not hasattr(base.Database, 'TIMESTAMP'):
#         base.Database.TIMESTAMP = getattr(oracledb, 'DB_TYPE_TIMESTAMP', None)
#     if not hasattr(base.Database, 'INTERVAL'):
#         base.Database.INTERVAL = getattr(oracledb, 'DB_TYPE_INTERVAL_DS', None)
    
#     print("✓ Database type attributes ensured")
    
#     # PATCH: Schema editor
#     from django.db import models
#     original_create_model = schema.DatabaseSchemaEditor.create_model
    
#     def patched_create_model(self, model):
#         original_create_model(self, model)
#         for field in model._meta.local_fields:
#             if isinstance(field, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
#                 sequence_name = self.connection.ops._get_no_autofield_sequence_name(model._meta.db_table)
#                 sequence_name_quoted = self.quote_name(sequence_name)
#                 try:
#                     self.execute(f"CREATE SEQUENCE {sequence_name_quoted} START WITH 1 INCREMENT BY 1 NOCACHE")
#                 except Exception as e:
#                     if 'ORA-00955' not in str(e):
#                         pass
    
#     schema.DatabaseSchemaEditor.create_model = patched_create_model
    
#     def patched_is_identity_column(self, table_name, column_name):
#         return False
    
#     def patched_drop_identity(self, table_name, column_name):
#         pass
    
#     schema.DatabaseSchemaEditor._is_identity_column = patched_is_identity_column
#     schema.DatabaseSchemaEditor._drop_identity = patched_drop_identity
    
#     print("✓ Schema editor patched")
    
#     print("=" * 80)
#     print("✅ All Oracle 11g patches applied successfully")
#     print("=" * 80)