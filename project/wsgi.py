"""
WSGI config for TGNPDCL Monolithic Application.
"""
import os
import sys
import oracledb
import datetime
from django.core.wsgi import get_wsgi_application

# ============================================================================
# COMPREHENSIVE ORACLE 11g COMPATIBILITY PATCHES FOR DJANGO 3.2
# ============================================================================

print("=" * 80)
print("Starting Oracle 11g compatibility patches...")
print("=" * 80)

# 1. ORACLE DRIVER SHIM - Make Django think we're using cx_Oracle
oracledb.version = "8.3.0"
sys.modules["cx_Oracle"] = oracledb
print("✓ cx_Oracle shim applied")

# 2. FIX MISSING ATTRIBUTES IN python-oracledb
# python-oracledb doesn't have these attributes that cx_Oracle had
if not hasattr(oracledb, 'Binary'):
    class BinaryDummy:
        pass
    oracledb.Binary = BinaryDummy

if not hasattr(oracledb, 'BINARY'):
    oracledb.BINARY = None

if not hasattr(oracledb, 'ROWID'):
    oracledb.ROWID = None

# CRITICAL: Add Timestamp type for isinstance checks
if not hasattr(oracledb, 'Timestamp'):
    # Use datetime.datetime as a substitute
    oracledb.Timestamp = datetime.datetime

if not hasattr(oracledb, 'Date'):
    oracledb.Date = datetime.date

if not hasattr(oracledb, 'Time'):
    oracledb.Time = datetime.time

print("✓ Missing oracledb attributes added")

# 3. INITIALIZE THICK MODE (REQUIRED for Oracle 11g)
# 3. INITIALIZE THICK MODE (REQUIRED for Oracle 11g)
try:
    lib_dir = "/opt/oracle/instantclient_11_2"
    if os.path.exists(lib_dir):
        oracledb.init_oracle_client(lib_dir=lib_dir)
        print(f"✓ Oracle Thick Mode enabled using {lib_dir}")
    else:
        # Only raise error if we are expecting to use Oracle
        if os.environ.get('ORACLE_USER'):
            print(f"❌ CRITICAL: {lib_dir} not found!")
            raise Exception(f"Oracle Instant Client not found at {lib_dir}")
        else:
            print(f"⚠️  Oracle client not found at {lib_dir}, but ORACLE_USER not set. assuming SQLite fallback.")
except Exception as e:
    print(f"❌ Oracle Client Init Error: {e}")
    if os.environ.get('ORACLE_USER'):
        raise

# 4. PATCH DJANGO ORACLE BACKEND
from django.db.backends.oracle import base, operations, schema

# ============================================================================
# PATCH 1: Fix 'operators' and 'pattern_ops' property descriptors
# ============================================================================
class PatchedOperatorsDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        if 'operators' not in instance.__dict__:
            instance.__dict__['operators'] = {
                'exact': '= %s',
                'iexact': '= UPPER(%s)',
                'contains': "LIKE TRANSLATE(%s USING NCHAR_CS) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
                'icontains': "LIKE UPPER(TRANSLATE(%s USING NCHAR_CS)) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
                'gt': '> %s',
                'gte': '>= %s',
                'lt': '< %s',
                'lte': '<= %s',
                'startswith': "LIKE TRANSLATE(%s USING NCHAR_CS) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
                'endswith': "LIKE TRANSLATE(%s USING NCHAR_CS) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
                'istartswith': "LIKE UPPER(TRANSLATE(%s USING NCHAR_CS)) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
                'iendswith': "LIKE UPPER(TRANSLATE(%s USING NCHAR_CS)) ESCAPE TRANSLATE('\\' USING NCHAR_CS)",
            }
        return instance.__dict__['operators']

class PatchedPatternOpsDescriptor:
    def __get__(self, instance, owner):
        if instance is None:
            return self
        
        if 'pattern_ops' not in instance.__dict__:
            instance.__dict__['pattern_ops'] = {
                'contains': "LIKE %s ESCAPE '\\'",
                'icontains': "LIKE UPPER(%s) ESCAPE '\\'",
                'startswith': "LIKE %s ESCAPE '\\'",
                'istartswith': "LIKE UPPER(%s) ESCAPE '\\'",
                'endswith': "LIKE %s ESCAPE '\\'",
                'iendswith': "LIKE UPPER(%s) ESCAPE '\\'",
            }
        return instance.__dict__['pattern_ops']

base.DatabaseWrapper.operators = PatchedOperatorsDescriptor()
base.DatabaseWrapper.pattern_ops = PatchedPatternOpsDescriptor()
print("✓ Operators and pattern_ops patched")

# ============================================================================
# PATCH 2: Use sequences instead of IDENTITY columns (Oracle 11g compatible)
# ============================================================================
from django.db import models

original_data_types = base.DatabaseWrapper.data_types.copy()

base.DatabaseWrapper.data_types = {
    **original_data_types,
    "AutoField": "NUMBER(11)",
    "BigAutoField": "NUMBER(19)", 
    "SmallAutoField": "NUMBER(5)",
}
print("✓ Data types patched to use NUMBER instead of IDENTITY")

# ============================================================================
# PATCH 3: Fix OracleParam class to handle missing Database.Binary
# ============================================================================
original_oracle_param_init = base.OracleParam.__init__

def patched_oracle_param_init(self, param, cursor, strings_only=False):
    from django.utils.encoding import force_str, force_bytes
    from django.conf import settings
    
    # Handle timezone-aware datetimes
    if settings.USE_TZ and isinstance(param, datetime.datetime):
        try:
            param = base.Oracle_datetime.from_datetime(param)
        except:
            pass
    
    # Handle booleans
    if param is True:
        param = 1
    elif param is False:
        param = 0
    
    # Handle objects with bind_parameter method
    if hasattr(param, "bind_parameter"):
        self.force_bytes = param.bind_parameter(cursor)
    else:
        # Safely check for Binary type
        is_binary = False
        if hasattr(base.Database, 'Binary'):
            try:
                is_binary = isinstance(param, base.Database.Binary)
            except TypeError:
                is_binary = isinstance(param, (bytes, bytearray))
        else:
            is_binary = isinstance(param, (bytes, bytearray))
        
        if is_binary or isinstance(param, datetime.timedelta):
            self.force_bytes = param
        else:
            self.force_bytes = force_str(param, cursor.charset, strings_only)
    
    # Set input_size
    if hasattr(param, "input_size"):
        self.input_size = param.input_size
    elif isinstance(self.force_bytes, str):
        string_size = len(force_bytes(param, cursor.charset, strings_only))
        if string_size > 4000:
            self.input_size = base.Database.CLOB
        else:
            self.input_size = None
    elif isinstance(param, datetime.datetime):
        self.input_size = base.Database.TIMESTAMP
    else:
        self.input_size = None

base.OracleParam.__init__ = patched_oracle_param_init
print("✓ OracleParam patched")

# ============================================================================
# PATCH 4: Fix DatabaseOperations convert methods for Timestamp/Date/Time
# ============================================================================
# Patch convert_datefield_value
original_convert_datefield = operations.DatabaseOperations.convert_datefield_value

def patched_convert_datefield_value(self, value, expression, connection):
    if value is not None:
        # Safe isinstance check
        try:
            if hasattr(base.Database, 'Timestamp') and isinstance(value, base.Database.Timestamp):
                value = value.date()
        except TypeError:
            # Database.Timestamp is not a valid type, check if it's datetime
            if isinstance(value, datetime.datetime):
                value = value.date()
    return value

operations.DatabaseOperations.convert_datefield_value = patched_convert_datefield_value

# Patch convert_datetimefield_value
original_convert_datetimefield = operations.DatabaseOperations.convert_datetimefield_value

def patched_convert_datetimefield_value(self, value, expression, connection):
    if value is not None:
        # Safe isinstance check
        try:
            if hasattr(base.Database, 'Timestamp') and isinstance(value, base.Database.Timestamp):
                pass  # Already a timestamp
        except TypeError:
            # Database.Timestamp is not a valid type
            pass
        
        # Handle timezone if needed
        if isinstance(value, datetime.datetime):
            from django.conf import settings
            if settings.USE_TZ and value.tzinfo is None:
                from django.utils import timezone
                value = timezone.make_aware(value)
    return value

operations.DatabaseOperations.convert_datetimefield_value = patched_convert_datetimefield_value

# Patch convert_timefield_value
original_convert_timefield = operations.DatabaseOperations.convert_timefield_value

def patched_convert_timefield_value(self, value, expression, connection):
    if value is not None:
        # Safe isinstance check
        try:
            if hasattr(base.Database, 'Timestamp') and isinstance(value, base.Database.Timestamp):
                value = value.time()
        except TypeError:
            # Database.Timestamp is not a valid type
            if isinstance(value, datetime.datetime):
                value = value.time()
    return value

operations.DatabaseOperations.convert_timefield_value = patched_convert_timefield_value

print("✓ DatabaseOperations converters patched")

# ============================================================================
# PATCH 5: Fix init_connection_state for Oracle 11g version
# ============================================================================
def patched_init_connection_state(self):
    try:
        # CRITICAL: Set oracle_version to 11 for Oracle 11g compatible SQL
        self.oracle_full_version = '11.2.0.4.0'
        self.oracle_version = 11
        
        with self.connection.cursor() as cursor:
            cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
            cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS.FF6'")
            
            if hasattr(self, 'timezone_name') and self.timezone_name:
                cursor.execute(f"ALTER SESSION SET TIME_ZONE = '{self.timezone_name}'")
        
        print("✓ Oracle 11g connection initialized")
    except Exception as e:
        print(f"❌ Error initializing connection: {e}")
        raise

base.DatabaseWrapper.init_connection_state = patched_init_connection_state

# ============================================================================
# PATCH 6: Fix limit_offset_sql to use ROWNUM (Oracle 11g compatible)
# ============================================================================
def patched_limit_offset_sql(self, low_mark, high_mark):
    """
    Return empty string to force Django to use ROWNUM subquery wrapping.
    FETCH FIRST is Oracle 12c+ only, Oracle 11g needs ROWNUM.
    """
    return ""

operations.DatabaseOperations.limit_offset_sql = patched_limit_offset_sql
print("✓ limit_offset_sql patched for ROWNUM")

# ============================================================================
# PATCH 7: Fix last_executed_query
# ============================================================================
def patched_last_executed_query(self, cursor, sql, params):
    try:
        from django.utils.encoding import force_str
        
        statement = getattr(cursor, 'statement', None)
        if statement is None:
            statement = sql
        
        if not statement or params is None:
            return statement or ''
        
        if hasattr(params, 'items'):
            params_list = list(params.values())
        else:
            params_list = params
        
        for i, param in enumerate(params_list):
            param_str = force_str(param, errors='replace')
            statement = statement.replace(f':arg{i}', param_str)
        
        return statement
    except Exception:
        return sql or ''

operations.DatabaseOperations.last_executed_query = patched_last_executed_query
print("✓ last_executed_query patched")

# ============================================================================
# PATCH 8: Fix get_new_connection for Oracle 11g
# ============================================================================
original_get_new_connection = base.DatabaseWrapper.get_new_connection

def patched_get_new_connection(self, conn_params):
    conn_params = conn_params.copy()
    
    if 'threaded' in conn_params:
        del conn_params['threaded']
    
    return original_get_new_connection(self, conn_params)

base.DatabaseWrapper.get_new_connection = patched_get_new_connection

# ============================================================================
# PATCH 9: Fix cursor execute to handle errors and clean queries
# ============================================================================
from django.db.backends.oracle.base import FormatStylePlaceholderCursor

original_cursor_execute = FormatStylePlaceholderCursor.execute

def patched_cursor_execute(self, query, params=None):
    try:
        # Clean query - remove trailing semicolons that might cause ORA-00933
        if query:
            query = query.rstrip(';').rstrip('/')
        
        return original_cursor_execute(self, query, params)
    except Exception as e:
        error_str = str(e)
        if 'ORA-00933' in error_str:
            print(f"\n❌ Oracle SQL Error (ORA-00933): SQL command not properly ended")
            print(f"Query: {query[:500]}...")
            print(f"Params: {params}")
        raise

FormatStylePlaceholderCursor.execute = patched_cursor_execute
print("✓ Cursor execute patched")

# ============================================================================
# PATCH 10: Ensure Database object has all required attributes
# ============================================================================
if not hasattr(base.Database, 'BLOB'):
    base.Database.BLOB = oracledb.DB_TYPE_BLOB if hasattr(oracledb, 'DB_TYPE_BLOB') else None

if not hasattr(base.Database, 'CLOB'):
    base.Database.CLOB = oracledb.DB_TYPE_CLOB if hasattr(oracledb, 'DB_TYPE_CLOB') else None

if not hasattr(base.Database, 'TIMESTAMP'):
    base.Database.TIMESTAMP = oracledb.DB_TYPE_TIMESTAMP if hasattr(oracledb, 'DB_TYPE_TIMESTAMP') else None

if not hasattr(base.Database, 'INTERVAL'):
    base.Database.INTERVAL = oracledb.DB_TYPE_INTERVAL_DS if hasattr(oracledb, 'DB_TYPE_INTERVAL_DS') else None

print("✓ Database type attributes ensured")

# ============================================================================
# PATCH 11: Schema Editor patches for Oracle 11g
# ============================================================================
original_create_model = schema.DatabaseSchemaEditor.create_model

def patched_create_model(self, model):
    """Create model with sequences for Oracle 11g compatibility"""
    original_create_model(self, model)
    
    # Create sequences for AutoFields
    for field in model._meta.local_fields:
        if isinstance(field, (models.AutoField, models.BigAutoField, models.SmallAutoField)):
            sequence_name = self.connection.ops._get_no_autofield_sequence_name(model._meta.db_table)
            sequence_name_quoted = self.quote_name(sequence_name)
            
            try:
                self.execute(f"""
                    CREATE SEQUENCE {sequence_name_quoted}
                    START WITH 1
                    INCREMENT BY 1
                    NOCACHE
                """)
            except Exception as e:
                if 'ORA-00955' not in str(e):  # Sequence already exists
                    pass

schema.DatabaseSchemaEditor.create_model = patched_create_model

# Patch _is_identity_column to return False (we use sequences, not IDENTITY)
def patched_is_identity_column(self, table_name, column_name):
    return False

schema.DatabaseSchemaEditor._is_identity_column = patched_is_identity_column

# Patch _drop_identity to do nothing
def patched_drop_identity(self, table_name, column_name):
    pass

schema.DatabaseSchemaEditor._drop_identity = patched_drop_identity

print("✓ Schema editor patched for sequences")

# ============================================================================
# START DJANGO APPLICATION
# ============================================================================
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

print("=" * 80)
print("Loading Django application...")
print("=" * 80)

application = get_wsgi_application()

print("=" * 80)
print("✅ Django WSGI application loaded successfully with Oracle 11g patches")
print("=" * 80)