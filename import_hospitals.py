"""
Script to import hospitals from Excel file (CC HOSP MASTER.xlsx) into the database.
"""
import os
import sys
import django
from datetime import datetime

# Initialize Oracle client before Django setup (same as wsgi.py)
import oracledb
import sys as sys_module

# This creates a "fake" cx_Oracle module using oracledb
oracledb.version = "8.3.0"
sys_module.modules["cx_Oracle"] = oracledb

try:
    # Try project-specific path first (production)
    oracledb.init_oracle_client(lib_dir="/MEDICALAPP/NEEPMEDBILL/soumya_final_production/instantclient_21_12")
    print("✓ Oracle thick mode initialized successfully (Linux - project path)")
except Exception as e1:
    try:
        # Fallback to standard Linux path
        oracledb.init_oracle_client(lib_dir="/opt/oracle/instantclient_21_12")
        print("✓ Oracle thick mode initialized successfully (Linux - standard path)")
    except Exception as e2:
        try:
            # Fallback to Windows path (development)
            oracledb.init_oracle_client(lib_dir=r"D:\HR_Ubuntu\MEDICALAPP\NEEPPRODAPP\HR_M\instantclient_21_12")
            print("✓ Oracle thick mode initialized successfully (Windows)")
        except Exception as e3:
            print(f"⚠ Warning: Could not initialize Oracle thick mode: {e3}")
            print("   Oracle 11g requires thick mode - connection will fail")
            raise

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from hospitals.models import Hospital
from django.core.management import execute_from_command_line
from django.db import connection
import pandas as pd

def check_and_create_tables():
    """Check if database tables exist, if not run migrations."""
    try:
        # Check if table exists by querying Oracle system tables
        with connection.cursor() as cursor:
            # Check if HOSPITALS_HOSPITAL table exists
            cursor.execute("""
                SELECT COUNT(*) 
                FROM user_tables 
                WHERE table_name = 'HOSPITALS_HOSPITAL'
            """)
            table_exists = cursor.fetchone()[0] > 0
            
            if table_exists:
                print("✅ Database tables already exist.")
                return True
            else:
                print("⚠️  Database tables not found. Running migrations...")
                print("   This may take a few minutes...")
                # Run migrations
                from django.core.management import call_command
                call_command('migrate', verbosity=1, interactive=False)
                print("✅ Migrations completed successfully!")
                return True
    except Exception as e:
        error_msg = str(e)
        if 'ORA-00942' in error_msg or 'does not exist' in error_msg or 'no such table' in error_msg.lower():
            print("⚠️  Database tables not found. Running migrations...")
            print("   This may take a few minutes...")
            try:
                # Run migrations
                from django.core.management import call_command
                call_command('migrate', verbosity=1, interactive=False)
                print("✅ Migrations completed successfully!")
                return True
            except Exception as migrate_error:
                print(f"❌ Error running migrations: {migrate_error}")
                print("\nPlease run manually: python manage.py migrate")
                return False
        else:
            # If it's a different error, try running migrations anyway
            print(f"⚠️  Database check error: {error_msg}")
            print("   Attempting to run migrations...")
            try:
                from django.core.management import call_command
                call_command('migrate', verbosity=1, interactive=False)
                print("✅ Migrations completed successfully!")
                return True
            except Exception as migrate_error:
                print(f"❌ Error running migrations: {migrate_error}")
                print("\nPlease run manually: python manage.py migrate")
                return False


def import_hospitals_from_excel(excel_file='CC HOSP MASTER.xlsx'):
    """
    Import hospitals from Excel file.
    Expected columns in Excel:
    - Hospital Name / Name
    - Code / Hospital Code
    - Serial Number (optional)
    - PAN Number (optional)
    - GST Number (optional)
    - CIN Number (optional)
    - Tier (TIER1, TIER2, TIER3)
    - Category (optional)
    - Address
    - City (optional)
    - District (optional)
    - State (optional)
    - Pincode (optional)
    - Phone / Contact Number (optional)
    - Email (optional)
    - Valid Upto (optional, date format)
    """
    
    file_path = os.path.join(os.path.dirname(__file__), excel_file)
    
    if not os.path.exists(file_path):
        print(f"❌ Error: File '{excel_file}' not found!")
        print(f"   Looking for file at: {file_path}")
        return
    
    # Check and create tables if needed
    # Note: If migrations fail due to Oracle 11g compatibility, run them manually first:
    # python manage.py migrate
    skip_check = '--skip-migration-check' in sys.argv or '--skip-check' in sys.argv
    
    if not skip_check:
        print("🔍 Checking database tables...")
        tables_ok = check_and_create_tables()
        
        if not tables_ok:
            print("\n⚠️  Warning: Could not verify/create tables automatically.")
            print("   This might be due to Oracle 11g compatibility issues.")
            print("   Please run migrations manually first:")
            print("   python manage.py migrate")
            print()
            print("   Or run this script with --skip-migration-check flag to continue anyway.")
            return
    else:
        print("⏭️  Skipping migration check...")
    
    print(f"\n📖 Reading Excel file: {excel_file}")
    
    try:
        # Read Excel file
        df = pd.read_excel(file_path)
        
        print(f"✅ Found {len(df)} rows in Excel file")
        print(f"\n📋 Columns found: {list(df.columns)}")
        print("\n" + "="*80)
        
        # Display first few rows for verification
        print("\nFirst 3 rows preview:")
        print(df.head(3).to_string())
        print("\n" + "="*80 + "\n")
        
        # Column mapping - adjust these based on your actual Excel column names
        # Common variations to check
        column_mapping = {
            'name': ['Hospital Name', 'Name', 'Hospital', 'HOSPITAL NAME', 'HOSPITAL_NAME'],
            'code': ['Code', 'Hospital Code', 'HOSPITAL CODE', 'HOSPITAL_CODE', 'Code'],
            'serial_number': ['Serial Number', 'SERIAL NUMBER', 'SERIAL_NUMBER', 'Serial No', 'S.No', 'SL.NO'],
            'pan_number': ['PAN Number', 'PAN', 'PAN NUMBER', 'PAN_NUMBER', 'Hospital PAN No'],
            'gst_number': ['GST Number', 'GST', 'GST NUMBER', 'GST_NUMBER', 'GSTIN', 'GST NO'],
            'cin_number': ['CIN Number', 'CIN', 'CIN NUMBER', 'CIN_NUMBER', 'CIN NO'],
            'tier': ['Tier', 'TIER', 'TIER_TYPE', 'Tier Type'],
            'category': ['Category', 'CATEGORY', 'Hospital Category'],
            'address': ['Address', 'ADDRESS', 'Hospital Address', 'Hospital Address1'],
            'address2': ['Hospital Address2', 'Address2', 'ADDRESS2'],
            'city': ['City', 'CITY'],
            'district': ['District', 'DISTRICT'],
            'state': ['State', 'STATE'],
            'pincode': ['Pincode', 'PINCODE', 'Pin Code', 'PIN CODE', 'PIN', 'Pin code'],
            'phone': ['Phone', 'PHONE', 'Contact Number', 'CONTACT', 'Mobile', 'MOBILE', 'Hospital Contact No'],
            'email': ['Email', 'EMAIL', 'Email ID', 'EMAIL_ID'],
            'valid_upto': ['Valid Upto', 'VALID UPTO', 'VALID_UPTO', 'Valid Until', 'Expiry Date']
        }
        
        # Find actual column names (case-insensitive)
        actual_columns = {}
        for key, possible_names in column_mapping.items():
            for col in df.columns:
                if str(col).strip().upper() in [n.upper() for n in possible_names]:
                    actual_columns[key] = col
                    break
        
        print("🔍 Column mapping:")
        for key, col in actual_columns.items():
            print(f"   {key}: '{col}'")
        print()
        
        # Required fields check
        required_fields = ['name', 'code', 'address']
        missing_fields = [f for f in required_fields if f not in actual_columns]
        
        if missing_fields:
            print(f"❌ Error: Missing required columns: {missing_fields}")
            print("   Please ensure your Excel file has columns for:")
            print("   - Hospital Name")
            print("   - Hospital Code")
            print("   - Address (or Hospital Address1)")
            return
        
        # Check if tier is missing - we'll default to TIER1
        if 'tier' not in actual_columns:
            print("⚠️  Warning: No 'Tier' column found. Defaulting all hospitals to TIER1")
            print("   You can manually update tiers later in the admin panel.")
        
        # Import hospitals
        imported_count = 0
        updated_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Get values with fallbacks
                name = str(row[actual_columns['name']]).strip()
                code = str(row[actual_columns['code']]).strip()
                
                # Get tier - default to TIER1 if not found
                if 'tier' in actual_columns:
                    tier = str(row[actual_columns['tier']]).strip().upper()
                    if tier not in ['TIER1', 'TIER2', 'TIER3']:
                        tier = 'TIER1'  # Default if invalid
                else:
                    tier = 'TIER1'  # Default if column doesn't exist
                
                # Combine address fields
                address1 = str(row[actual_columns['address']]).strip() if actual_columns.get('address') else ''
                address2 = ''
                if actual_columns.get('address2'):
                    addr2_val = row[actual_columns['address2']]
                    if pd.notna(addr2_val):
                        address2 = str(addr2_val).strip()
                
                # Combine addresses
                if address2 and address2 != 'nan':
                    address = f"{address1}, {address2}".strip()
                else:
                    address = address1
                
                # Skip if essential fields are empty
                if not name or name == 'nan' or not code or code == 'nan' or not address or address == 'nan':
                    print(f"⚠️ Row {index + 2}: Skipping - missing essential data (Name: {name}, Code: {code})")
                    error_count += 1
                    continue
                
                # Get optional fields with proper NaN handling
                def get_field_value(field_key):
                    if actual_columns.get(field_key):
                        val = row[actual_columns[field_key]]
                        if pd.notna(val):
                            return str(val).strip()
                    return None
                
                def clean_value(val):
                    if val and str(val).strip() and str(val).strip().lower() not in ['nan', 'none', '']:
                        return str(val).strip()
                    return None
                
                serial_number = clean_value(get_field_value('serial_number'))
                pan_number = clean_value(get_field_value('pan_number'))
                gst_number = clean_value(get_field_value('gst_number'))
                cin_number = clean_value(get_field_value('cin_number'))
                category = clean_value(get_field_value('category'))
                city = clean_value(get_field_value('city'))
                district = clean_value(get_field_value('district'))
                state = clean_value(get_field_value('state'))
                pincode = clean_value(get_field_value('pincode'))
                
                # Phone number - truncate to 15 characters (database limit)
                phone = clean_value(get_field_value('phone'))
                if phone and len(phone) > 15:
                    print(f"⚠️ Row {index + 2}: Phone number '{phone}' truncated to 15 chars")
                    phone = phone[:15]
                
                email = clean_value(get_field_value('email'))
                
                # Handle valid_upto date
                valid_upto = None
                if actual_columns.get('valid_upto'):
                    try:
                        valid_upto_val = row[actual_columns['valid_upto']]
                        if pd.notna(valid_upto_val):
                            if isinstance(valid_upto_val, str):
                                valid_upto = datetime.strptime(valid_upto_val, '%Y-%m-%d').date()
                            else:
                                valid_upto = valid_upto_val.date() if hasattr(valid_upto_val, 'date') else None
                    except:
                        pass
                
                # Create or update hospital
                hospital, created = Hospital.objects.update_or_create(
                    code=code,
                    defaults={
                        'name': name,
                        'tier': tier,
                        'address': address,
                        'serial_number': serial_number,
                        'pan_number': pan_number,
                        'gst_number': gst_number,
                        'cin_number': cin_number,
                        'category': category,
                        'city': city,
                        'district': district,
                        'state': state,
                        'pincode': pincode,
                        'phone': phone,
                        'email': email,
                        'valid_upto': valid_upto,
                        'is_active': True
                    }
                )
                
                if created:
                    imported_count += 1
                    print(f"✅ [{index + 2}] Created: {name} ({code}) - {tier}")
                else:
                    updated_count += 1
                    print(f"🔄 [{index + 2}] Updated: {name} ({code}) - {tier}")
                    
            except Exception as e:
                error_count += 1
                print(f"❌ [{index + 2}] Error importing row: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print("\n" + "="*80)
        print("📊 Import Summary:")
        print(f"   ✅ Created: {imported_count}")
        print(f"   🔄 Updated: {updated_count}")
        print(f"   ❌ Errors: {error_count}")
        print(f"   📝 Total Processed: {imported_count + updated_count + error_count}")
        print("="*80)
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    print("🏥 Hospital Import Script")
    print("="*80)
    print("\n📝 Note: If this is your first run, make sure to run migrations first:")
    print("   python manage.py migrate")
    print("="*80)
    print()
    
    # Check if file argument provided
    excel_file = sys.argv[1] if len(sys.argv) > 1 else 'CC HOSP MASTER.xlsx'
    
    # Check if --skip-migration-check flag is provided
    skip_check = '--skip-migration-check' in sys.argv or '--skip-check' in sys.argv
    
    if skip_check:
        print("⏭️  Skipping migration check (--skip-migration-check flag set)")
        print()
    
    import_hospitals_from_excel(excel_file)
