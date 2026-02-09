"""
Django settings for TGNPDCL Monolithic Application.
"""
from pathlib import Path
import os
import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

# # Load .env file - try multiple locations
# env_path = BASE_DIR / '.env'
# env_path_str = str(env_path)

# # Try multiple paths
# env_paths = [
#     env_path_str,  # Project root
#     '/MEDICALAPP/NEEPMEDBILL/soumya_final_production/.env',  # Absolute Linux path
#     os.path.join(os.getcwd(), '.env'),  # Current directory
# ]

# env_loaded = False
# for path in env_paths:
#     if os.path.exists(path):
#         load_dotenv(dotenv_path=path, override=True)
#         if os.environ.get('ORACLE_USER'):
#             print(f"✅ Loaded .env file from: {path}")
#             env_loaded = True
#             break

# if not env_loaded:
#     # Try default load_dotenv (searches current dir and parents)
#     load_dotenv(override=True)
#     if os.environ.get('ORACLE_USER'):
#         print(f"✅ Loaded .env file (auto-detected)")
#         env_loaded = True
#     else:
#         print(f"⚠️  Warning: .env file not found!")
#         print(f"   Searched in:")
#         for path in env_paths:
#             print(f"     - {path}")
#         print(f"   Current directory: {os.getcwd()}")
#         print(f"   BASE_DIR: {BASE_DIR}")
#         print(f"   Please create .env file with Oracle credentials.")

# SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
# DEBUG = os.environ.get('DEBUG', 'True') == 'True'
# # Include host with and without port so Django accepts requests when run behind integrated app (Host: 10.48.49.26:8000)
# _default_hosts = 'localhost,127.0.0.1,hospital.localhost,10.48.49.26,10.48.49.26:8000'
# ALLOWED_HOSTS = [h.strip() for h in os.environ.get('ALLOWED_HOSTS', _default_hosts).split(',') if h.strip()]
# # Ensure host:port is allowed when host is in list (e.g. 10.48.49.26 -> also allow 10.48.49.26:8000)
# for h in list(ALLOWED_HOSTS):
#     if h and ':' not in h and h not in ('*', '.'):
#         for port in ('8000', '80', '443'):
#             candidate = f'{h}:{port}'
#             if candidate not in ALLOWED_HOSTS:
#                 ALLOWED_HOSTS.append(candidate)
# CSRF_TRUSTED_ORIGINS = [origin.strip().strip('"').strip("'") for origin in os.environ.get('CSRF_TRUSTED_ORIGINS','http://localhost:8000,http://127.0.0.1:8000,http://0.0.0.0:8000,http://10.48.49.26:8000,http://10.48.49.26').split(',')]

# # When run under integrated portal (Medical at /medical), set FORCE_SCRIPT_NAME=/medical
# # so Django generates correct URLs (e.g. /medical/admin/, /medical/static/).
# FORCE_SCRIPT_NAME = os.environ.get("FORCE_SCRIPT_NAME", "") or None



SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1,hospital.localhost').split(',')]
CSRF_TRUSTED_ORIGINS = [origin.strip().strip('"').strip("'") for origin in os.environ.get('CSRF_TRUSTED_ORIGINS','http://localhost:8000,http://127.0.0.1:8000,http://0.0.0.0:8000').split(',')]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Custom apps
    'accounts',
    'hospitals',
    'workflow',
    'documents',
    # Third party
    'storages',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'project.wsgi.application'

# Apply Oracle 11g compatibility patch before database configuration
try:
    from .oracle11g_patch import *
except ImportError:
    print("⚠️  Warning: Oracle 11g patch not found, migrations may fail on Oracle 11g")

# Database
ORACLE_USER = os.environ.get('ORACLE_USER')
ORACLE_PASSWORD = os.environ.get('ORACLE_PASSWORD')
ORACLE_HOST = os.environ.get('ORACLE_HOST')
ORACLE_PORT = os.environ.get('ORACLE_PORT', '1521')
ORACLE_SID = os.environ.get('ORACLE_SID')

# Debug: Print database configuration
print(f"🔍 Database Config Check:")
print(f"   ORACLE_USER: {'✓ Set' if ORACLE_USER else '✗ Not Set'}")
print(f"   ORACLE_PASSWORD: {'✓ Set' if ORACLE_PASSWORD else '✗ Not Set'}")
print(f"   ORACLE_HOST: {ORACLE_HOST if ORACLE_HOST else '✗ Not Set'}")
print(f"   ORACLE_SID: {ORACLE_SID if ORACLE_SID else '✗ Not Set'}")
print(f"   Using: {'Oracle' if (ORACLE_USER and ORACLE_PASSWORD and ORACLE_HOST and ORACLE_SID) else 'SQLite (fallback)'}")

if ORACLE_USER and ORACLE_PASSWORD and ORACLE_HOST and ORACLE_SID:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.oracle',
            'NAME': ORACLE_SID,
            'USER': ORACLE_USER,
            'PASSWORD': ORACLE_PASSWORD,
            'HOST': ORACLE_HOST,
            'PORT': ORACLE_PORT,
        }
    }


else:
    DATABASES = {
        'default': dj_database_url.config(
            default='sqlite:///' + str(BASE_DIR / 'db.sqlite3'),
            conn_max_age=600
        )
    }
# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# Static files (handled by STORAGES setting below)
STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# AWS S3 Configuration
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.environ.get('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = os.environ.get('AWS_S3_REGION_NAME', 'ap-south-1')
AWS_S3_FILE_OVERWRITE = False
AWS_DEFAULT_ACL = None
AWS_S3_SIGNATURE_VERSION = 's3v4'

if AWS_ACCESS_KEY_ID and AWS_STORAGE_BUCKET_NAME:
    # Use S3 for file storage
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {
                "access_key": AWS_ACCESS_KEY_ID,
                "secret_key": AWS_SECRET_ACCESS_KEY,
                "bucket_name": AWS_STORAGE_BUCKET_NAME,
                "region_name": AWS_S3_REGION_NAME,
            },
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }
else:
    # Local file storage fallback
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
        },
    }



# Logging configuration
import logging.config
import os

log_file_path = BASE_DIR / 'django_errors.log'
# Ensure log directory exists
log_file_path.parent.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': str(log_file_path),
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': 'ERROR',
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG' if DEBUG else 'ERROR',
            'propagate': False,
        },
    },
}


# Login settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Session Configuration
# Temporarily use file-based sessions to avoid Oracle 11g session query issues
# TODO: Fix database session queries and switch back to 'django.contrib.sessions.backends.db'
SESSION_ENGINE = 'django.contrib.sessions.backends.file'
SESSION_FILE_PATH = BASE_DIR / 'sessions'  # Directory for session files
SESSION_FILE_PATH.mkdir(exist_ok=True)  # Create directory if it doesn't exist

# SECURE_SSL_REDIRECT = os.environ.get('SECURE_SSL_REDIRECT')
# SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE')
# CSRF_COOKIE_SECURE = os.environ.get('CSRF_COOKIE_SECURE')
# SECURE_BROWSER_XSS_FILTER = os.environ.get('SECURE_BROWSER_XSS_FILTER')
# SECURE_CONTENT_TYPE_NOSNIFF = os.environ.get('SECURE_CONTENT_TYPE_NOSNIFF')